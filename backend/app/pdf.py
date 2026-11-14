"""DOCX -> PDF conversion.

Primary path is Microsoft Word over COM, which produces a PDF identical to what
the office would get from "Save as PDF" -- important because these forms have
hand-tuned table layouts and Devanagari text.  If Word is not available (e.g.
the app is later moved to a Linux server) it falls back to LibreOffice headless.

Starting Word is what this costs, not converting: a cold launch measured at
about six seconds against roughly half a second for the sheet itself.  Every
save in Word used to pay that again, which is most of the wait between the
clerk pressing Ctrl+S and the new page appearing in the app.

So one Word instance is kept alive between conversions.  COM objects belong to
the thread that created them, so that instance lives on a single worker thread
and every conversion is handed to it -- which also gives the serialisation
Word's automation interface needs anyway.  The instance is dropped after a spell
with nothing to do, and after enough documents that a long session does not let
Word grow unbounded, so an idle machine is left as it was found.
"""
from __future__ import annotations

import atexit
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

WD_FORMAT_PDF = 17

# Quit Word once it has been idle this long. Long enough that a clerk working
# through a case never waits for a launch, short enough that a machine left
# alone is not sitting on a Word process.
IDLE_SECONDS = float(os.environ.get("PENSION_WORD_IDLE", "300"))

# Replace the instance after this many documents. Word is not built to stay up
# for days; recycling costs one launch and rules out a slow leak.
RECYCLE_AFTER = int(os.environ.get("PENSION_WORD_RECYCLE", "400"))

# Set PENSION_WORD_KEEPALIVE=0 to go back to a fresh Word per conversion.
KEEP_WORD_ALIVE = os.environ.get("PENSION_WORD_KEEPALIVE", "1").strip().lower() \
    not in ("0", "false", "no")


class PdfConversionError(RuntimeError):
    pass


def _find_libreoffice() -> str | None:
    for candidate in ("soffice", "libreoffice",
                      r"C:\Program Files\LibreOffice\program\soffice.exe",
                      r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        found = shutil.which(candidate) if os.sep not in candidate else (
            candidate if Path(candidate).exists() else None)
        if found:
            return found
    return None


# Which converters this machine has does not change while the app runs, and
# health is polled by the sign-in page, so the answers are worked out once.
_BACKEND_LOCK = threading.Lock()
_word_available: bool | None = None
_libreoffice_path: str | None | object = None
_UNKNOWN = object()
_libreoffice_path = _UNKNOWN


def word_available() -> bool:
    global _word_available
    with _BACKEND_LOCK:
        if _word_available is None:
            _word_available = _probe_word()
        return _word_available


def _probe_word() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        return False
    try:
        import winreg
        winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "Word.Application")
        return True
    except OSError:
        return False


def libreoffice_path() -> str | None:
    global _libreoffice_path
    with _BACKEND_LOCK:
        if _libreoffice_path is _UNKNOWN:
            _libreoffice_path = _find_libreoffice()
        return _libreoffice_path


def backend_name() -> str:
    if word_available():
        return "msword"
    if libreoffice_path():
        return "libreoffice"
    return "none"


