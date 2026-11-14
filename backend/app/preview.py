# -*- coding: utf-8 -*-
"""Template preview: render a form and highlight the parts that vary per case.

The admin screen shows a form exactly as it will print, with every value that
comes from the case data shaded yellow, so it is obvious which text is the
standing wording of the form and which is filled in for each employee.

How it works: the preview render installs a Jinja ``finalize`` hook that wraps
the result of each ``{{ ... }}`` expression in a pair of private-use marker
characters. The admin's own text blocks are exempted -- they are the standing
wording -- by tagging their values as ``Static``. After rendering, the runs of
the .docx that contain markers are split and given a yellow highlight.

Marking at ``finalize`` (rather than on the context values) matters: it happens
after the filters have run, so ``{{ chk.date|dt }}`` still parses a real date,
and it never touches the expressions inside ``{% if %}`` conditions.
"""
from __future__ import annotations

from pathlib import Path

import jinja2
from docx import Document
from docx.enum.text import WD_COLOR_INDEX
from docx.oxml.ns import qn

MARK_START = ""
MARK_END = ""


class Static(str):
    """Text that is part of the form itself, not a per-case value."""


def _finalize(value):
    """Escape for XML exactly as the normal render does, then mark the value."""
    from .render import xml_escape

    if value is None:
        return ""
    if isinstance(value, Static):
        return str(value)          # already escaped when the block was resolved
    text = xml_escape(value)
    if not isinstance(text, str):
        return text                # an image or other XML object; nothing to mark
    if not text.strip():
        return text
    return f"{MARK_START}{text}{MARK_END}"


def preview_env(base_env: jinja2.Environment) -> jinja2.Environment:
    """A copy of the render environment that marks per-case values."""
    env = jinja2.Environment(undefined=base_env.undefined)
    env.filters.update(base_env.filters)
    env.finalize = _finalize
    return env


def iter_paragraphs(container):
    """Every paragraph in the document, including those inside nested tables."""
    for paragraph in container.paragraphs:
        yield paragraph
    for table in container.tables:
        for row in table.rows:
            for cell in row.cells:
                yield from iter_paragraphs(cell)


def _segments(text: str, inside: bool):
    """Split run text into (chunk, highlighted) pairs, tracking marker state."""
    out, buffer = [], ""
    for char in text:
        if char == MARK_START:
            if buffer:
                out.append((buffer, inside))
                buffer = ""
            inside = True
        elif char == MARK_END:
            if buffer:
                out.append((buffer, inside))
                buffer = ""
            inside = False
        else:
            buffer += char
    if buffer:
        out.append((buffer, inside))
    return out, inside


def highlight_marked(docx_path: Path) -> Path:
    """Replace the markers with real yellow highlighting, in place."""
    docx_path = Path(docx_path)
    document = Document(str(docx_path))

    for paragraph in iter_paragraphs(document):
        if not any(MARK_START in r.text or MARK_END in r.text for r in paragraph.runs):
            continue

        inside = False
        for run in list(paragraph.runs):
            text = run.text
            if MARK_START not in text and MARK_END not in text:
                _set_highlight(run, inside)
                continue

            parts, inside = _segments(text, inside)
            if not parts:
                run._element.getparent().remove(run._element)
                continue

            # Reuse this run for the first chunk, then clone it for the rest so
            # every piece keeps the original font, size and weight. The highlight
            # is set on every chunk, not only the marked ones -- a clone is taken
            # from a run that may already carry the highlight.
            run.text = parts[0][0]
            _set_highlight(run, parts[0][1])
            anchor = run
            for chunk, marked in parts[1:]:
                clone = _clone_run_after(anchor, chunk)
                _set_highlight(clone, marked)
                anchor = clone

    document.save(str(docx_path))
    return docx_path


def _set_highlight(run, on: bool) -> None:
    run.font.highlight_color = WD_COLOR_INDEX.YELLOW if on else None


def _clone_run_after(run, text: str):
    """Copy a run's formatting into a new run placed just after it."""
    from copy import deepcopy

    from docx.text.run import Run

    element = deepcopy(run._element)
    for child in list(element):
        if child.tag != qn("w:rPr"):
            element.remove(child)
    run._element.addnext(element)
    clone = Run(element, run._parent)
    clone.text = text
    return clone
