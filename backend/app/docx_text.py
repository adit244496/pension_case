"""Reading and rewriting the words in a generated .docx, in place.

The forms are dense tables ruled to a printed original, so the usual way of
editing a document in a browser -- turn it into HTML, let the user work on that,
turn it back -- is out of the question: the round trip would not survive a single
merged cell. What a clerk actually needs to change is the *wording*: a name
spelt differently, a date, a sentence the office phrases its own way.

So this reads the document as an ordered list of editable pieces, each addressed
by where it sits, and writes changes back into the runs that are already there.
Nothing else in the file is touched -- fonts, borders, column widths, section
breaks and merges all stay exactly as generated -- because the only thing that
changes is the text inside a run.
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

# A cell with more text than this is shown as a box rather than a line.
LONG_TEXT = 60


def _alignment(paragraph: Paragraph) -> str:
    value = paragraph.alignment
    if value is None:
        return ""
    return {0: "left", 1: "center", 2: "right", 3: "justify"}.get(int(value), "")


def _describe(paragraph: Paragraph) -> dict:
    """The few visual hints the editor needs to look like the page."""
    runs = paragraph.runs
    first = runs[0] if runs else None
    size = None
    if first is not None and first.font.size is not None:
        size = round(first.font.size.pt)
    return {
        "bold": bool(first is not None and first.bold),
        "underline": bool(first is not None and first.underline),
        "align": _alignment(paragraph),
        "size": size,
    }


def _walk(parent, prefix: str, blocks: list, tables: dict) -> None:
    """Body children in document order: paragraphs, and tables cell by cell."""
    element = parent.element.body if hasattr(parent.element, "body") else parent._tc
    para_index = 0
    table_index = 0
    for child in element.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            paragraph = Paragraph(child, parent)
            text = paragraph.text
            if text.strip():
                blocks.append({
                    "id": f"{prefix}p{para_index}",
                    "kind": "para",
                    "text": text,
                    **_describe(paragraph),
                })
            para_index += 1
        elif tag == "tbl":
            table = Table(child, parent)
            key = f"{prefix}t{table_index}"
            # Keyed by id() *and* holding the element: lxml makes its proxy
            # objects on demand, and a collected one's id can be handed to the
            # next -- keeping a reference is what makes the identity reliable.
            seen: dict[int, object] = {}
            rows = 0
            cols = 0
            for row_index, row in enumerate(table.rows):
                rows = row_index + 1
                for col_index, cell in enumerate(row.cells):
                    cols = max(cols, col_index + 1)
                    # A merged cell is the same underlying element in every
                    # position it spans; edit it once, at its first position.
                    marker = cell._tc
                    if id(marker) in seen:
                        continue
                    seen[id(marker)] = marker
                    _cell_blocks(cell, f"{key}.r{row_index}.c{col_index}.",
                                 blocks, tables, key, row_index, col_index)
            tables[key] = {"rows": rows, "cols": cols}
            table_index += 1


def _cell_blocks(cell: _Cell, prefix: str, blocks: list, tables: dict,
                 table_key: str, row: int, col: int) -> None:
    for index, paragraph in enumerate(cell.paragraphs):
        text = paragraph.text
        blocks.append({
            "id": f"{prefix}p{index}",
            "kind": "cell",
            "text": text,
            "table": table_key,
            "row": row,
            "col": col,
            "part": index,
            "long": len(text) > LONG_TEXT,
            **_describe(paragraph),
        })
    for nested_index, nested in enumerate(cell.tables):
        # Nested tables are rare here, but addressing them keeps ids unique.
        key = f"{prefix}t{nested_index}"
        seen: dict[int, object] = {}
        rows = cols = 0
        for row_index, nrow in enumerate(nested.rows):
            rows = row_index + 1
            for col_index, ncell in enumerate(nrow.cells):
                cols = max(cols, col_index + 1)
                marker = ncell._tc
                if id(marker) in seen:
                    continue
                seen[id(marker)] = marker
                _cell_blocks(ncell, f"{key}.r{row_index}.c{col_index}.",
                             blocks, tables, key, row_index, col_index)
        tables[key] = {"rows": rows, "cols": cols}


def read_blocks(path: Path) -> dict:
    """Every editable piece of the document, in the order it is printed."""
    document = Document(str(path))
    blocks: list[dict] = []
    tables: dict[str, dict] = {}
    _walk(document, "", blocks, tables)
    return {"blocks": blocks, "tables": tables}


def _set_text(paragraph: Paragraph, new_text: str) -> bool:
    """Put `new_text` in the paragraph without disturbing its formatting.

    Only the part that actually differs is rewritten, and it is written into the
    run that already held it -- so a name in bold stays bold, and a sentence made
    of a plain run and an emphasised one keeps both.
    """
    runs = paragraph.runs
    old = "".join(run.text for run in runs)
    if old == new_text:
        return False
    if not runs:
        paragraph.add_run(new_text)
        return True

    # The edit is the stretch between the shared start and the shared end.
    prefix = 0
    shortest = min(len(old), len(new_text))
    while prefix < shortest and old[prefix] == new_text[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < len(old) - prefix and suffix < len(new_text) - prefix
           and old[len(old) - 1 - suffix] == new_text[len(new_text) - 1 - suffix]):
        suffix += 1
    start, end = prefix, len(old) - suffix
    middle = new_text[prefix:len(new_text) - suffix]

    position = 0
    written = False
    for run in runs:
        run_start, run_end = position, position + len(run.text)
        position = run_end
        touches = not (run_end < start or run_start > end)
        if not touches:
            continue
        head = run.text[:max(0, start - run_start)]
        tail = run.text[max(0, min(end, run_end) - run_start):]
        if not written:
            run.text = head + middle + tail
            written = True
        else:
            run.text = head + tail
    if not written:                                   # appended past the last run
        runs[-1].text = runs[-1].text + middle
    return True


def _find(document: Document, block_id: str):
    """The paragraph a block id points at, or None if the shape has changed."""
    parts = block_id.split(".")
    container = document
    element = document.element.body
    for part in parts:
        if part.startswith("p"):
            index = int(part[1:])
            paragraphs = [child for child in element.iterchildren()
                          if child.tag.endswith("}p")]
            if index >= len(paragraphs):
                return None
            return Paragraph(paragraphs[index], container)
        if part.startswith("t"):
            index = int(part[1:])
            tables = [child for child in element.iterchildren()
                      if child.tag.endswith("}tbl")]
            if index >= len(tables):
                return None
            table = Table(tables[index], container)
            container = table
        elif part.startswith("r"):
            row_index = int(part[1:])
            if row_index >= len(table.rows):
                return None
            row = table.rows[row_index]
        elif part.startswith("c"):
            col_index = int(part[1:])
            if col_index >= len(row.cells):
                return None
            cell = row.cells[col_index]
            container = cell
            element = cell._tc
    return None


def apply_edits(path: Path, edits: dict[str, str]) -> int:
    """Write the changed pieces back into the file. Returns how many changed."""
    document = Document(str(path))
    changed = 0
    missing = []
    for block_id, text in edits.items():
        paragraph = _find(document, block_id)
        if paragraph is None:
            missing.append(block_id)
            continue
        if _set_text(paragraph, text):
            changed += 1
    if missing:
        raise KeyError("The document no longer has: " + ", ".join(missing[:5]))
    if changed:
        document.save(str(path))
    return changed
