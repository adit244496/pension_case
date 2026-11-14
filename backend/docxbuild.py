# -*- coding: utf-8 -*-
"""A thin layer over python-docx for laying out the DCRG case forms.

The forms are dense government tables, so the helpers here are deliberately
low-level: exact column widths, per-cell borders, and runs that carry both a
Latin and a complex-script (Devanagari) font so Marathi renders correctly in
Word and survives the PDF conversion.
"""
from __future__ import annotations

import os

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_ALIGN_VERTICAL
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

# Fonts are named in the .docx, so they must exist wherever the PDF is made.
# On Windows with Word these are the defaults; on a Linux server install
# Liberation Serif (metric-compatible with Times New Roman) and a Devanagari
# face, then set these before running build_templates.py:
#
#   PENSION_FONT_LATIN="Liberation Serif"
#   PENSION_FONT_DEVANAGARI="Noto Sans Devanagari"
LATIN_FONT = os.environ.get("PENSION_FONT_LATIN", "Times New Roman")
DEVANAGARI_FONT = os.environ.get("PENSION_FONT_DEVANAGARI", "Nirmala UI")

ALIGN = {
    "left": WD_ALIGN_PARAGRAPH.LEFT,
    "center": WD_ALIGN_PARAGRAPH.CENTER,
    "right": WD_ALIGN_PARAGRAPH.RIGHT,
    "justify": WD_ALIGN_PARAGRAPH.JUSTIFY,
}

VALIGN = {
    "top": WD_ALIGN_VERTICAL.TOP,
    "center": WD_ALIGN_VERTICAL.CENTER,
    "bottom": WD_ALIGN_VERTICAL.BOTTOM,
}


# --------------------------------------------------------------------------
# low-level xml helpers
# --------------------------------------------------------------------------
def _set_run_fonts(run, latin: str = LATIN_FONT, complex_script: str = DEVANAGARI_FONT):
    """Set the ascii/hAnsi font and the complex-script font on one run."""
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:ascii"), latin)
    fonts.set(qn("w:hAnsi"), latin)
    fonts.set(qn("w:cs"), complex_script)


def _set_run_size(run, size_pt: float):
    run.font.size = Pt(size_pt)
    rpr = run._element.get_or_add_rPr()
    szcs = rpr.find(qn("w:szCs"))
    if szcs is None:
        szcs = OxmlElement("w:szCs")
        rpr.append(szcs)
    szcs.set(qn("w:val"), str(int(size_pt * 2)))


def _set_run_bold(run, bold: bool):
    run.bold = bold
    rpr = run._element.get_or_add_rPr()
    bcs = rpr.find(qn("w:bCs"))
    if bcs is None:
        bcs = OxmlElement("w:bCs")
        rpr.append(bcs)
    bcs.set(qn("w:val"), "1" if bold else "0")


def cell_borders(cell, top="single", bottom="single", left="single",
                 right="single", size=4, color="000000"):
    """Apply per-side borders; pass None for a side to leave it open."""
    tc_pr = cell._tc.get_or_add_tcPr()
    existing = tc_pr.find(qn("w:tcBorders"))
    if existing is not None:
        tc_pr.remove(existing)
    borders = OxmlElement("w:tcBorders")
    for name, style in (("top", top), ("left", left),
                        ("bottom", bottom), ("right", right)):
        element = OxmlElement(f"w:{name}")
        element.set(qn("w:val"), style or "nil")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), color)
        borders.append(element)
    tc_pr.append(borders)


def table_borders(table, size=4):
    tbl_pr = table._tbl.tblPr
    existing = tbl_pr.find(qn("w:tblBorders"))
    if existing is not None:
        tbl_pr.remove(existing)
    borders = OxmlElement("w:tblBorders")
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{name}")
        element.set(qn("w:val"), "single")
        element.set(qn("w:sz"), str(size))
        element.set(qn("w:space"), "0")
        element.set(qn("w:color"), "000000")
        borders.append(element)
    tbl_pr.append(borders)


