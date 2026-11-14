"""Template administration: wording, layout, ordering, and adding or removing forms."""
from __future__ import annotations

import re
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import schemas
from ..auth import current_user, require_admin
from ..config import TEMPLATE_DIR, UPLOAD_DIR
from ..db import get_db
from ..models import Case, FormTemplate, TextBlock, User
from ..render import placeholders_in, template_path

router = APIRouter(prefix="/api/templates", tags=["templates"],
                   dependencies=[Depends(current_user)])

BLOCK_KEY_RE = re.compile(r"\bt\.([a-zA-Z_]\w*)")


def _get_template(db: Session, template_id: int) -> FormTemplate:
    template = db.get(FormTemplate, template_id)
    if template is None:
        raise HTTPException(404, "Template not found")
    return template


def _detail(template: FormTemplate) -> schemas.TemplateDetail:
    return schemas.TemplateDetail(
        id=template.id, code=template.code, order_no=template.order_no,
        title_en=template.title_en, title_mr=template.title_mr,
        language=template.language, landscape=template.landscape,
        enabled=template.enabled, docx_name=template.docx_name,
        version=template.version, updated_at=template.updated_at,
        builtin=template.builtin, archived=template.archived,
        notes=template.notes or "",
        blocks=[schemas.TextBlockOut.model_validate(b) for b in template.blocks],
        placeholders=placeholders_in(template.docx_name),
    )


def sync_blocks_from_docx(db: Session, template: FormTemplate) -> list[str]:
    """Create a text block for every ``{{ t.key }}`` found in the .docx.

    Lets an admin add an editable sentence simply by writing the placeholder into
    the Word file; the new key appears on the wording screen after upload.
    """
    names = {m.group(1) for name in placeholders_in(template.docx_name)
             for m in [BLOCK_KEY_RE.fullmatch(name)] if m}
    existing = {b.key for b in template.blocks}
    added = []
    next_order = max((b.order_no for b in template.blocks), default=-1) + 1
    for key in sorted(names - existing):
        db.add(TextBlock(template_id=template.id, key=key,
                         label=key.replace("_", " ").capitalize(),
                         value="", default_value="", order_no=next_order,
                         multiline=True))
        next_order += 1
        added.append(key)
    if added:
        db.commit()
        db.refresh(template)
    return added


# --------------------------------------------------------------------------
# listing and editing
# --------------------------------------------------------------------------
@router.get("", response_model=list[schemas.TemplateSummary])
def list_templates(include_archived: bool = False, db: Session = Depends(get_db)):
    query = db.query(FormTemplate).order_by(FormTemplate.order_no, FormTemplate.id)
    return [t for t in query.all() if include_archived or not t.archived]


@router.get("/placeholders")
def available_placeholders():
    """Every value a form can use, grouped -- the reference for authoring a new form."""
    from ..context import EMPTY_CASE
    from ..fields import TABLE_SECTIONS

    groups = {
        "emp": ["name_en", "name_mr", "name_en_upper", "designation_en",
                "designation_en_upper", "designation_mr", "father_name_en",
                "mother_name_en", "spouse_name_en", "dob_f", "dor_f",
                "doj_unaided_f", "doj_aided_f", "doj_combined", "address_block",
                "address_inline", "age_at_retirement", "mobile", "email", "pan",
                "aadhaar", "height", "marks_list", "sex", "group_class",
                "religion_caste", "nationality", "substantive"],
        "school": sorted(EMPTY_CASE["school"]),
        "office": sorted(EMPTY_CASE["office"]),
        "meta": sorted(EMPTY_CASE["meta"]),
        "bank": sorted(EMPTY_CASE["bank"]),
        "pay": ["basic_r", "da_r", "hra_r", "ta_r", "other_r", "total_r",
                "matrix_full", "level", "matrix", "paid_upto", "da_pct", "hra_pct"],
        "svc": ["net.dashed", "net.words_en", "net.y", "net.mm", "net.dd",
                "gross.dashed", "gross.words_en", "non_qualifying.dashed",
                "rendered.dashed", "unaided.dashed", "unaided_end_f", "periods",
                "periods_words", "last_pay_r", "dcrg_r", "dcrg_formula",
                "dcrg_words_en", "dcrg_words_mr"],
        "chk": sorted(EMPTY_CASE["checklist"]),
        "tbl": [t["key"] for t in TABLE_SECTIONS],
        "": ["letter_date", "letter_date_mr", "today", "place", "place_mr", "refs"],
    }
    filters = ["dt", "dt_mr", "dt_long", "dt_mr_long", "dev", "money", "inr",
               "words_en", "words_mr", "ordinal", "upper2", "blank", "roman"]
    return {"groups": groups, "filters": filters,
            "note": "Repeating tables are used as {%tr for r in tbl.leave %} ... "
                    "{%tr endfor %} inside a table row."}


