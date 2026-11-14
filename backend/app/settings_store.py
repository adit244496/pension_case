# -*- coding: utf-8 -*-
"""System-wide defaults an administrator can change once for every new case.

The government resolution references quoted on the covering letter are the first
of these: they are the same for every case until a new circular is issued, so
they are held here rather than retyped, and a case that has not been edited
keeps following them.
"""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from .models import Setting

# Shipped values, used until an administrator changes them.
DEFAULTS: dict[str, object] = {
    "default_refs": [
        "वित्त विभाग शासन निर्णय क्र.रानियो-2022/प्र.क्र.34/सेवा-4 दि.31.03.2023",
        "शासन शुद्धीपत्रक क्र.रानियो-2022/प्र.क्र.34/सेवा-4 दिनांक 20.04.2023",
        "शालेय शिक्षण व क्रीडा विभाग, महाराष्ट्र शासन निर्णय क्रमांक अनियो-2023/"
        "प्र.क्र.28/टीएनटी-6 दिनांक 14 जून, 2023",
        "वित्त विभाग शासन परिपत्रक क्र.सेनिप्र.- 2023/प्र.क्र.57/सेवा-4 दि.24.08.2024",
    ],
}


def get_setting(db: Session, key: str):
    row = db.query(Setting).filter_by(key=key).one_or_none()
    if row is None:
        return DEFAULTS.get(key)
    try:
        return json.loads(row.value)
    except (ValueError, TypeError):
        return DEFAULTS.get(key)


def set_setting(db: Session, key: str, value) -> None:
    row = db.query(Setting).filter_by(key=key).one_or_none()
    if row is None:
        row = Setting(key=key)
        db.add(row)
    row.value = json.dumps(value, ensure_ascii=False)
    db.commit()


def reset_setting(db: Session, key: str) -> None:
    row = db.query(Setting).filter_by(key=key).one_or_none()
    if row is not None:
        db.delete(row)
        db.commit()


def apply_defaults(db: Session, data: dict) -> dict:
    """Refresh the parts of a case that follow the system defaults.

    A case carries ``meta.refs_auto``; while it is on, the references are kept in
    step with the defaults, so updating a circular in one place updates every
    case that has not been edited by hand.
    """
    meta = data.setdefault("meta", {})
    if meta.get("refs_auto", True):
        data["refs"] = list(get_setting(db, "default_refs") or [])
    return data
