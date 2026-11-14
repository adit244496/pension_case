"""Transliteration and system defaults."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import current_user, require_admin
from ..db import get_db
from ..models import User
from ..settings_store import DEFAULTS, get_setting, reset_setting, set_setting
from ..translit import GLOSSARY, convert

router = APIRouter(prefix="/api", tags=["tools"],
                   dependencies=[Depends(current_user)])


class ConvertRequest(BaseModel):
    text: str
    direction: str = "auto"          # auto | mr2en | en2mr


@router.post("/transliterate")
def transliterate(payload: ConvertRequest):
    """Convert a name or place between Devanagari and Latin script.

    ``reliable`` is false for the Latin-to-Devanagari direction: English
    spelling does not record vowel length or the retroflex/dental distinction,
    so the result is a draft that must be read and corrected.
    """
    return convert(payload.text, payload.direction)


@router.get("/glossary")
def glossary():
    """Terms that are translated rather than transliterated."""
    return {"terms": GLOSSARY}


class SettingUpdate(BaseModel):
    value: object


@router.get("/settings")
def read_settings(db: Session = Depends(get_db)):
    return {key: get_setting(db, key) for key in DEFAULTS}


@router.put("/settings/{key}")
def write_setting(key: str, payload: SettingUpdate, db: Session = Depends(get_db),
                  _: User = Depends(require_admin)):
    if key not in DEFAULTS:
        from fastapi import HTTPException
        raise HTTPException(404, f"Unknown setting '{key}'")
    set_setting(db, key, payload.value)
    return {key: get_setting(db, key)}


@router.post("/settings/{key}/reset")
def restore_setting(key: str, db: Session = Depends(get_db),
                    _: User = Depends(require_admin)):
    reset_setting(db, key)
    return {key: get_setting(db, key)}
