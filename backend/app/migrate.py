# -*- coding: utf-8 -*-
"""Additive schema migration for the SQLite database.

``create_all`` makes new tables but never alters existing ones, so a database
created by an earlier version is missing any newly added columns. Rather than
pull in Alembic for a single-file office database, new columns are added here
with their defaults. Only additions are performed -- nothing is dropped or
rewritten, so running this against an up-to-date database does nothing.
"""
from __future__ import annotations

from sqlalchemy import inspect, text

from .db import Base, engine

# table -> column -> SQL type and default, matching models.py
NEW_COLUMNS: dict[str, dict[str, str]] = {
    "form_templates": {
        "builtin": "BOOLEAN DEFAULT 1",
        "archived": "BOOLEAN DEFAULT 0",
        "notes": "TEXT DEFAULT ''",
        "version": "INTEGER DEFAULT 1",
    },
    "text_blocks": {
        "multiline": "BOOLEAN DEFAULT 0",
        "order_no": "INTEGER DEFAULT 0",
        "default_value": "TEXT DEFAULT ''",
    },
    "cases": {
        "revision": "INTEGER DEFAULT 1",
        "generated_revision": "INTEGER DEFAULT 0",
        "regen_state": "VARCHAR(16) DEFAULT 'idle'",
        "regen_error": "TEXT DEFAULT ''",
    },
    "generated_docs": {
        "manual": "BOOLEAN DEFAULT 0",
        "manual_at": "DATETIME",
        "manual_by": "VARCHAR(64) DEFAULT ''",
        "pdf_error": "TEXT DEFAULT ''",
        "title_en": "VARCHAR(255) DEFAULT ''",
        "order_no": "INTEGER DEFAULT 0",
        "built_stamp": "VARCHAR(64) DEFAULT ''",
    },
}


def migrate() -> list[str]:
    """Create missing tables, then add any missing columns. Returns what changed."""
    Base.metadata.create_all(engine)
    applied: list[str] = []
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.begin() as connection:
        for table, columns in NEW_COLUMNS.items():
            if table not in existing_tables:
                continue
            present = {c["name"] for c in inspector.get_columns(table)}
            for name, definition in columns.items():
                if name in present:
                    continue
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {definition}"))
                applied.append(f"{table}.{name}")
    return applied