@router.get("/{template_id}", response_model=schemas.TemplateDetail)
def get_template(template_id: int, db: Session = Depends(get_db)):
    return _detail(_get_template(db, template_id))


@router.patch("/{template_id}", response_model=schemas.TemplateDetail)
def update_template(template_id: int, payload: schemas.TemplateUpdate,
                    db: Session = Depends(get_db)):
    template = _get_template(db, template_id)
    for field in ("enabled", "order_no", "title_en", "title_mr", "notes", "language"):
        value = getattr(payload, field, None)
        if value is not None:
            setattr(template, field, value)
    db.commit()
    db.refresh(template)
    return _detail(template)


@router.put("/{template_id}/blocks", response_model=schemas.TemplateDetail)
def update_blocks(template_id: int, payload: schemas.BlocksUpdate,
                  db: Session = Depends(get_db)):
    """Save the admin's edited wording. Layout is untouched."""
    template = _get_template(db, template_id)
    by_key = {b.key: b for b in template.blocks}
    unknown = [b.key for b in payload.blocks if b.key not in by_key]
    if unknown:
        raise HTTPException(400, f"Unknown text block(s): {', '.join(unknown)}")
    for update in payload.blocks:
        by_key[update.key].value = update.value
    template.version += 1
    db.commit()
    db.refresh(template)
    return _detail(template)


@router.post("/{template_id}/blocks/reset", response_model=schemas.TemplateDetail)
def reset_blocks(template_id: int, db: Session = Depends(get_db)):
    """Restore every sentence on this form to the wording shipped with the system."""
    template = _get_template(db, template_id)
    for block in template.blocks:
        block.value = block.default_value
    template.version += 1
    db.commit()
    db.refresh(template)
    return _detail(template)


