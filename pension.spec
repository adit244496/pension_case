# PyInstaller recipe for the portable Windows build.
#
#   build_portable.bat        (builds the web interface first, then this)
#
# The result is dist/PensionCase/, a folder that can be copied to a machine with
# no Python and no Node on it. Word does the PDF conversion there, as it does
# here, so the pages come out identical to the ones this machine produces.
from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

PROJECT = Path(SPECPATH)
BACKEND = PROJECT / "backend"

# The templates and the built web interface travel inside the .exe; config.py
# copies the templates out to the data folder on first run, because an admin
# edits them.
datas = [
    (str(BACKEND / "templates"), "templates"),
    (str(PROJECT / "frontend" / "dist"), "frontend_dist"),
]

# Uvicorn and Starlette reach for these by name at runtime, so PyInstaller
# cannot see them by following imports.
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "app.main",
    "encodings.idna",
]
hiddenimports += collect_submodules("app")
hiddenimports += collect_submodules("win32com")
# The directory watcher behind "a save in Word shows up by itself". It is
# imported only when the watcher starts, so nothing PyInstaller follows leads to
# it, and its Rust extension has to be named as well. Without these the portable
# build still works -- edits are picked up when the documents list is read --
# but a second or so later.
hiddenimports += ["watchfiles", "watchfiles.main", "watchfiles._rust_notify"]

analysis = Analysis(
    [str(BACKEND / "desktop.py")],
    pathex=[str(BACKEND)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    # Nothing here draws charts or does science; leaving these out keeps the
    # folder small enough to copy over a slow network.
    excludes=["tkinter", "matplotlib", "numpy", "pandas", "scipy", "PIL",
              "pytest", "IPython", "notebook"],
    noarchive=False,
)
pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="PensionCase",
    console=True,               # the window explains itself and holds errors
    icon="pension.ico",         # the same sheet mark the browser tab shows
    debug=False,
    strip=False,
    upx=False,
    disable_windowed_traceback=False,
)

COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    name="PensionCase",
)
