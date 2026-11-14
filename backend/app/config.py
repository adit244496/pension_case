"""Application paths and settings.

Paths can be overridden with environment variables, so an office can keep the
database and the generated documents on a shared drive without editing code:

    PENSION_DB       full path to the SQLite file      (default backend/pension.db)
    PENSION_STORAGE  directory for generated documents (default backend/storage)
    PENSION_SECRET   file holding the session signing key (default backend/.secret)
    PENSION_DATA     folder holding all of the above    (default backend/)

The portable build (build_portable.bat) is one .exe with no Python on the
machine. Everything it carries -- the form templates and the built web
interface -- is read-only inside the bundle, so the working copies live in a
`data` folder beside the .exe instead, and the templates are copied there the
first time it runs. An office can then keep that folder on a shared drive, or
copy the whole thing to another machine and carry its cases with it.
"""
import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# PyInstaller sets both of these: the bundle is unpacked somewhere temporary,
# while sys.executable is the .exe the clerk actually double-clicked.
FROZEN = bool(getattr(sys, "frozen", False))
BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", str(BASE_DIR)))
APP_DIR = Path(sys.executable).resolve().parent if FROZEN else BASE_DIR


def _path(env_var: str, default: Path) -> Path:
    value = os.environ.get(env_var, "").strip()
    return Path(value).expanduser().resolve() if value else default


# Everything the app writes lives under here: the database, the generated
# documents and the templates as the office has edited them.
DATA_DIR = _path("PENSION_DATA", APP_DIR / "data" if FROZEN else BASE_DIR)

# Built frontend (frontend/dist). When present it is served by the API itself,
# so a deployment is one process behind nginx instead of two.
_dist_default = (BUNDLE_DIR / "frontend_dist") if FROZEN else BASE_DIR.parent / "frontend" / "dist"
FRONTEND_DIST = _path("PENSION_FRONTEND", _dist_default)

TEMPLATE_DIR = _path("PENSION_TEMPLATES", DATA_DIR / "templates")
STORAGE_DIR = _path("PENSION_STORAGE", DATA_DIR / "storage")
UPLOAD_DIR = STORAGE_DIR / "uploads"           # admin-uploaded template revisions
DB_PATH = _path("PENSION_DB", DATA_DIR / "pension.db")
SECRET_PATH = _path("PENSION_SECRET", DATA_DIR / ".secret")

for _d in (TEMPLATE_DIR, STORAGE_DIR, UPLOAD_DIR, DB_PATH.parent, SECRET_PATH.parent):
    _d.mkdir(parents=True, exist_ok=True)

# First run of the portable build: lay the templates it carries into the data
# folder, where an admin can then edit them. Existing files are left alone, so
# an upgrade brings in new forms without undoing anyone's wording.
if FROZEN:
    _bundled = BUNDLE_DIR / "templates"
    if _bundled.is_dir():
        for _src in _bundled.glob("*.docx"):
            _dst = TEMPLATE_DIR / _src.name
            if not _dst.exists():
                shutil.copy2(_src, _dst)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Local desktop mode: skip the sign-in screen when the app is launched by
# start.bat on the clerk's own machine. Requests are still only trusted when
# they come from that machine -- see auth.local_mode_user -- so setting this on
# a networked server does not open it up.
LOCAL_MODE = os.environ.get("PENSION_LOCAL_MODE", "").strip().lower() in ("1", "true", "yes")

# CORS origins. Only needed when the web interface is served from a different
# origin than the API (the Vite dev server). Add production origins with
# PENSION_ORIGINS as a comma-separated list.
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
_extra = os.environ.get("PENSION_ORIGINS", "").strip()
if _extra:
    ALLOWED_ORIGINS += [o.strip() for o in _extra.split(",") if o.strip()]
