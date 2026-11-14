import sqlite3
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from config.settings import settings

_engine = None
_Session = None


def get_engine():
    global _engine, _Session
    if _engine is None:
        _engine = create_engine(f"sqlite:///{settings.db_path}", connect_args={"check_same_thread": False})

        @event.listens_for(_engine, "connect")
        def _fk(dbapi_conn, _):
            dbapi_conn.execute("PRAGMA foreign_keys=ON")
        _Session = sessionmaker(bind=_engine, expire_on_commit=False)
    return _engine


def get_session():
    get_engine()
    return _Session()


def reset_engine(db_path: str | None = None):
    """Uso en pruebas: apunta a otra base."""
    global _engine, _Session
    if db_path:
        settings_db = db_path
        _engine = create_engine(f"sqlite:///{settings_db}", connect_args={"check_same_thread": False})
        _Session = sessionmaker(bind=_engine, expire_on_commit=False)
    else:
        _engine = _Session = None
