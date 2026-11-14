"""Database models.

A pension case keeps all of its fields and repeating tables in a single JSON
document (``data``). The forms only ever read from that document, so adding a
field to an intake screen never needs a migration.
"""
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text, UniqueConstraint)
from sqlalchemy.orm import relationship

from .db import Base


class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True)
    case_no = Column(String(64), unique=True, index=True, nullable=False)
    employee_name_en = Column(String(255), default="")
    employee_name_mr = Column(String(255), default="")
    status = Column(String(32), default="draft")       # draft | ready | generated
    # Bumped on every save; documents record the revision they were built from,
    # so the UI can tell when the forms no longer match the case.
    revision = Column(Integer, default=1, nullable=False)
    generated_revision = Column(Integer, default=0, nullable=False)
    regen_state = Column(String(16), default="idle")   # idle | running | error
    regen_error = Column(Text, default="")
    data = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    documents = relationship("GeneratedDoc", back_populates="case",
                             cascade="all, delete-orphan")

    @property
    def document_count(self) -> int:
        """Whether this case can be exported yet -- shown on the case list."""
        return len(self.documents)

    @property
    def documents_stale(self) -> bool:
        """True when the case has been edited since the forms were produced."""
        return bool(self.documents) and self.generated_revision != self.revision


class FormTemplate(Base):
    """One document in a DCRG case.

    Templates shipped with the system are ``builtin`` and can be rebuilt from
    code; admins may also add their own and reorder or remove any of them.
    Removing a builtin form archives it rather than deleting it, so that
    re-registering the built-in set does not bring it back.
    """
    __tablename__ = "form_templates"

    id = Column(Integer, primary_key=True)
    code = Column(String(64), unique=True, index=True, nullable=False)
    order_no = Column(Integer, default=0)
    title_en = Column(String(255), default="")
    title_mr = Column(String(255), default="")
    docx_name = Column(String(255), nullable=False)     # file inside templates/
    language = Column(String(8), default="en")          # en | mr | both
    landscape = Column(Boolean, default=False)
    enabled = Column(Boolean, default=True)
    builtin = Column(Boolean, default=True)
    archived = Column(Boolean, default=False)
    notes = Column(Text, default="")
    version = Column(Integer, default=1)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    blocks = relationship("TextBlock", back_populates="template",
                          cascade="all, delete-orphan",
                          order_by="TextBlock.order_no")


class TextBlock(Base):
    """An editable sentence/label inside a template, addressed as {{ t.key }}.

    Admins reword these in the browser; the .docx layout stays untouched.
    """
    __tablename__ = "text_blocks"
    __table_args__ = (UniqueConstraint("template_id", "key", name="uq_block_key"),)

    id = Column(Integer, primary_key=True)
    template_id = Column(Integer, ForeignKey("form_templates.id", ondelete="CASCADE"))
    key = Column(String(128), nullable=False)
    label = Column(String(255), default="")             # what this block is, for the admin
    value = Column(Text, default="")                    # current (editable) text
    default_value = Column(Text, default="")            # seeded text, for "reset"
    order_no = Column(Integer, default=0)
    multiline = Column(Boolean, default=False)

    template = relationship("FormTemplate", back_populates="blocks")


class GeneratedDoc(Base):
    __tablename__ = "generated_docs"

    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), index=True)
    template_code = Column(String(64), nullable=False)
    title_en = Column(String(255), default="")
    order_no = Column(Integer, default=0)
    docx_path = Column(String(512), default="")
    pdf_path = Column(String(512), default="")
    pdf_error = Column(Text, default="")
    # Set when the operator uploads their own edited .docx for this form. Such a
    # document is never overwritten by a rebuild until it is reset.
    manual = Column(Boolean, default=False, nullable=False)
    manual_at = Column(DateTime, nullable=True)
    manual_by = Column(String(64), default="")
    # Size and mtime of the .docx as this system last wrote it. Anything else on
    # disk means the file was changed from outside -- Word, usually -- which is
    # how such an edit is noticed without the operator having to say so.
    built_stamp = Column(String(64), default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("Case", back_populates="documents")


class Setting(Base):
    """System-wide defaults, stored as JSON text under a key."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True)
    key = Column(String(64), unique=True, index=True, nullable=False)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    display_name = Column(String(128), default="")
    password_hash = Column(String(255), nullable=False)
    role = Column(String(16), default="admin")          # admin | operator
    must_change_password = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