# --------------------------------------------------------------------------
# the Word instance
# --------------------------------------------------------------------------
class _WordWorker:
    """Runs work against one long-lived Word instance, on one thread.

    Callers hand in a function taking the Word application; it runs on the
    worker thread and its result -- or its exception -- comes back here. The
    instance behind it is started on demand, checked before each use, and let go
    when it has been idle or has done enough documents.
    """

    def __init__(self) -> None:
        self._jobs: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._thread: threading.Thread | None = None
        # Touched only on the worker thread.
        self._word = None
        self._converted = 0
        self._leash = None

    # -- caller side ------------------------------------------------------
    def run(self, work, timeout: float = 900.0):
        done = threading.Event()
        box: dict = {}
        with self._lock:
            # Queued and started under the same lock as the worker's decision to
            # stop, so a job can never be left in the queue with nobody serving.
            self._jobs.put((work, box, done))
            if self._thread is None:
                self._thread = threading.Thread(target=self._serve, daemon=True,
                                                name="word-com")
                self._thread.start()
        if not done.wait(timeout):
            raise PdfConversionError("Word did not answer in time")
        if "error" in box:
            raise box["error"]
        return box.get("value")

    def reset(self) -> None:
        """Throw the current instance away; the next job starts a fresh one."""
        with self._lock:
            if self._thread is None:
                return                     # nothing running, nothing to drop
        try:
            self.run(_DROP, timeout=60.0)
        except Exception:                              # noqa: BLE001 - best effort
            pass

    def close(self) -> None:
        with self._lock:
            if self._thread is None:
                return
            done = threading.Event()
            self._jobs.put((_STOP, {}, done))
        done.wait(30.0)

    # -- worker side ------------------------------------------------------
    def _serve(self) -> None:
        import pythoncom

        pythoncom.CoInitialize()
        try:
            while True:
                try:
                    work, box, done = self._jobs.get(timeout=IDLE_SECONDS)
                except queue.Empty:
                    with self._lock:
                        if self._jobs.empty():
                            self._thread = None
                            return
                    continue
                if work is _STOP:
                    with self._lock:
                        self._thread = None
                    # Quit before answering: at shutdown the caller's return is
                    # the last thing between here and the process exiting, and
                    # an unquit Word would be left with no window to close it.
                    self._release()
                    done.set()
                    return
                try:
                    if work is _DROP:
                        self._release()
                    else:
                        box["value"] = work(self._application())
                        self._converted += 1
                        if self._converted >= RECYCLE_AFTER:
                            self._release()
                except Exception as exc:               # noqa: BLE001 - reported to the caller
                    box["error"] = exc
                finally:
                    done.set()
        finally:
            self._release()
            pythoncom.CoUninitialize()
            with self._lock:
                if self._thread is threading.current_thread():
                    self._thread = None

    def _application(self):
        import win32com.client

        if self._word is not None:
            try:
                self._word.Version            # cheap call; raises if it has gone
            except Exception:                 # noqa: BLE001
                self._release()               # also lets go of its job handle
        if self._word is None:
            word = win32com.client.DispatchEx("Word.Application")
            word.Visible = False
            word.DisplayAlerts = 0
            self._word = word
            self._converted = 0
            self._leash = _leash_to_this_process(word)
        return self._word

    def _release(self) -> None:
        word, self._word = self._word, None
        leash, self._leash = self._leash, None
        self._converted = 0
        if word is not None:
            try:
                word.Quit(SaveChanges=0)
            except Exception:                          # noqa: BLE001
                pass
        if leash is not None:
            # Closing the job ends anything still in it, so a Word that ignored
            # Quit does not survive as an invisible process.
            try:
                leash.Close()
            except Exception:                          # noqa: BLE001
                pass


def _word_process_id(word) -> int | None:
    """The process id of a Word instance, via the window of a document in it.

    Word offers no other way to say which process answered, and there is no safe
    way to guess: picking the newest WINWORD on the machine could just as easily
    find the one the clerk opened their own letter in.
    """
    import win32process

    document = None
    try:
        document = word.Documents.Add()
        hwnd = document.ActiveWindow.Hwnd
        return win32process.GetWindowThreadProcessId(hwnd)[1]
    except Exception:                                  # noqa: BLE001
        return None
    finally:
        try:
            if document is not None:
                document.Close(False)
        except Exception:                              # noqa: BLE001
            pass


def _leash_to_this_process(word):
    """Ask Windows to close this Word whenever this process goes.

    The instance is kept alive between conversions, so it is no longer the case
    that it dies with the conversion that started it. Quitting it at shutdown
    covers Ctrl+C and a normal stop, but not stop.bat, which ends the app with
    Stop-Process -Force, nor the console window simply being closed -- and each
    of those would otherwise leave an invisible WINWORD.EXE holding a hundred
    megabytes until the machine was restarted.

    A job object with KILL_ON_JOB_CLOSE puts that in the operating system's
    hands: the handle is released however this process dies, and Word goes with
    it. Returns the handle to hold open, or None where this cannot be arranged --
    in which case the shutdown path is still there, it is just the only one.
    """
    try:
        import win32api
        import win32con
        import win32job
    except ImportError:
        return None

    pid = _word_process_id(word)
    if not pid:
        return None
    try:
        job = win32job.CreateJobObject(None, "")
        limits = win32job.QueryInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation)
        limits["BasicLimitInformation"]["LimitFlags"] |= \
            win32job.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        win32job.SetInformationJobObject(
            job, win32job.JobObjectExtendedLimitInformation, limits)
        handle = win32api.OpenProcess(
            win32con.PROCESS_SET_QUOTA | win32con.PROCESS_TERMINATE, False, pid)
        win32job.AssignProcessToJobObject(job, handle)
        return job
    except Exception:                                  # noqa: BLE001 - best effort
        return None


