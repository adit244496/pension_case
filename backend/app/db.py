from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_connection, _record):
        """Settings SQLite needs to survive a desktop app with several callers.

        WAL: in the default rollback journal a reader blocks a writer outright,
        and this app reads constantly -- the documents tab polls, the case screen
        refreshes. Under WAL readers and writers no longer wait on each other.

        busy_timeout: writers still take turns, so one that arrives during
        another's commit waits rather than failing. Five seconds -- the default --
        was short enough that a rebuild could push a photograph upload over it.
        """
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.execute("PRAGMA synchronous=NORMAL")
        finally:
            cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
