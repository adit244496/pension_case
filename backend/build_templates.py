# -*- coding: utf-8 -*-
"""Generate the master .docx templates from the form definitions in ``forms/``.

Run this once at install time, and again whenever a form's layout changes in
code.  It never overwrites a template an admin has uploaded (those live under
storage/uploads and are recorded on the FormTemplate row) -- it only rewrites
the code-owned masters in templates/.

    python build_templates.py            # build every template
    python build_templates.py cover_sheet gratuity_calculation
"""
from __future__ import annotations

import sys
from pathlib import Path

from docxbuild import Doc
from forms import ALL_FORMS

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"


def docx_name_for(code: str) -> str:
    return f"{code}.docx"


def build_one(meta: dict) -> Path:
    d = Doc(landscape=meta.get("landscape", False),
            margin_cm=meta.get("margin_cm", 1.6 if meta.get("landscape") else 1.9),
            base_size=meta.get("base_size", 11))
    meta["build"](d)
    TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)
    out = TEMPLATE_DIR / docx_name_for(meta["code"])
    d.save(out)
    return out


def build_all(only: list[str] | None = None) -> list[Path]:
    built = []
    for meta in ALL_FORMS:
        if only and meta["code"] not in only:
            continue
        path = build_one(meta)
        built.append(path)
        print(f"  [{meta['order']:02d}] {meta['code']:<32} -> {path.name}")
    return built


if __name__ == "__main__":
    only = sys.argv[1:] or None
    print(f"Building templates into {TEMPLATE_DIR}")
    paths = build_all(only)
    print(f"\n{len(paths)} template(s) built.")