_STOP = object()
_DROP = object()
_WORKER = _WordWorker()
# A Word left running after the app closes is invisible and has no window to
# close, so it would sit in Task Manager until the machine is restarted.
atexit.register(_WORKER.close)


def shutdown() -> None:
    """Let go of the Word instance. Called when the app stops."""
    _WORKER.close()


def _export(word, src: Path, dst: Path) -> None:
    """Open one document on the Word instance and write it out as PDF."""
    doc = None
    try:
        doc = word.Documents.Open(str(src), ReadOnly=True,
                                  AddToRecentFiles=False, Visible=False)
        doc.SaveAs(str(dst), FileFormat=WD_FORMAT_PDF)
    finally:
        try:
            if doc is not None:
                doc.Close(False)
        except Exception:                              # noqa: BLE001
            pass


def _prepare(src, dst) -> tuple[Path, Path]:
    # Word's COM interface resolves paths against its own working directory,
    # so both sides must be absolute.
    src, dst = Path(src).resolve(), Path(dst).resolve()
    if not src.exists():
        raise PdfConversionError(f"source not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()
    return src, dst


def _convert_with_word(docx_path: Path, pdf_path: Path) -> None:
    """Convert on the shared instance, retrying once on a fresh one.

    A Word that has been sitting open can be left in a state where the next
    document will not open -- a modal it raised to itself, or an instance an
    installer restarted underneath us. One retry against a new instance turns
    that from a failed conversion into a slow one.
    """
    try:
        _WORKER.run(lambda word: _export(word, docx_path, pdf_path))
    except Exception:                                  # noqa: BLE001
        _WORKER.reset()
        _WORKER.run(lambda word: _export(word, docx_path, pdf_path))
    finally:
        if not KEEP_WORD_ALIVE:
            _WORKER.reset()


def _convert_with_libreoffice(docx_path: Path, pdf_path: Path) -> None:
    """Convert with headless LibreOffice.

    Each run gets its own user profile directory: LibreOffice refuses to start a
    second instance against a profile that is already in use, which otherwise
    makes concurrent conversions fail intermittently on a server.
    """
    soffice = libreoffice_path()
    if not soffice:
        raise PdfConversionError("LibreOffice not found")

    with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile:
        profile_url = Path(profile).as_uri()
        try:
            result = subprocess.run(
                [soffice, f"-env:UserInstallation={profile_url}",
                 "--headless", "--nologo", "--nofirststartwizard", "--norestore",
                 "--convert-to", "pdf:writer_pdf_Export",
                 "--outdir", str(pdf_path.parent), str(docx_path)],
                capture_output=True, text=True, timeout=300,
            )
        except subprocess.TimeoutExpired as exc:
            raise PdfConversionError("LibreOffice timed out") from exc

    produced = pdf_path.parent / (docx_path.stem + ".pdf")
    if not produced.exists():
        raise PdfConversionError(result.stderr or result.stdout or "conversion failed")
    if produced != pdf_path:
        produced.replace(pdf_path)


def docx_to_pdf(docx_path: Path, pdf_path: Path) -> Path:
    """Convert and return the PDF path, raising PdfConversionError on failure."""
    docx_path, pdf_path = _prepare(docx_path, pdf_path)

    errors = []
    if word_available():
        try:
            _convert_with_word(docx_path, pdf_path)
            if pdf_path.exists():
                return pdf_path
            errors.append("Word produced no output")
        except Exception as exc:                      # noqa: BLE001 - report and fall back
            errors.append(f"Word: {exc}")
    try:
        _convert_with_libreoffice(docx_path, pdf_path)
        if pdf_path.exists():
            return pdf_path
        errors.append("LibreOffice produced no output")
    except Exception as exc:                          # noqa: BLE001
        errors.append(f"LibreOffice: {exc}")

    raise PdfConversionError("; ".join(errors) or "no converter available")


def docx_to_pdf_batch(pairs: list[tuple[Path, Path]]) -> dict[str, str]:
    """Convert many documents in one go.

    The whole batch runs as a single job on the Word thread, so nothing else can
    interleave and the instance is asked for once rather than per sheet. Returns
    {docx_path: error}, empty string meaning success.
    """
    results: dict[str, str] = {}
    if not pairs:
        return results

    if not word_available():
        for src, dst in pairs:
            try:
                docx_to_pdf(src, dst)
                results[str(Path(src).resolve())] = ""
            except Exception as exc:                  # noqa: BLE001
                results[str(Path(src).resolve())] = str(exc)
        return results

    def work(word):
        for src, dst in pairs:
            try:
                source, target = _prepare(src, dst)
            except Exception as exc:                  # noqa: BLE001
                results[str(Path(src).resolve())] = str(exc)
                continue
            try:
                _export(word, source, target)
                results[str(source)] = "" if target.exists() else "Word produced no output"
            except Exception as exc:                  # noqa: BLE001
                results[str(source)] = f"Word: {exc}"

    try:
        _WORKER.run(work, timeout=60.0 + 30.0 * len(pairs))
    except Exception as exc:                          # noqa: BLE001 - Word failed to start
        _WORKER.reset()
        for src, _ in pairs:
            results.setdefault(str(Path(src).resolve()), f"Word: {exc}")
    finally:
        if not KEEP_WORD_ALIVE:
            _WORKER.reset()
    return results


def merge_pdfs(pdf_paths: list[Path], out_path: Path) -> Path:
    """Combine the case documents into one printable PDF, in form order."""
    from pypdf import PdfWriter

    writer = PdfWriter()
    for path in pdf_paths:
        path = Path(path)
        if path.exists():
            writer.append(str(path))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "wb") as fh:
        writer.write(fh)
    writer.close()
    return out_path