def no_table_borders(table):
    tbl_pr = table._tbl.tblPr
    existing = tbl_pr.find(qn("w:tblBorders"))
    if existing is not None:
        tbl_pr.remove(existing)
    borders = OxmlElement("w:tblBorders")
    for name in ("top", "left", "bottom", "right", "insideH", "insideV"):
        element = OxmlElement(f"w:{name}")
        element.set(qn("w:val"), "nil")
        borders.append(element)
    tbl_pr.append(borders)


def cell_margins(table, top=0, bottom=0, left=0.10, right=0.10):
    """Table-wide cell padding in cm.

    Word's default side padding is ~0.19cm each way, which costs almost 0.4cm of
    usable width per column -- enough to wrap an extra line in these dense forms.
    """
    tbl_pr = table._tbl.tblPr
    existing = tbl_pr.find(qn("w:tblCellMar"))
    if existing is not None:
        tbl_pr.remove(existing)
    margins = OxmlElement("w:tblCellMar")
    for name, value in (("top", top), ("left", left),
                        ("bottom", bottom), ("right", right)):
        element = OxmlElement(f"w:{name}")
        element.set(qn("w:w"), str(int(value * 567)))
        element.set(qn("w:type"), "dxa")
        margins.append(element)
    tbl_pr.append(margins)


def shade_cell(cell, fill="D9D9D9"):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)


def set_cell_width(cell, cm: float):
    cell.width = Cm(cm)
    tc_pr = cell._tc.get_or_add_tcPr()
    existing = tc_pr.find(qn("w:tcW"))
    if existing is not None:
        tc_pr.remove(existing)
    tcw = OxmlElement("w:tcW")
    tcw.set(qn("w:w"), str(int(cm * 567)))
    tcw.set(qn("w:type"), "dxa")
    tc_pr.append(tcw)


def rotate_cell_text(cell, direction="btLr"):
    """Vertical text, used for the narrow header columns on landscape sheets."""
    tc_pr = cell._tc.get_or_add_tcPr()
    element = OxmlElement("w:textDirection")
    element.set(qn("w:val"), direction)
    tc_pr.append(element)


def prevent_row_split(row):
    tr_pr = row._tr.get_or_add_trPr()
    element = OxmlElement("w:cantSplit")
    tr_pr.append(element)


def repeat_header(row):
    tr_pr = row._tr.get_or_add_trPr()
    element = OxmlElement("w:tblHeader")
    tr_pr.append(element)


