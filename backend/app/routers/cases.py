"""Case CRUD, document generation and downloads."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import (APIRouter, BackgroundTasks, Depends, File, HTTPException,
                     Query, Request, UploadFile)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.orm.attributes import flag_modified

from .. import schemas
from ..auth import current_user
from ..models import User  # noqa: F401
from ..context import EMPTY_CASE, build_context, merge_defaults
from ..db import get_db
from ..fields import form_schema
from ..generate import (case_bundle, form_prefs, generate_case,
                        regenerate_in_background)
from ..models import Case, FormTemplate
from ..settings_store import apply_defaults
from ..word_sync import documents_tick, pick_up_word_edits, remake_pdf

router = APIRouter(prefix="/api/cases", tags=["cases"],
                   dependencies=[Depends(current_user)])

MEDIA_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "zip": "application/zip",
}


def _get_case(db: Session, case_id: int) -> Case:
    case = db.get(Case, case_id)
    if case is None:
        raise HTTPException(404, "Case not found")
    return case


def _computed(case: Case) -> dict:
    """The derived figures the UI shows live while the case is being filled."""
    ctx = build_context(case.data or {})
    svc = ctx["svc"]
    return {
        "gross_service": svc["gross"],
        "non_qualifying": svc["non_qualifying"],
        "net_qualifying": svc["net"],
        "unaided": svc["unaided"],
        "rendered": svc["rendered"],
        "six_monthly_periods": svc["periods"],
        "period_cap_reached": svc["capped"],
        "last_pay": svc["last_pay"],
        "gratuity": svc["dcrg"],
        "gratuity_formatted": svc["dcrg_r"],
        "gratuity_words_en": svc["dcrg_words_en"],
        "gratuity_words_mr": svc["dcrg_words_mr"],
        "formula": svc["dcrg_formula"],
        "age_at_retirement": ctx["emp"]["age_at_retirement"],
    }


def manual_changes(db: Session, case: Case) -> list[dict]:
    """Everything on this case that departs from what the system would produce.

    Surfaced as notes so a reviewer can see at a glance which figures were
    entered by hand and which documents were edited outside the system.
    """
    notes: list[dict] = []
    data = merge_defaults(case.data)
    ctx = build_context(data)

    if str(data["service"].get("gratuity_override") or "").strip():
        notes.append({"kind": "field", "key": "service.gratuity_override",
                      "label_en": "Gratuity amount entered by hand",
                      "label_mr": "उपदान रक्कम स्वतः भरली",
                      "value": str(data["service"]["gratuity_override"])})

    if data["meta"].get("refs_auto") is False:
        notes.append({"kind": "field", "key": "refs",
                      "label_en": "Government resolution references edited for this case",
                      "label_mr": "या प्रकरणासाठी शासन निर्णय संदर्भ बदलले",
                      "value": f"{len(data.get('refs') or [])} entries"})

    from ..compute import age_on, parse_date
    on_date = data["meta"].get("letter_date")
    for index, row in enumerate(data["tables"].get("leave", []), start=1):
        typed = str(row.get("days") or "").strip()
        a, b = parse_date(row.get("frm")), parse_date(row.get("to"))
        if typed and a and b:
            computed = (b - a).days + 1
            if typed != str(computed):
                notes.append({"kind": "table", "key": f"leave[{index}].days",
                              "label_en": f"Leave row {index}: {typed} days entered, "
                                          f"{computed} by the dates",
                              "label_mr": f"रजा ओळ {index}: भरलेले {typed} दिवस, "
                                          f"दिनांकानुसार {computed}",
                              "value": typed})
    for table, label in (("family", "Family member"), ("nominees", "Nominee")):
        for index, row in enumerate(data["tables"].get(table, []), start=1):
            typed = str(row.get("age") or "").strip()
            computed = age_on(row.get("dob"), on_date)
            if typed and computed != "" and typed != str(computed):
                notes.append({"kind": "table", "key": f"{table}[{index}].age",
                              "label_en": f"{label} {index}: age {typed} entered, "
                                          f"{computed} by the date of birth",
                              "label_mr": f"{label} {index}: वय {typed} भरले, "
                                          f"जन्मतारखेनुसार {computed}",
                              "value": typed})

    for doc in sorted(case.documents, key=lambda d: d.order_no):
        if doc.manual:
            when = doc.manual_at.strftime("%d-%m-%Y %H:%M") if doc.manual_at else ""
            notes.append({"kind": "document", "key": doc.template_code,
                          "doc_id": doc.id,
                          "label_en": f"{doc.title_en} — replaced with an edited file",
                          "label_mr": f"{doc.title_en} — संपादित फाईलने बदलले",
                          "value": when})

    prefs = form_prefs(case)
    excluded = [c for c, v in prefs.items() if v.get("included") is False]
    if excluded:
        notes.append({"kind": "forms", "key": "excluded",
                      "label_en": f"{len(excluded)} form(s) left out of the final file",
                      "label_mr": f"{len(excluded)} नमुने अंतिम फाईलमधून वगळले",
                      "value": ", ".join(excluded)})
    return notes


def _detail(case: Case, db: Session | None = None) -> schemas.CaseDetail:
    return schemas.CaseDetail(
        id=case.id, case_no=case.case_no,
        employee_name_en=case.employee_name_en or "",
        employee_name_mr=case.employee_name_mr or "",
        status=case.status, created_at=case.created_at, updated_at=case.updated_at,
        document_count=case.document_count, documents_stale=case.documents_stale,
        regen_state=case.regen_state or "idle", regen_error=case.regen_error or "",
        data=merge_defaults(case.data), computed=_computed(case),
        manual_changes=manual_changes(db, case) if db is not None else [],
    )


@router.get("/schema")
def get_schema():
    """Field definitions (bilingual) plus a blank case, for the intake screens."""
    return {"schema": form_schema(), "empty_case": EMPTY_CASE}


@router.get("", response_model=list[schemas.CaseSummary])
def list_cases(db: Session = Depends(get_db), q: str = Query("", description="search")):
    # Load the documents alongside, so document_count does not fire a query per row.
    query = (db.query(Case)
             .options(selectinload(Case.documents))
             .order_by(Case.updated_at.desc()))
    if q:
        like = f"%{q}%"
        query = query.filter(Case.case_no.ilike(like) |
                             Case.employee_name_en.ilike(like) |
                             Case.employee_name_mr.ilike(like))
    return query.all()


@router.post("", response_model=schemas.CaseDetail, status_code=201)
def create_case(payload: schemas.CaseCreate, db: Session = Depends(get_db)):
    data = payload.data
    if payload.copy_from:
        source = _get_case(db, payload.copy_from)
        data = merge_defaults(source.data)
        # A duplicate is a new person's case: keep the school and office blocks,
        # clear everything specific to the retiring employee.
        blank = merge_defaults({})
        for section in ("employee", "pay", "bank", "service", "tables", "checklist"):
            data[section] = blank[section]
        data["meta"] = {**blank["meta"],
                        "place": data["meta"].get("place", ""),
                        "place_mr": data["meta"].get("place_mr", "")}

    data = apply_defaults(db, merge_defaults(data))
    case_no = payload.case_no or data["meta"].get("case_no") or _next_case_no(db)
    if db.query(Case).filter_by(case_no=case_no).first():
        raise HTTPException(409, f"Case number '{case_no}' already exists")
    data["meta"]["case_no"] = case_no

    case = Case(case_no=case_no, data=data,
                employee_name_en=data["employee"].get("name_en", ""),
                employee_name_mr=data["employee"].get("name_mr", ""))
    db.add(case)
    db.commit()
    db.refresh(case)
    return _detail(case, db)


def _next_case_no(db: Session) -> str:
    year = datetime.now().year
    prefix = f"DCRG-{year}-"
    existing = [c.case_no for c in db.query(Case).filter(Case.case_no.like(f"{prefix}%")).all()]
    numbers = []
    for value in existing:
        tail = value.rsplit("-", 1)[-1]
        if tail.isdigit():
            numbers.append(int(tail))
    return f"{prefix}{(max(numbers) + 1) if numbers else 1:03d}"


@router.get("/{case_id}", response_model=schemas.CaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db)):
    return _detail(_get_case(db, case_id), db)


@router.put("/{case_id}", response_model=schemas.CaseDetail)
def update_case(case_id: int, payload: schemas.CaseUpdate,
                background: BackgroundTasks, db: Session = Depends(get_db),
                regenerate: bool = True):
    """Save a case; forms that were already produced are rebuilt in the background."""
    case = _get_case(db, case_id)
    if payload.data is not None:
        data = apply_defaults(db, merge_defaults(payload.data))
        case.data = data
        case.employee_name_en = data["employee"].get("name_en", "")
        case.employee_name_mr = data["employee"].get("name_mr", "")
    if payload.case_no and payload.case_no != case.case_no:
        if db.query(Case).filter(Case.case_no == payload.case_no,
                                 Case.id != case.id).first():
            raise HTTPException(409, f"Case number '{payload.case_no}' already exists")
        case.case_no = payload.case_no
        case.data = {**case.data, "meta": {**case.data.get("meta", {}),
                                           "case_no": payload.case_no}}
    if payload.status:
        case.status = payload.status
    case.revision = (case.revision or 1) + 1
    db.commit()
    db.refresh(case)

    # Editing a detail changes almost every form, so rebuild them rather than
    # leaving the operator with documents that quietly disagree with the case.
    if regenerate and case.documents:
        background.add_task(regenerate_in_background, case.id)
    return _detail(case, db)


@router.delete("/{case_id}", status_code=204)
def delete_case(case_id: int, db: Session = Depends(get_db)):
    db.delete(_get_case(db, case_id))
    db.commit()


PHOTO_TYPES = {"image/jpeg": ".jpg", "image/png": ".png"}
MAX_PHOTO_BYTES = 8 * 1024 * 1024


@router.post("/{case_id}/photo")
async def upload_photo(case_id: int, file: UploadFile = File(...),
                       db: Session = Depends(get_db)):
    """Attach the joint photograph that prints on the photographs sheet."""
    case = _get_case(db, case_id)
    suffix = PHOTO_TYPES.get((file.content_type or "").lower())
    if suffix is None:
        raise HTTPException(400, "Upload a JPEG or PNG image")

    payload = await file.read()
    if len(payload) > MAX_PHOTO_BYTES:
        raise HTTPException(400, "The image is larger than 8 MB")
    if not payload:
        raise HTTPException(400, "The file is empty")

    # Checked now rather than when the photographs sheet is built: a file that
    # is named .png but is not one fails at the moment the form is rendered,
    # where it reads as the form being broken instead of the picture.
    from docx.image.image import Image as _DocxImage
    try:
        _DocxImage.from_blob(payload)
    except Exception as exc:                          # noqa: BLE001
        raise HTTPException(400, "That image could not be read; save it again "
                                 "as a JPEG or PNG and retry") from exc

    from ..render import case_dir
    folder = case_dir(case.case_no) / "photos"
    folder.mkdir(parents=True, exist_ok=True)
    name = f"photo{suffix}"
    for old in folder.glob("photo.*"):        # only one photograph per case
        old.unlink(missing_ok=True)
    (folder / name).write_bytes(payload)

    data = merge_defaults(case.data)
    data["employee"]["photo"] = name
    case.data = data
    case.revision = (case.revision or 1) + 1
    db.commit()
    db.refresh(case)
    return {"photo": name}


@router.delete("/{case_id}/photo", status_code=204)
def delete_photo(case_id: int, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    from ..render import case_dir
    for old in (case_dir(case.case_no) / "photos").glob("photo.*"):
        old.unlink(missing_ok=True)
    data = merge_defaults(case.data)
    data["employee"]["photo"] = ""
    case.data = data
    case.revision = (case.revision or 1) + 1
    db.commit()


@router.get("/{case_id}/photo")
def get_photo(case_id: int, db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    from ..render import case_photo_path
    name = (case.data or {}).get("employee", {}).get("photo", "")
    path = case_photo_path(case.case_no, name)
    if path is None:
        raise HTTPException(404, "No photograph uploaded")
    media = "image/png" if path.suffix == ".png" else "image/jpeg"
    return FileResponse(path, media_type=media,
                        headers={"Cache-Control": "no-store"})


@router.post("/{case_id}/generate", response_model=list[schemas.GeneratedDocOut])
def generate(case_id: int, payload: schemas.GenerateRequest,
             db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    if not (case.data or {}).get("employee", {}).get("name_en"):
        raise HTTPException(400, "Enter the employee's name before generating documents")
    docs = generate_case(db, case, codes=payload.codes, make_pdf=payload.make_pdf,
                         force=payload.force)
    if not payload.codes:                    # a full run brings the case up to date
        case.generated_revision = case.revision
        case.regen_state, case.regen_error = "idle", ""
        db.commit()
    return docs


def _discard_case_bundles(case: Case) -> None:
    from ..generate import _discard_bundles
    _discard_bundles(case)


@router.put("/{case_id}/forms", response_model=schemas.CaseDetail)
def set_form_preferences(case_id: int, payload: schemas.FormPreferences,
                         db: Session = Depends(get_db)):
    """Set this case's form order and which forms it includes.

    These live on the case, not on the generated rows, so they survive a rebuild.
    """
    case = _get_case(db, case_id)
    data = merge_defaults(case.data)
    prefs = dict(data.get("forms") or {})
    for item in payload.forms:
        entry = dict(prefs.get(item.code) or {})
        if item.order is not None:
            entry["order"] = int(item.order)
        if item.included is not None:
            entry["included"] = bool(item.included)
        prefs[item.code] = entry
    data["forms"] = prefs
    case.data = data
    flag_modified(case, "data")
    # The merged files no longer reflect the chosen order or set of forms.
    _discard_case_bundles(case)
    db.commit()
    db.refresh(case)
    return _detail(case, db)


@router.post("/{case_id}/forms/reset", response_model=schemas.CaseDetail)
def reset_form_preferences(case_id: int, db: Session = Depends(get_db)):
    """Put the order and the included forms back to the standard set."""
    case = _get_case(db, case_id)
    data = merge_defaults(case.data)
    data["forms"] = {}
    case.data = data
    flag_modified(case, "data")

    # Documents remember the position they were built at, so put those back to
    # the template order too -- otherwise clearing the preference would leave
    # the old order in place.
    template_order = {t.code: t.order_no
                      for t in db.query(FormTemplate).all()}
    for doc in case.documents:
        doc.order_no = template_order.get(doc.template_code, doc.order_no)

    _discard_case_bundles(case)
    db.commit()
    db.refresh(case)
    return _detail(case, db)


DOCX_TYPE = ("application/vnd.openxmlformats-officedocument"
             ".wordprocessingml.document")


@router.post("/{case_id}/documents/{doc_id}/upload",
             response_model=schemas.GeneratedDocOut)
async def upload_edited_document(case_id: int, doc_id: int,
                                 file: UploadFile = File(...),
                                 db: Session = Depends(get_db),
                                 user: User = Depends(current_user)):
    """Replace one generated form with an edited Word file.

    The document is marked as edited by hand: it is listed in the case notes and
    is skipped by later rebuilds, so an unrelated change to the case cannot wipe
    it out. Resetting it brings the generated version back.
    """
    case = _get_case(db, case_id)
    doc = next((d for d in case.documents if d.id == doc_id), None)
    if doc is None:
        raise HTTPException(404, "Document not found")
    if not (file.filename or "").lower().endswith(".docx"):
        raise HTTPException(400, "Upload a .docx file")

    payload = await file.read()
    if not payload.startswith(b"PK"):
        raise HTTPException(400, "That does not look like a .docx file")

    target = Path(doc.docx_path)
    if not target.name:
        raise HTTPException(400, "This form has not been generated yet")
    target.parent.mkdir(parents=True, exist_ok=True)
    previous = target.read_bytes() if target.exists() else None
    target.write_bytes(payload)

    try:
        from docx import Document as _Docx
        _Docx(str(target))
    except Exception as exc:                          # noqa: BLE001
        if previous is not None:
            target.write_bytes(previous)
        raise HTTPException(400, f"The file could not be read: {exc}") from exc

    from .. import pdf as pdf_engine
    doc.pdf_error = ""
    try:
        produced = pdf_engine.docx_to_pdf(target, target.with_suffix(".pdf"))
        pdf_engine.rotate_landscape_pages(produced)
        doc.pdf_path = str(produced)
    except Exception as exc:                          # noqa: BLE001
        doc.pdf_path, doc.pdf_error = "", str(exc)

    from ..generate import docx_stamp
    doc.built_stamp = docx_stamp(target)
    doc.manual = True
    doc.manual_at = datetime.utcnow()
    doc.manual_by = user.username
    _discard_case_bundles(case)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{case_id}/documents/{doc_id}/open-in-word",
             response_model=schemas.GeneratedDocOut)
def open_in_word(case_id: int, doc_id: int, request: Request,
                 db: Session = Depends(get_db)):
    """Open this form's Word file in the desktop editor on this machine.

    Only for the desktop mode start.bat launches, where the browser and the API
    are the same computer: a server has no screen to open Word on, and opening
    files there on a remote request would be plainly wrong. The clerk edits and
    saves in Word as usual, then presses "pick up my edits", which re-reads the
    same file.
    """
    from ..config import LOCAL_MODE
    from ..auth import LOOPBACK

    client = request.client.host if request.client else ""
    if not LOCAL_MODE or client not in LOOPBACK:
        raise HTTPException(400, "Opening Word is only available on the local desktop")

    case = _get_case(db, case_id)
    doc = next((d for d in case.documents if d.id == doc_id), None)
    if doc is None or not doc.docx_path:
        raise HTTPException(404, "Document not found")
    path = Path(doc.docx_path)
    if not path.exists():
        raise HTTPException(404, "The Word file is missing; generate the case again")

    try:
        import os
        os.startfile(str(path))                       # noqa: S606 - Windows desktop
    except AttributeError:                            # not Windows
        import subprocess
        subprocess.Popen(["xdg-open", str(path)])     # noqa: S603,S607
    except Exception as exc:                          # noqa: BLE001
        raise HTTPException(500, f"Could not open the file: {exc}") from exc
    return doc


@router.post("/{case_id}/documents/{doc_id}/adopt",
             response_model=schemas.GeneratedDocOut)
def adopt_edits(case_id: int, doc_id: int, db: Session = Depends(get_db),
                user: User = Depends(current_user)):
    """Take the Word file as it now stands on disk as this form's document.

    The companion to "open in Word": the clerk edited the file in place, so the
    changes are already there -- this re-makes the PDF from it and records that
    the form was edited by hand.
    """
    case = _get_case(db, case_id)
    doc = next((d for d in case.documents if d.id == doc_id), None)
    if doc is None or not doc.docx_path:
        raise HTTPException(404, "Document not found")
    path = Path(doc.docx_path)
    if not path.exists():
        raise HTTPException(404, "The Word file is missing")

    try:
        from docx import Document as _Docx
        _Docx(str(path))
    except Exception as exc:                          # noqa: BLE001
        raise HTTPException(400, f"The file could not be read: {exc}") from exc

    remake_pdf(doc)

    from ..generate import docx_stamp
    doc.built_stamp = docx_stamp(path)
    doc.manual = True
    doc.manual_at = datetime.utcnow()
    doc.manual_by = user.username
    _discard_case_bundles(case)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{case_id}/documents/{doc_id}/content")
def document_content(case_id: int, doc_id: int, db: Session = Depends(get_db)):
    """The words of this form, in printed order, ready to be edited in place."""
    from ..docx_text import read_blocks

    case = _get_case(db, case_id)
    doc = next((d for d in case.documents if d.id == doc_id), None)
    if doc is None or not doc.docx_path:
        raise HTTPException(404, "Document not found")
    path = Path(doc.docx_path)
    if not path.exists():
        raise HTTPException(404, "The Word file is missing; generate the case again")
    try:
        return read_blocks(path)
    except Exception as exc:                          # noqa: BLE001
        raise HTTPException(500, f"The document could not be read: {exc}") from exc


@router.put("/{case_id}/documents/{doc_id}/content",
            response_model=schemas.GeneratedDocOut)
def save_document_content(case_id: int, doc_id: int, payload: schemas.DocumentEdits,
                          db: Session = Depends(get_db),
                          user: User = Depends(current_user)):
    """Save wording changed in the app back into this form's Word file.

    Only the text inside runs is rewritten, so the sheet keeps its layout to the
    millimetre. As with a file edited in Word, the form is then marked as edited
    by hand and left alone by later rebuilds until it is reset.
    """
    from ..docx_text import apply_edits

    case = _get_case(db, case_id)
    doc = next((d for d in case.documents if d.id == doc_id), None)
    if doc is None or not doc.docx_path:
        raise HTTPException(404, "Document not found")
    path = Path(doc.docx_path)
    if not path.exists():
        raise HTTPException(404, "The Word file is missing; generate the case again")

    edits = {item.id: item.text for item in payload.edits}
    if not edits:
        return doc
    try:
        changed = apply_edits(path, edits)
    except KeyError as exc:
        raise HTTPException(409, str(exc.args[0])) from exc
    except Exception as exc:                          # noqa: BLE001
        raise HTTPException(500, f"The document could not be saved: {exc}") from exc
    if not changed:
        return doc

    remake_pdf(doc)
    from ..generate import docx_stamp
    doc.built_stamp = docx_stamp(path)
    doc.manual = True
    doc.manual_at = datetime.utcnow()
    doc.manual_by = user.username
    _discard_case_bundles(case)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{case_id}/documents/{doc_id}/reset",
             response_model=schemas.GeneratedDocOut)
def reset_document(case_id: int, doc_id: int, db: Session = Depends(get_db)):
    """Throw away an uploaded file and rebuild this form from the template."""
    case = _get_case(db, case_id)
    doc = next((d for d in case.documents if d.id == doc_id), None)
    if doc is None:
        raise HTTPException(404, "Document not found")
    code = doc.template_code
    generate_case(db, case, codes=[code], make_pdf=True, force=True)
    db.refresh(case)
    fresh = next((d for d in case.documents if d.template_code == code), None)
    if fresh is None:
        raise HTTPException(500, "The form could not be rebuilt")
    return fresh


@router.get("/{case_id}/documents/tick")
def documents_state(case_id: int, db: Session = Depends(get_db)):
    """One short value that changes whenever this case's documents do.

    The Documents tab watches this rather than re-reading the whole list, so a
    save in Word can be looked for every second or so without sending every
    form's row back each time.

    It also takes in any Word edit it finds, which makes it a complete stand-in
    for the directory watcher on a machine where that could not start.
    """
    case = _get_case(db, case_id)
    picked = pick_up_word_edits(db, case)
    return {"tick": documents_tick(case),
            "picked": [{"id": d.id, "title_en": d.title_en,
                        "template_code": d.template_code} for d in picked]}


@router.get("/{case_id}/documents", response_model=list[schemas.GeneratedDocOut])
def list_documents(case_id: int, db: Session = Depends(get_db)):
    """Documents in this case's print order, each carrying its included flag.

    Forms edited in Word are taken in on the way past: the tab re-reads this
    list when the window is focused and while a form is open in Word, so a save
    over there shows up here on its own.
    """
    case = _get_case(db, case_id)
    pick_up_word_edits(db, case)
    from ..generate import _ordered_docs
    prefs = form_prefs(case)
    out = []
    for doc in _ordered_docs(case):
        item = schemas.GeneratedDocOut.model_validate(doc)
        item.included = (prefs.get(doc.template_code) or {}).get("included", True)
        out.append(item)
    return out


@router.get("/{case_id}/documents/{doc_id}/download")
def download_document(case_id: int, doc_id: int,
                      fmt: str = Query("pdf", pattern="^(pdf|docx)$"),
                      inline: bool = False,
                      db: Session = Depends(get_db)):
    case = _get_case(db, case_id)
    doc = next((d for d in case.documents if d.id == doc_id), None)
    if doc is None:
        raise HTTPException(404, "Document not found")
    path = Path(doc.pdf_path if fmt == "pdf" else doc.docx_path)
    if not path or not path.exists():
        raise HTTPException(404, f"{fmt.upper()} not available for this document")
    disposition = "inline" if (inline and fmt == "pdf") else "attachment"
    return FileResponse(
        path, media_type=MEDIA_TYPES[fmt],
        headers={"Content-Disposition": f'{disposition}; filename="{path.name}"',
                 # The URL never changes, so without this the browser is free to
                 # invent a freshness window and keep showing the copy it already
                 # has -- an edit is saved, the PDF is rebuilt, and the preview
                 # still shows the old sheet. "no-cache" still allows the ETag
                 # revalidation below, so an unchanged file costs one 304.
                 "Cache-Control": "no-cache, must-revalidate"},
    )


@router.get("/{case_id}/bundle")
def download_bundle(case_id: int,
                    kind: str = Query("pdf", pattern="^(pdf|docx|zip)$"),
                    inline: bool = False,
                    db: Session = Depends(get_db)):
    """The complete case: one PDF, one Word document, or a ZIP of everything."""
    case = _get_case(db, case_id)
    if not case.documents:
        raise HTTPException(400, "Generate the documents first")
    try:
        path = case_bundle(case, kind)
    except Exception as exc:                            # noqa: BLE001
        raise HTTPException(500, f"Could not build the complete file: {exc}") from exc
    if not path.exists():
        raise HTTPException(500, "Could not build the complete file")
    disposition = "inline" if (inline and kind == "pdf") else "attachment"
    return FileResponse(
        path, media_type=MEDIA_TYPES[kind],
        headers={"Content-Disposition": f'{disposition}; filename="{path.name}"',
                 "Cache-Control": "no-cache, must-revalidate"},
    )


@router.get("/{case_id}/preview/{template_code}")
def preview_context(case_id: int, template_code: str, db: Session = Depends(get_db)):
    """The resolved values a template will receive -- useful when a form looks wrong."""
    case = _get_case(db, case_id)
    template = db.query(FormTemplate).filter_by(code=template_code).one_or_none()
    if template is None:
        raise HTTPException(404, "Template not found")
    from ..render import jinja_env, resolve_blocks
    ctx = build_context(case.data, blocks={})
    ctx["t"] = resolve_blocks({b.key: b.value for b in template.blocks}, ctx, jinja_env())
    ctx.pop("raw", None)
    return ctx

