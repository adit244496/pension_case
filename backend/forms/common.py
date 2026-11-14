# -*- coding: utf-8 -*-
"""Shared pieces used by more than one form template."""
from docxbuild import DEVANAGARI_FONT, Doc, cell_borders  # noqa: F401

MR = DEVANAGARI_FONT
EN = "Times New Roman"


def loop_start(d: Doc, table, expr: str, ncols: int):
    """Open a docxtpl row loop: this row is removed at render time."""
    d.row(table, ["{%tr for " + expr + " %}"] + [""] * (ncols - 1), size=6)


def loop_end(d: Doc, table, ncols: int):
    d.row(table, ["{%tr endfor %}"] + [""] * (ncols - 1), size=6)


def letterhead_mr(d: Doc, rule: bool = True):
    """School letterhead in Marathi, as on the covering letter."""
    d.para("{{ school.society_line_mr }}", align="center", size=10, font=MR)
    d.para("{{ school.name_mr }}", align="center", size=16, bold=True, font=MR)
    d.para("ता.{{ school.taluka_mr }}, जि.{{ school.district_mr }}.",
           align="center", size=13, bold=True, font=MR)
    if rule:
        d.rule()


def letterhead_en(d: Doc, rule: bool = True):
    d.para("{{ school.society_line_en }}", align="center", size=10)
    d.para("{{ school.name_en }}", align="center", size=12, bold=True, underline=True)
    d.para("TAL. {{ school.taluka_en }}, DIST. {{ school.district_en }}",
           align="center", size=12, bold=True, underline=True)
    if rule:
        d.rule()


def sr_no(d: Doc, key: str = "sr_no"):
    """The 'Sr. No. NN' marker printed at the top-right of the annexures."""
    d.para("Sr. No. {{ t." + key + " }}", align="right", size=11)


def countersign_block(d: Doc, right_lines, left_key="cs_left", size=11):
    """Countersigned-by block on the left, signature caption on the right."""
    right = "\n".join(right_lines) if isinstance(right_lines, list) else right_lines
    d.two_col("{{ t." + left_key + " }}", right, size=size, right_align="left",
              left_w=d.content_cm * 0.55)


def place_date(d: Doc, place_expr="{{ meta.place }}", date_expr="{{ letter_date }}",
               size=11, labels=("Place", "Date")):
    d.para(f"{labels[0]} : {place_expr}", size=size)
    d.para(f"{labels[1]} : {date_expr}", size=size)
