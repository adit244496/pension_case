"""The portable build's entry point: one .exe, no Python on the machine.

The clerk double-clicks it, a console window explains what is happening, and the
browser opens on the case list. Everything else -- the database, the documents,
the templates -- lives in the `data` folder beside the .exe.

Sign-in is skipped, as with start.bat, because the machine's own user is the
operator; the API still only trusts that for requests from this machine.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser

# Local desktop mode has to be set before the app is imported, since config
# reads it at import time.
os.environ.setdefault("PENSION_LOCAL_MODE", "1")

HOST = "127.0.0.1"
PORTS = (8000, 8001, 8002, 8003, 8080)


def free_port() -> int:
    """The first port nothing else is listening on.

    Deliberately without SO_REUSEADDR: on Windows that option lets a socket bind
    over one another process already holds, so the probe would report a busy
    port as free and the server would then fail to start on it.
    """
    for port in PORTS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind((HOST, port))
            except OSError:
                continue
        # And nothing answering on it either, which catches a listener left
        # behind by a process that has since died.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reach:
            reach.settimeout(0.3)
            if reach.connect_ex((HOST, port)) == 0:
                continue
        return port
    raise SystemExit(
        "Ports 8000-8003 and 8080 are all in use.\n"
        "Another copy of the application is probably already running."
    )


def open_when_ready(url: str, port: int) -> None:
    """Wait for the server to answer, then show it to the operator."""
    for _ in range(60):
        time.sleep(0.5)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            if probe.connect_ex((HOST, port)) == 0:
                webbrowser.open(url)
                return
    print("The application did not start in time. See the messages above.")


def main() -> None:
    import uvicorn

    from app.config import DATA_DIR, FRONTEND_DIST
    from app.seed import main as seed

    print("Pension Case System")
    print("-" * 60)
    print(f"Data folder : {DATA_DIR}")

    if not (FRONTEND_DIST / "index.html").exists():
        print("\nThe web interface is missing from this build.")
        input("Press Enter to close. ")
        raise SystemExit(1)

    print("Preparing the database ...")
    seed()

    from app import pdf
    engine = pdf.backend_name()
    print(f"PDF engine  : {engine}"
          + ("" if engine != "none" else "  (no Word found -- Word files only)"))

    port = free_port()
    url = f"http://{HOST}:{port}/"
    print(f"Address     : {url}")
    print("-" * 60)
    print("Leave this window open while you work.")
    print("Closing it closes the application.\n")

    # PENSION_NO_BROWSER leaves the browser alone, for a machine where the app
    # is started by the Task Scheduler rather than by a person.
    if not os.environ.get("PENSION_NO_BROWSER", "").strip():
        threading.Thread(target=open_when_ready, args=(url, port), daemon=True).start()
    uvicorn.run("app.main:app", host=HOST, port=port, workers=1,
                log_level="warning", access_log=False)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:                              # noqa: BLE001
        # A frozen app has no terminal to leave a traceback in, so hold the
        # window open long enough for the operator to read what went wrong.
        import traceback
        traceback.print_exc()
        print(f"\nThe application could not start: {exc}")
        input("Press Enter to close. ")
        sys.exit(1)
