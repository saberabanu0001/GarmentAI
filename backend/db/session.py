"""SQLAlchemy engine/session helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.core.config import get_settings

_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker[Session] | None = None


def is_database_enabled() -> bool:
    return bool(get_settings().resolved_database_url)


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is not None:
        return _ENGINE
    s = get_settings()
    url = s.resolved_database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not configured")
    kwargs: dict = {"echo": s.database_echo, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs["pool_pre_ping"] = True
    _ENGINE = create_engine(url, **kwargs)
    return _ENGINE


def _get_session_factory() -> sessionmaker[Session]:
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            bind=get_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
            class_=Session,
        )
    return _SESSION_FACTORY


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    session = _get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