# --------------------------------------------------------------------------
# the builder
# --------------------------------------------------------------------------
class Doc:
    """Builds one form template."""

    def __init__(self, landscape: bool = False, margin_cm: float = 1.9,
                 base_size: float = 11, font: str = LATIN_FONT):
        self.doc = Document()
        self.base_size = base_size
        self.font = font

        style = self.doc.styles["Normal"]
        style.font.name = font
        style.font.size = Pt(base_size)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.space_before = Pt(0)
        rpr = style.element.get_or_add_rPr()
        fonts = rpr.find(qn("w:rFonts"))
        if fonts is None:
            fonts = OxmlElement("w:rFonts")
            rpr.append(fonts)
        fonts.set(qn("w:cs"), DEVANAGARI_FONT)

        # The scanned originals are A4; python-docx defaults to Letter.
        section = self.doc.sections[0]
        section.page_width, section.page_height = Cm(21.0), Cm(29.7)
        if landscape:
            section.orientation = WD_ORIENT.LANDSCAPE
            section.page_width, section.page_height = Cm(29.7), Cm(21.0)
        for attr in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
            setattr(section, attr, Cm(margin_cm))
        self.section = section

    # -- content width ----------------------------------------------------
    @property
    def content_cm(self) -> float:
        s = self.section
        return (s.page_width - s.left_margin - s.right_margin) / 360000

    # -- paragraphs -------------------------------------------------------
    def para(self, content="", *, bold=False, size=None, align="left",
             italic=False, underline=False, space_after=0, space_before=0,
             font=None, indent=0, first_line=0, line_spacing=None, keep=False):
        """Add a paragraph.

        ``content`` is either a string or a list of (text, opts) run tuples,
        letting one line mix bold placeholders with normal text.
        """
        p = self.doc.add_paragraph()
        p.alignment = ALIGN[align]
        pf = p.paragraph_format
        pf.space_after = Pt(space_after)
        pf.space_before = Pt(space_before)
        if indent:
            pf.left_indent = Cm(indent)
        if first_line:
            pf.first_line_indent = Cm(first_line)
        if line_spacing:
            pf.line_spacing = line_spacing
        if keep:
            pf.keep_with_next = True

        runs = content if isinstance(content, list) else [(content, {})]
        for text, opts in runs:
            if text == "":
                continue
            run = p.add_run(str(text))
            _set_run_bold(run, opts.get("bold", bold))
            run.italic = opts.get("italic", italic)
            run.underline = opts.get("underline", underline)
            _set_run_fonts(run, opts.get("font", font or self.font))
            _set_run_size(run, opts.get("size", size or self.base_size))
        return p

    def blank(self, count=1, size=None):
        for _ in range(count):
            self.para("", size=size)

    def rule(self, size=8):
        """A horizontal rule, as used under the school letterhead."""
        p = self.doc.add_paragraph()
        p_pr = p._p.get_or_add_pPr()
        borders = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), str(size))
        bottom.set(qn("w:space"), "1")
        bottom.set(qn("w:color"), "000000")
        borders.append(bottom)
        p_pr.append(borders)
        return p

    def page_break(self):
        self.doc.add_page_break()

    # -- tables -----------------------------------------------------------
    def table(self, widths, *, borders=True, align="center"):
        """Create an empty table with fixed column widths (cm).

        Word lays a fixed table out from its ``tblGrid``, so the grid has to be
        rewritten to the requested widths -- setting only the per-cell widths
        leaves the grid at python-docx's equal-column default and the table
        renders wider than the page.
        """
        table = self.doc.add_table(rows=0, cols=len(widths))
        table.autofit = False
        tbl_pr = table._tbl.tblPr

        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tbl_pr.append(layout)

        total_twips = int(sum(widths) * 567)
        existing_w = tbl_pr.find(qn("w:tblW"))
        if existing_w is not None:
            tbl_pr.remove(existing_w)
        tbl_w = OxmlElement("w:tblW")
        tbl_w.set(qn("w:w"), str(total_twips))
        tbl_w.set(qn("w:type"), "dxa")
        tbl_pr.append(tbl_w)

        grid = table._tbl.find(qn("w:tblGrid"))
        if grid is not None:
            table._tbl.remove(grid)
        grid = OxmlElement("w:tblGrid")
        for width in widths:
            col = OxmlElement("w:gridCol")
            col.set(qn("w:w"), str(int(width * 567)))
            grid.append(col)
        table._tbl.insert(list(table._tbl).index(tbl_pr) + 1, grid)

        cell_margins(table)
        if borders:
            table_borders(table)
        else:
            no_table_borders(table)
        if align == "center":
            table.alignment = 1
        table._col_widths_cm = list(widths)
        return table

    def row(self, table, cells, *, bold=False, size=None, align="left",
            valign="center", aligns=None, bolds=None, font=None,
            space=1, header=False):
        """Append a row.  ``cells`` may be strings or lists of run tuples."""
        widths = table._col_widths_cm
        tr = table.add_row()
        if header:
            repeat_header(tr)
        prevent_row_split(tr)
        for idx, value in enumerate(cells):
            if idx >= len(tr.cells):
                break
            cell = tr.cells[idx]
            set_cell_width(cell, widths[idx])
            cell.vertical_alignment = VALIGN[valign]
            self.fill_cell(
                cell, value,
                bold=bolds[idx] if bolds else bold,
                align=aligns[idx] if aligns else align,
                size=size, font=font, space=space,
            )
        return tr

    def fill_cell(self, cell, value, *, bold=False, size=None, align="left",
                  font=None, space=1):
        """Replace a cell's content; multi-line strings become multiple paragraphs."""
        cell.paragraphs[0].text = ""
        blocks = value if isinstance(value, list) and value and isinstance(value[0], list) \
            else [value]
        first = True
        for block in blocks:
            p = cell.paragraphs[0] if first else cell.add_paragraph()
            first = False
            p.alignment = ALIGN[align]
            p.paragraph_format.space_after = Pt(space)
            p.paragraph_format.space_before = Pt(0)
            runs = block if isinstance(block, list) else [(block, {})]
            for text, opts in runs:
                # python-docx's Run.text setter turns "\n" into <w:br/> itself.
                run = p.add_run(str(text))
                _set_run_bold(run, opts.get("bold", bold))
                run.italic = opts.get("italic", False)
                run.underline = opts.get("underline", False)
                _set_run_fonts(run, opts.get("font", font or self.font))
                _set_run_size(run, opts.get("size", size or self.base_size))
        return cell

    def cell_para(self, cell, content="", *, reuse_first=False, bold=False,
                  size=None, align="left", italic=False, underline=False,
                  space_after=0, space_before=0, font=None, indent=0,
                  first_line=0, line_spacing=None):
        """Add a fully formatted paragraph inside a table cell.

        Set ``reuse_first`` on the first call to consume the empty paragraph
        python-docx creates with every cell.
        """
        if reuse_first:
            p = cell.paragraphs[0]
            for run in list(p.runs):
                run._element.getparent().remove(run._element)
        else:
            p = cell.add_paragraph()
        p.alignment = ALIGN[align]
        pf = p.paragraph_format
        pf.space_after = Pt(space_after)
        pf.space_before = Pt(space_before)
        if indent:
            pf.left_indent = Cm(indent)
        if first_line:
            pf.first_line_indent = Cm(first_line)
        if line_spacing:
            pf.line_spacing = line_spacing

        runs = content if isinstance(content, list) else [(content, {})]
        for text, opts in runs:
            if text == "":
                continue
            run = p.add_run(str(text))
            _set_run_bold(run, opts.get("bold", bold))
            run.italic = opts.get("italic", italic)
            run.underline = opts.get("underline", underline)
            _set_run_fonts(run, opts.get("font", font or self.font))
            _set_run_size(run, opts.get("size", size or self.base_size))
        return p

    def box(self, width_cm=None, size=8):
        """A single bordered cell, used for the case cover sheet."""
        table = self.table([width_cm or self.content_cm], borders=True)
        tr = table.add_row()
        prevent_row_split(tr)
        cell = tr.cells[0]
        set_cell_width(cell, width_cm or self.content_cm)
        cell_borders(cell, size=size)
        return cell

    def merge_row(self, tr, start, end):
        """Merge cells start..end of a row.

        Word keeps one paragraph per merged cell, so a span of five columns
        leaves four blank lines and a very tall row; drop the empties.
        """
        merged = tr.cells[start]
        for idx in range(start + 1, end + 1):
            merged = merged.merge(tr.cells[idx])
        paragraphs = merged.paragraphs
        for p in paragraphs[1:] if paragraphs[0].text.strip() else paragraphs:
            if not p.text.strip() and len(merged.paragraphs) > 1:
                p._p.getparent().remove(p._p)
        return merged

    # -- signature blocks -------------------------------------------------
    def two_col(self, left, right, *, bold=False, size=None, left_w=None,
                right_align="right", space=0, font=None):
        """Untabled two-column line, e.g. Place/Date on the left and a
        signature caption on the right."""
        total = self.content_cm
        left_w = left_w or total / 2
        table = self.table([left_w, total - left_w], borders=False)
        self.row(table, [left, right], bold=bold, size=size, font=font,
                 aligns=["left", right_align], valign="top", space=space)
        return table

    def save(self, path):
        self.doc.save(str(path))
        return path