# The case file reads better when every page is the same size, so the wide
# sheets are turned rather than left as landscape pages in a portrait bundle.
# 270 puts the table's first column at the foot of the page and the signature
# block on the right, which is how the printed original reads.
PORTRAIT_ROTATION = 270

# Set PENSION_ROTATE_WIDE=0 to leave the wide sheets as landscape pages.
ROTATE_WIDE_PAGES = os.environ.get("PENSION_ROTATE_WIDE", "1").strip().lower() \
    not in ("0", "false", "no")


def rotate_landscape_pages(pdf_path: Path, angle: int = PORTRAIT_ROTATION) -> int:
    """Turn landscape pages so they present as portrait. Returns how many.

    Only the /Rotate entry changes: the content is untouched, so the sheet that
    comes out of the printer is exactly the same piece of paper either way. What
    it fixes is the digital bundle, where a landscape page among portrait ones
    breaks the page width.
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject, NumberObject

    pdf_path = Path(pdf_path)
    if not ROTATE_WIDE_PAGES or not pdf_path.exists():
        return 0

    reader = PdfReader(str(pdf_path))
    # Most forms are portrait throughout, and rewriting a file costs far more
    # than looking at it, so decide before building anything.
    if not any(float(p.mediabox.width) > float(p.mediabox.height)
               for p in reader.pages):
        return 0

    turned = 0
    writer = PdfWriter()
    for page in reader.pages:
        box = page.mediabox
        if float(box.width) > float(box.height):
            page[NameObject("/Rotate")] = NumberObject(angle % 360)
            turned += 1
        writer.add_page(page)

    temporary = pdf_path.with_suffix(".rotating.pdf")
    with open(temporary, "wb") as fh:
        writer.write(fh)
    writer.close()
    temporary.replace(pdf_path)
    return turned
