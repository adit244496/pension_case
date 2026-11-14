"""Generate a whole case: every enabled form to .docx, then one batched PDF pass."""
from __future__ import annotations

import threading
from pathlib import Path

from sqlalchemy.orm import Session

from . import pdf as pdf_engine
from . import render
from .compose import merge_docx
from .models import Case, FormTemplate, GeneratedDoc

# Cases with a rebuild in flight. Between rendering the .docx files and the
# batched PDF pass every .docx on disk is newer than the .pdf beside it, and the
# new rows are not committed yet, so a reader in another thread would see files
# that look hand-edited. Nothing may adopt a form while its case is in here.
_GENERATING: set[int] = set()
_GENERATING_LOCK = threading.Lock()


def is_generating(case_id: int) -> bool:
    with _GENERATING_LOCK:
        return case_id in _GENERATING


def docx_stamp(path) -> str:
    """Size and mtime of a .docx, as a value that changes whenever it is saved."""
    try:
        st = Path(path).stat()
    except OSError:
        return ""
    return f"{st.st_size}:{st.st_mtime_ns}"


COMPLETE_DOCX_SUFFIX = "_complete.docx"
COMPLETE_PDF_SUFFIX = "_complete.pdf"
ZIP_SUFFIX = "_all_documents.zip"


def form_prefs(case: Case) -> dict:
    """Per-case overrides of a form's position and whether it is included."""
    return dict((case.data or {}).get("forms") or {})


def form_order(case: Case, template_or_code, fallback: int = 0) -> int:
    """Where this form sits in this case, falling back to the template order."""
    code = getattr(template_or_code, "code", template_or_code)
    pref = form_prefs(case).get(code) or {}
    order = pref.get("order")
    return int(order) if isinstance(order, (int, float)) else fallback


def form_included(case: Case, template: FormTemplate) -> bool:
    """Whether this case uses the form. Defaults to the template's own setting."""
    pref = form_prefs(case).get(template.code) or {}
    value = pref.get("included")
    return bool(template.enabled) if value is None else bool(value)


def case_templates(db: Session, case: Case, codes: list[str] | None = None
                   ) -> list[FormTemplate]:
    """The forms this case is made of, in this case's order."""
    everything = [t for t in db.query(FormTemplate).all() if not t.archived]
    chosen = [t for t in everything
              if (t.code in codes if codes else form_included(case, t))]
    return sorted(chosen, key=lambda t: (form_order(case, t, t.order_no), t.order_no))


def selected_templates(db: Session, codes: list[str] | None) -> list[FormTemplate]:
    query = db.query(FormTemplate).order_by(FormTemplate.order_no)
    return [t for t in query.all()
            if not t.archived and (t.code in codes if codes else t.enabled)]


def generate_case(db: Session, case: Case, *, codes: list[str] | None = None,
                  make_pdf: bool = True, force: bool = False) -> list[GeneratedDoc]:
    """Render this case's forms, in this case's order.

    A document the operator replaced with their own edited file is left alone
    unless ``force`` is set, so a rebuild triggered by an unrelated edit cannot
    quietly throw that work away.
    """
    with _GENERATING_LOCK:
        _GENERATING.add(case.id)
    try:
        return _generate_case(db, case, codes=codes, make_pdf=make_pdf, force=force)
    finally:
        with _GENERATING_LOCK:
            _GENERATING.discard(case.id)


def _generate_case(db: Session, case: Case, *, codes: list[str] | None = None,
                   make_pdf: bool = True, force: bool = False) -> list[GeneratedDoc]:
    templates = case_templates(db, case, codes)

    kept: list[GeneratedDoc] = []
    protected = set()
    if not force:
        protected = {d.template_code for d in case.documents if d.manual}
        if protected:
            templates = [t for t in templates if t.code not in protected]
            kept = [d for d in case.documents if d.template_code in protected]

    # Replace only the documents we are re-generating; drop those for forms the
    # case no longer includes.
    wanted = {t.code for t in templates} | protected
    regenerating = {t.code for t in templates}
    for doc in list(case.documents):
        if doc.template_code in regenerating or (codes is None
                                                 and doc.template_code not in wanted):
            db.delete(doc)
    db.flush()

    produced: list[GeneratedDoc] = []
    pdf_jobs: list[tuple[Path, Path]] = []

    for template in templates:
        blocks = {b.key: b.value for b in template.blocks}
        doc = GeneratedDoc(case_id=case.id, template_code=template.code,
                           title_en=template.title_en,
                           order_no=form_order(case, template, template.order_no))
        try:
            result = render.render_form(case, template, blocks, make_pdf=False)
            doc.docx_path = result["docx_path"]
            # Recorded as the file is written, so the rebuild is never mistaken
            # later for somebody having edited the form in Word.
            doc.built_stamp = docx_stamp(result["docx_path"])
            if make_pdf:
                pdf_path = Path(result["docx_path"]).with_suffix(".pdf")
                pdf_jobs.append((Path(result["docx_path"]), pdf_path))
                doc.pdf_path = str(pdf_path)
        except Exception as exc:                       # noqa: BLE001 - shown in the UI
            doc.pdf_error = f"render failed: {exc}"
        db.add(doc)
        produced.append(doc)

    # Commit the rendered forms before converting anything.
    #
    # Word takes a second or two a sheet, so a whole case runs to half a minute.
    # SQLite locks the database for the length of a write transaction, so holding
    # this one open across the conversion made every other write in that window
    # fail -- a photograph uploaded, a field saved -- after the five second busy
    # timeout, with the clerk told only "Internal Server Error".
    case.status = "generated"
    db.commit()

    if pdf_jobs:
        errors = pdf_engine.docx_to_pdf_batch(pdf_jobs)
        for doc in produced:
            if not doc.docx_path:
                continue
            error = errors.get(str(Path(doc.docx_path).resolve()), "")
            if error:
                doc.pdf_error, doc.pdf_path = error, ""
            elif doc.pdf_path:
                # The two wide sheets are turned so the whole case is one page size.
                pdf_engine.rotate_landscape_pages(Path(doc.pdf_path))
        db.commit()

    for doc in produced:
        db.refresh(doc)
    produced.extend(kept)

    _discard_stale_files(case)
    _discard_bundles(case)             # bundles are rebuilt on the next download
    return produced


