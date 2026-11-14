"""FastAPI entry point for the pension (DCRG) case automation system."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import pdf, word_sync
from .config import ALLOWED_ORIGINS, FRONTEND_DIST, LOCAL_MODE
from .db import SessionLocal
from .migrate import migrate
from .routers import auth, cases, templates, tools

app = FastAPI(
    title="Pension Case Automation",
    description="Retirement Gratuity (DCRG) case preparation",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(templates.router)
app.include_router(tools.router)


@app.on_event("startup")
def on_startup():
    """Bring the schema up to date and register anything added since last run."""
    changes = migrate()
    if changes:
        print("Schema updated:", ", ".join(changes))
    db = SessionLocal()
    try:
        from .auth import DEFAULT_PASSWORD, DEFAULT_USERNAME, ensure_default_user
        from .seed import sync_templates
        sync_templates(db)
        if ensure_default_user(db):
            print(f"Default sign-in created -> {DEFAULT_USERNAME} / {DEFAULT_PASSWORD}")
            print("Change it from the account menu after signing in.")
    finally:
        db.close()

    # Watch the storage folder so a save in Word is acted on as it happens
    # rather than when the browser next asks.
    if not word_sync.start_watcher():
        print("Word edits will be picked up when the documents list is read.")


@app.on_event("shutdown")
def on_shutdown():
    """Stop the watcher and let go of the Word instance conversions share."""
    word_sync.stop_watcher()
    pdf.shutdown()


@app.get("/api/health")
def health():
    """Unauthenticated, so the sign-in page can show whether PDF export will work."""
    return {
        "status": "ok",
        "pdf_backend": pdf.backend_name(),
        "pdf_available": pdf.backend_name() != "none",
        "auth_required": not LOCAL_MODE,
        "local_desktop": LOCAL_MODE,
    }


# --------------------------------------------------------------------------
# Serve the built web interface, when there is one.
#
# In development the Vite server serves it and proxies /api here, so this block
# does nothing. In production `npm run build` writes frontend/dist and the API
# serves it directly -- one process to run, and no CORS to configure.
# --------------------------------------------------------------------------
# Python does not know this one, and without it the Marathi face is served as
# text/plain, which some browsers refuse to use as a font.
mimetypes.add_type("font/woff2", ".woff2")

if FRONTEND_DIST.is_dir() and (FRONTEND_DIST / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"),
              name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa(full_path: str):
        """Return the requested file, falling back to index.html for app routes."""
        if full_path.startswith("api/"):
            raise HTTPException(404, "Not found")
        # Icons this app does not have. Without this the catch-all below hands
        # back index.html as text/html with a 200, so the browser fetches the
        # whole page, fails to read it as an image, and may cache that answer.
        if full_path in ("favicon.ico", "favicon.png", "apple-touch-icon.png",
                         "apple-touch-icon-precomposed.png"):
            raise HTTPException(404, "Not found")
        candidate = (FRONTEND_DIST / full_path).resolve()
        if (full_path and candidate.is_file()
                and candidate.is_relative_to(FRONTEND_DIST.resolve())):
            return FileResponse(candidate)
        return FileResponse(FRONTEND_DIST / "index.html")