# --------------------------------------------------------------------------
# adding, removing and ordering forms
# --------------------------------------------------------------------------
def _unique_code(db: Session, title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", (title or "form").lower()).strip("_")[:48] or "form"
    code = base
    n = 2
    while db.query(FormTemplate).filter_by(code=code).first():
        code = f"{base}_{n}"
        n += 1
    return code


@router.post("", response_model=schemas.TemplateDetail, status_code=201)
async def create_template(
    title_en: str = Form(...),
    title_mr: str = Form(""),
    language: str = Form("en"),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Add a form of your own, from a Word file containing {{ }} placeholders.

    Without a file, a starter document is created that can be downloaded, laid
    out in Word and uploaded back.
    """
    code = _unique_code(db, title_en)
    docx_name = f"{code}.docx"
    target = template_path(docx_name)

    if file is not None:
        if not (file.filename or "").lower().endswith(".docx"):
            raise HTTPException(400, "Upload a .docx file")
        payload = await file.read()
        if not payload.startswith(b"PK"):
            raise HTTPException(400, "That does not look like a .docx file")
        target.write_bytes(payload)
    else:
        _starter_document(target, title_en, title_mr)

    last = db.query(FormTemplate).order_by(FormTemplate.order_no.desc()).first()
    template = FormTemplate(
        code=code, docx_name=docx_name, title_en=title_en,
        title_mr=title_mr or title_en, language=language,
        order_no=(last.order_no + 1) if last else 1,
        builtin=False, enabled=True,
    )
    db.add(template)
    db.commit()
    db.refresh(template)

    if not placeholders_in(docx_name) and file is not None:
        pass                               # a form with no placeholders is still valid
    sync_blocks_from_docx(db, template)
    db.refresh(template)
    return _detail(template)


def _starter_document(target: Path, title_en: str, title_mr: str) -> None:
    """A minimal form the admin can lay out in Word."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from docxbuild import DEVANAGARI_FONT, Doc                      # noqa: E402

    d = Doc()
    if title_mr:
        d.para(title_mr, align="center", size=13, bold=True,
               font=DEVANAGARI_FONT, space_after=2)
    d.para(title_en, align="center", size=12, bold=True, space_after=10)
    d.para("{{ emp.name_en_upper }}, {{ emp.designation_en_upper }}", size=11, bold=True)
    d.para("{{ school.name_en }}", size=11, space_after=10)
    d.para("Replace this text with the body of the form. Use placeholders such as "
           "{{ emp.dob_f }}, {{ emp.dor_f }} and {{ svc.dcrg_r }}.", size=11,
           align="justify")
    d.blank(2)
    d.two_col("Place : {{ meta.place }}\nDate  : {{ letter_date }}", "Head Master",
              size=11, right_align="center")
    d.save(target)


@router.post("/reorder", response_model=list[schemas.TemplateSummary])
def reorder(payload: schemas.ReorderRequest, db: Session = Depends(get_db),
            _: User = Depends(require_admin)):
    """Set the printing order of the case from a list of template ids."""
    templates = {t.id: t for t in db.query(FormTemplate).all()}
    unknown = [i for i in payload.ids if i not in templates]
    if unknown:
        raise HTTPException(400, f"Unknown template id(s): {unknown}")
    for position, template_id in enumerate(payload.ids, start=1):
        templates[template_id].order_no = position
    db.commit()
    return db.query(FormTemplate).order_by(FormTemplate.order_no).all()


@router.delete("/{template_id}", status_code=204)
def delete_template(template_id: int, db: Session = Depends(get_db),
                    _: User = Depends(require_admin)):
    """Remove a form from the case.

    A form added by an admin is deleted outright. One that ships with the system
    is archived instead, so that re-registering the built-in set does not bring it
    back; it can be restored from the archived list.
    """
    template = _get_template(db, template_id)
    if template.builtin:
        template.archived = True
        template.enabled = False
        db.commit()
        return
    template_path(template.docx_name).unlink(missing_ok=True)
    db.delete(template)
    db.commit()


@router.post("/{template_id}/restore", response_model=schemas.TemplateDetail)
def restore_template(template_id: int, db: Session = Depends(get_db),
                     _: User = Depends(require_admin)):
    template = _get_template(db, template_id)
    template.archived = False
    template.enabled = True
    db.commit()
    db.refresh(template)
    return _detail(template)


# --------------------------------------------------------------------------
# layout
# --------------------------------------------------------------------------
@router.get("/{template_id}/docx")
def download_template(template_id: int, resolved: bool = False,
                      db: Session = Depends(get_db)):
    """Download the form's Word file, to adjust it and upload it back.

    ``resolved`` fills in the editable wording first, so the Marathi reads
    normally in Word instead of showing ``{{ t.subject }}``; the placeholders
    that carry case data are always left in place.
    """
    template = _get_template(db, template_id)
    path = template_path(template.docx_name)
    if not path.exists():
        raise HTTPException(404, "Template file is missing")

    filename = template.docx_name
    if resolved:
        from ..config import STORAGE_DIR
        from ..render import resolve_text_blocks
        out_dir = STORAGE_DIR / "_downloads"
        out_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{template.code}_with_wording.docx"
        path = resolve_text_blocks(
            template.docx_name, {b.key: b.value for b in template.blocks},
            out_dir / filename)

    return FileResponse(
        path, filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/{template_id}/docx", response_model=schemas.TemplateDetail)
async def upload_template(template_id: int, file: UploadFile = File(...),
                          db: Session = Depends(get_db),
                          _: User = Depends(require_admin)):
    """Replace a form's layout with an admin-edited .docx.

    The previous file is kept under storage/uploads so a bad upload can be undone.
    """
    template = _get_template(db, template_id)
    if not (file.filename or "").lower().endswith(".docx"):
        raise HTTPException(400, "Upload a .docx file")

    target = template_path(template.docx_name)
    if target.exists():
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = UPLOAD_DIR / template.code
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(target, backup_dir / f"{stamp}_v{template.version}.docx")

    payload = await file.read()
    if not payload.startswith(b"PK"):
        raise HTTPException(400, "That does not look like a .docx file")
    previous = target.read_bytes() if target.exists() else None
    target.write_bytes(payload)

    if not _readable(template.docx_name):
        if previous is not None:
            target.write_bytes(previous)
        raise HTTPException(400, "The uploaded file could not be read as a Word document")

    template.version += 1
    db.commit()
    db.refresh(template)
    sync_blocks_from_docx(db, template)
    db.refresh(template)
    return _detail(template)


def _readable(docx_name: str) -> bool:
    from docx import Document
    try:
        Document(str(template_path(docx_name)))
        return True
    except Exception:                                  # noqa: BLE001
        return False


@router.get("/{template_id}/backups")
def list_backups(template_id: int, db: Session = Depends(get_db)):
    template = _get_template(db, template_id)
    backup_dir = UPLOAD_DIR / template.code
    if not backup_dir.exists():
        return []
    return sorted(
        ({"name": p.name, "size": p.stat().st_size,
          "saved_at": datetime.fromtimestamp(p.stat().st_mtime).isoformat()}
         for p in backup_dir.glob("*.docx")),
        key=lambda item: item["saved_at"], reverse=True,
    )


@router.post("/{template_id}/restore-backup/{backup_name}",
             response_model=schemas.TemplateDetail)
def restore_backup(template_id: int, backup_name: str, db: Session = Depends(get_db),
                   _: User = Depends(require_admin)):
    template = _get_template(db, template_id)
    backup_dir = (UPLOAD_DIR / template.code).resolve()
    source = (backup_dir / backup_name).resolve()
    if source.parent != backup_dir or not source.exists():
        raise HTTPException(404, "Backup not found")
    shutil.copy2(source, template_path(template.docx_name))
    template.version += 1
    db.commit()
    db.refresh(template)
    return _detail(template)


@router.post("/{template_id}/rebuild", response_model=schemas.TemplateDetail)
def rebuild_template(template_id: int, db: Session = Depends(get_db),
                     _: User = Depends(require_admin)):
    """Regenerate this form's .docx from the layout defined in code.

    Discards an uploaded layout; the admin's text-block wording is unaffected.
    """
    template = _get_template(db, template_id)
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from build_templates import build_all

    if not template.builtin or not build_all([template.code]):
        raise HTTPException(404, f"No built-in layout for '{template.code}'")
    template.version += 1
    db.commit()
    db.refresh(template)
    return _detail(template)


# --------------------------------------------------------------------------
# preview
# --------------------------------------------------------------------------
@router.get("/{template_id}/preview")
def preview(template_id: int, case_id: int | None = None, fmt: str = "pdf",
            db: Session = Depends(get_db)):
    """Render this form with sample data, values that vary shown highlighted.

    Served inline so the browser opens it in a tab instead of downloading it.
    """
    if fmt not in ("pdf", "docx"):
        raise HTTPException(400, "fmt must be 'pdf' or 'docx'")
    template = _get_template(db, template_id)

    case = db.get(Case, case_id) if case_id else None
    if case is None:
        case = db.query(Case).order_by(Case.updated_at.desc()).first()
    if case is None:
        raise HTTPException(400, "Create a case first, so the preview has data to show")

    from ..config import STORAGE_DIR
    from ..render import render_form

    out_dir = STORAGE_DIR / "_previews"
    out_dir.mkdir(parents=True, exist_ok=True)
    result = render_form(case, template, {b.key: b.value for b in template.blocks},
                         make_pdf=(fmt == "pdf"), preview=True, out_dir=out_dir)

    if fmt == "pdf" and not result["pdf_path"]:
        raise HTTPException(
            503, result["pdf_error"] or "PDF preview needs Word or LibreOffice installed")

    path = Path(result["pdf_path"] if fmt == "pdf" else result["docx_path"])
    media = ("application/pdf" if fmt == "pdf" else
             "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    return FileResponse(
        path, media_type=media,
        headers={"Content-Disposition": f'inline; filename="{path.name}"',
                 "Cache-Control": "no-store"},
    )
