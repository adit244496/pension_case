"""Keeping the app in step with forms the clerk edits in Word.

A form is a .docx on disk. The clerk opens it -- from this app, from Explorer,
from Word's recent files -- edits it and presses Ctrl+S. That save is the whole
signal: there is nothing to press in the app afterwards, and nothing to upload.

Two things watch for it. A directory watcher reacts to the save itself, so the
PDF is already being rebuilt while Word is still writing its status bar; and the
documents list re-checks on the way past, which covers a machine where the
watcher could not start and the moments when it was not running.

Both end up in :func:`pick_up_word_edits`, which is safe to call as often as
anyone likes: with nothing changed it costs one stat() per form.
"""
from __future__ import annotations

import re
import threading
import zlib
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from .config import STORAGE_DIR
from .models import Case


def remake_pdf(doc) -> None:
    """Re-convert a document's PDF after its Word file changed on disk."""
    from . import pdf as pdf_engine

    doc.pdf_error = ""
    try:
        produced = pdf_engine.docx_to_pdf(Path(doc.docx_path),
                                          Path(doc.docx_path).with_suffix(".pdf"))
        pdf_engine.rotate_landscape_pages(produced)
        doc.pdf_path = str(produced)
    except Exception as exc:                          # noqa: BLE001
        doc.pdf_path, doc.pdf_error = "", str(exc)


# One pass per case at a time. The watcher and the browser both come through
# here, and a save can reach them within milliseconds of each other; without
# this they would each convert the same sheet, and the second would be doing it
# while Word still had the file.
_case_locks: dict[int, threading.Lock] = {}
_case_locks_guard = threading.Lock()


def _case_lock(case_id: int) -> threading.Lock:
    with _case_locks_guard:
        return _case_locks.setdefault(case_id, threading.Lock())


def pick_up_word_edits(db: Session, case: Case) -> list:
    """Adopt every form whose Word file has changed on disk since we wrote it.

    Each .docx carries the size and mtime it had when this system last wrote it;
    anything else on disk was written by something else.

    Deliberately not "is the .docx newer than its .pdf": a rebuild renders every
    .docx first and converts them in one batch afterwards, so mid-rebuild the
    whole case looks hand-edited. Marking forms manual there would be quietly
    destructive -- a manual form is skipped by later rebuilds, so it would stop
    following the case data with nothing on screen to say why.

    Returns the documents that were picked up, for the caller to report.
    """
    from .generate import is_generating

    # A rebuild in flight is writing these very files, and its rows are not
    # committed yet, so nothing here can be judged until it finishes.
    if is_generating(case.id) or (case.regen_state or "") == "running":
        return []

    lock = _case_lock(case.id)
    if not lock.acquire(blocking=False):
        # Another caller is already looking at this case. Theirs will find the
        # same save, so there is nothing to wait for -- and waiting here would
        # hold a request open for the length of a conversion.
        return []
    try:
        return _pick_up(db, case)
    finally:
        lock.release()


def _pick_up(db: Session, case: Case) -> list:
    from docx import Document as _Docx
    from .generate import _discard_bundles, docx_stamp

    picked = []
    for doc in case.documents:
        if not doc.docx_path or not doc.pdf_path:
            continue                      # never auto-adopt a form with no PDF
        stamp = docx_stamp(doc.docx_path)
        if not stamp:
            continue                      # the file is gone; nothing to adopt
        if not doc.built_stamp:
            # Written before this system started stamping. Record where it
            # stands now so the next real save is seen, but do not claim this
            # one was edited -- there is nothing to compare it against.
            doc.built_stamp = stamp
            db.commit()
            continue
        if stamp == doc.built_stamp:
            continue

        # Word saves by writing a new file and renaming it over the old one, so
        # a poll can land mid-rename. A file that will not open is not corrupt,
        # only unfinished -- the next poll takes it.
        try:
            _Docx(str(doc.docx_path))
        except Exception:                                 # noqa: BLE001
            continue

        was = doc.pdf_path
        remake_pdf(doc)
        if doc.pdf_error:
            # Word is busy with the document this instant. Keep pointing at the
            # last good sheet rather than blanking the form, and try again next
            # time round -- built_stamp is left alone, so it stays pending.
            doc.pdf_path = was
            continue

        # The stamp read before the conversion, deliberately: if Word saved
        # again while we were converting, this one no longer matches the file
        # and the next pass picks that save up too.
        doc.built_stamp = stamp
        doc.manual = True
        doc.manual_at = datetime.utcnow()
        doc.manual_by = "Word"
        _discard_bundles(case)
        picked.append(doc)

    if picked:
        db.commit()
        for doc in picked:
            db.refresh(doc)
    return picked


