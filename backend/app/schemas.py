"""Request and response models."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CaseSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_no: str
    employee_name_en: str = ""
    employee_name_mr: str = ""
    status: str = "draft"
    document_count: int = 0
    documents_stale: bool = False
    regen_state: str = "idle"
    regen_error: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CaseDetail(CaseSummary):
    data: dict[str, Any] = Field(default_factory=dict)
    computed: dict[str, Any] = Field(default_factory=dict)
    manual_changes: list[dict[str, Any]] = Field(default_factory=list)


class CaseCreate(BaseModel):
    case_no: str | None = None
    data: dict[str, Any] | None = None
    copy_from: int | None = None       # duplicate an existing case's data


class CaseUpdate(BaseModel):
    case_no: str | None = None
    status: str | None = None
    data: dict[str, Any] | None = None


class TextBlockOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    key: str
    label: str = ""
    value: str = ""
    default_value: str = ""
    multiline: bool = False
    order_no: int = 0


class TemplateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    order_no: int
    title_en: str = ""
    title_mr: str = ""
    language: str = "en"
    landscape: bool = False
    enabled: bool = True
    builtin: bool = True
    archived: bool = False
    docx_name: str = ""
    version: int = 1
    updated_at: datetime | None = None


class TemplateDetail(TemplateSummary):
    blocks: list[TextBlockOut] = Field(default_factory=list)
    placeholders: list[str] = Field(default_factory=list)
    notes: str = ""


class TemplateUpdate(BaseModel):
    enabled: bool | None = None
    order_no: int | None = None
    title_en: str | None = None
    title_mr: str | None = None
    language: str | None = None
    notes: str | None = None


class ReorderRequest(BaseModel):
    ids: list[int]


class BlockUpdate(BaseModel):
    key: str
    value: str


class BlocksUpdate(BaseModel):
    blocks: list[BlockUpdate]


class GeneratedDocOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_code: str
    title_en: str = ""
    order_no: int = 0
    docx_path: str = ""
    pdf_path: str = ""
    pdf_error: str = ""
    manual: bool = False
    manual_at: datetime | None = None
    manual_by: str = ""
    included: bool = True
    created_at: datetime | None = None


class GenerateRequest(BaseModel):
    codes: list[str] | None = None      # None means every included form
    make_pdf: bool = True
    force: bool = False                 # also rebuild manually edited documents


class FormPreference(BaseModel):
    code: str
    order: int | None = None
    included: bool | None = None


class FormPreferences(BaseModel):
    forms: list[FormPreference]


class PreviewRequest(BaseModel):
    data: dict[str, Any] | None = None


class DocumentEdit(BaseModel):
    """One piece of a generated document, addressed by where it sits in it."""
    id: str
    text: str


class DocumentEdits(BaseModel):
    edits: list[DocumentEdit]