def _remove_if_possible(path: Path) -> None:
    """Delete a leftover file, and shrug if Windows will not let go of it.

    Word keeps a converted document open for a moment after it is done with it,
    and an instance that failed to quit can hold one indefinitely. Either way
    this is housekeeping: a file that cannot be removed now is removed by the
    next rebuild, and it must never turn a case that generated perfectly well
    into an "Internal Server Error".
    """
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def _discard_stale_files(case: Case) -> None:
    """Remove documents left over from forms that are no longer part of the case."""
    out_dir = render.case_dir(case.case_no)
    keep = set()
    for doc in case.documents:
        for value in (doc.docx_path, doc.pdf_path):
            if value:
                keep.add(Path(value).name)
    for path in out_dir.glob("[0-9][0-9]_*"):
        if path.name not in keep:
            _remove_if_possible(path)


def _discard_bundles(case: Case) -> None:
    out_dir = render.case_dir(case.case_no)
    for suffix in (COMPLETE_DOCX_SUFFIX, COMPLETE_PDF_SUFFIX, ZIP_SUFFIX):
        _remove_if_possible(out_dir / f"{case.case_no}{suffix}")


def _ordered_docs(case: Case, only_included: bool = False) -> list[GeneratedDoc]:
    """Documents in this case's print order.

    ``only_included`` drops the forms the operator unticked, which is how a case
    leaves a form out of the complete file without deleting its documents.
    """
    prefs = form_prefs(case)
    docs = list(case.documents)
    if only_included:
        docs = [d for d in docs
                if (prefs.get(d.template_code) or {}).get("included", True)]
    return sorted(docs, key=lambda d: (form_order(case, d.template_code, d.order_no),
                                       d.order_no, d.template_code))


def complete_docx(case: Case, *, rebuild: bool = False) -> Path:
    """The whole case as one Word document, in form order.

    Each form keeps its own page setup, so the landscape sheets stay landscape --
    this is the file the office prints and files, matching the reference case.
    """
    out_dir = render.case_dir(case.case_no)
    target = out_dir / f"{case.case_no}{COMPLETE_DOCX_SUFFIX}"
    if target.exists() and not rebuild:
        return target
    sources = [Path(d.docx_path) for d in _ordered_docs(case, only_included=True)
               if d.docx_path and Path(d.docx_path).exists()]
    if not sources:
        raise ValueError("no documents have been generated for this case")
    return merge_docx(sources, target)


def complete_pdf(case: Case, *, rebuild: bool = False) -> Path:
    """The whole case as one PDF, converted from the complete Word document.

    Converting the merged document (rather than stitching the individual PDFs)
    guarantees the Word and PDF outputs are the same document.
    """
    out_dir = render.case_dir(case.case_no)
    target = out_dir / f"{case.case_no}{COMPLETE_PDF_SUFFIX}"
    if target.exists() and not rebuild:
        return target
    source = complete_docx(case, rebuild=rebuild)
    try:
        result = pdf_engine.docx_to_pdf(source, target)
        pdf_engine.rotate_landscape_pages(result)
        return result
    except pdf_engine.PdfConversionError:
        # Fall back to stitching the per-form PDFs that were produced earlier.
        parts = [Path(d.pdf_path) for d in _ordered_docs(case, only_included=True)
                 if d.pdf_path and Path(d.pdf_path).exists()]
        if not parts:
            raise
        merged = pdf_engine.merge_pdfs(parts, target)
        pdf_engine.rotate_landscape_pages(merged)
        return merged


def case_bundle(case: Case, kind: str = "pdf") -> Path:
    """kind: 'pdf' and 'docx' give the complete case as one file; 'zip' gives everything."""
    if kind == "docx":
        return complete_docx(case)
    if kind == "pdf":
        return complete_pdf(case)

    out_dir = render.case_dir(case.case_no)
    paths: list[Path] = []
    for doc in _ordered_docs(case):
        for value in (doc.docx_path, doc.pdf_path):
            if value and Path(value).exists():
                paths.append(Path(value))
    for builder in (complete_docx, complete_pdf):
        try:
            paths.append(builder(case))
        except Exception:                              # noqa: BLE001 - zip is best-effort
            pass
    return render.build_zip(paths, out_dir / f"{case.case_no}{ZIP_SUFFIX}",
                            arc_prefix=case.case_no)


def regenerate_in_background(case_id: int) -> None:
    """Rebuild every form for a case after its details were edited.

    Runs on its own database session because the request that scheduled it has
    already returned. Word conversion is serialised behind a lock, so two saves
    in quick succession queue rather than collide.
    """
    from .db import SessionLocal

    db = SessionLocal()
    try:
        case = db.get(Case, case_id)
        if case is None:
            return
        revision = case.revision
        case.regen_state = "running"
        case.regen_error = ""
        db.commit()
        try:
            generate_case(db, case)
            case = db.get(Case, case_id)
            # Only mark clean if nothing was saved while we were working.
            case.generated_revision = revision
            case.regen_state = "idle"
        except Exception as exc:                       # noqa: BLE001 - shown in the UI
            case = db.get(Case, case_id)
            case.regen_state = "error"
            case.regen_error = str(exc)[:500]
        db.commit()
    finally:
        db.close()