def documents_tick(case: Case) -> str:
    """A short value that changes whenever this case's documents do.

    The Documents tab asks for this rather than the whole list, so watching for
    a save in Word costs one small reply a second instead of every form's row.
    """
    parts = []
    for doc in sorted(case.documents, key=lambda d: d.id):
        when = doc.manual_at.isoformat() if doc.manual_at else ""
        parts.append(f"{doc.id}:{when}:{doc.built_stamp or ''}:"
                     f"{1 if doc.pdf_path else 0}:{doc.pdf_error or ''}")
    # crc32 rather than hash(): Python salts hash() per process, which would
    # make every restart look to the browser like the documents had changed.
    return format(zlib.crc32("|".join(parts).encode("utf-8")), "08x")


# --------------------------------------------------------------------------
# the directory watcher
# --------------------------------------------------------------------------
_stop = threading.Event()
_thread: threading.Thread | None = None
# watchfiles reports resolved paths, so compare against a resolved root.
_ROOT = STORAGE_DIR.resolve()


def _case_for_folder(db: Session, folder: str) -> Case | None:
    """Find the case whose storage folder this is.

    The folder is the case number with anything awkward replaced, so it is
    matched by running case numbers through the same function rather than by
    trying to reverse it. Only the two columns needed to match are read; the
    case itself is loaded once there is a hit.
    """
    from .render import case_dir

    for case_id, case_no in db.query(Case.id, Case.case_no).all():
        if case_dir(case_no).name == folder:
            return db.get(Case, case_id)
    return None


# The forms themselves are "01_cover_sheet.docx" and so on. Anything else in a
# case folder -- Word's "~$" lock file, the complete-case bundle, the ZIP -- is
# not a form and must not set this off.
FORM_FILE = re.compile(r"^\d{2}_.+\.docx$", re.IGNORECASE)


def _interesting(path: Path) -> bool:
    return bool(FORM_FILE.match(path.name))


def _handle(folders: set[str]) -> None:
    from .db import SessionLocal

    db = SessionLocal()
    try:
        for folder in folders:
            case = _case_for_folder(db, folder)
            if case is None:
                continue
            try:
                pick_up_word_edits(db, case)
            except Exception:                          # noqa: BLE001 - keep watching
                db.rollback()
    finally:
        db.close()


def _watch() -> None:
    try:
        _watch_forever()
    except Exception as exc:                           # noqa: BLE001
        # The documents list still picks edits up, so say so and stand down
        # rather than taking anything else with us.
        print(f"Word watcher stopped: {exc}")


def _watch_forever() -> None:
    from watchfiles import watch

    # debounce groups the burst Word makes of a single save -- it writes a new
    # file, deletes the old one and renames -- into one wake-up, by which time
    # the document on disk is the finished one.
    for changes in watch(str(_ROOT), stop_event=_stop, debounce=700, step=50,
                         yield_on_timeout=False, raise_interrupt=False):
        folders = set()
        for _kind, raw in changes:
            path = Path(raw)
            # One level down from the storage root: a case folder, not the
            # preview scratch folder or a case's photos.
            if _interesting(path) and path.parent.parent == _ROOT:
                folders.add(path.parent.name)
        if folders:
            _handle(folders)


def start_watcher() -> bool:
    """Begin watching the storage folder. Returns whether it started.

    Never fatal: a machine where the watcher cannot run (an unusual filesystem,
    a shared drive that reports no events) still picks edits up through the
    documents list, only a second or two later.
    """
    global _thread
    if _thread is not None and _thread.is_alive():
        return True
    try:
        import watchfiles                              # noqa: F401
    except ImportError:
        return False
    _stop.clear()
    _thread = threading.Thread(target=_watch, daemon=True, name="word-watch")
    _thread.start()
    return True


def stop_watcher() -> None:
    _stop.set()
