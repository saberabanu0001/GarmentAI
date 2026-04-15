"""Schema bootstrap helper.

This intentionally uses SQLAlchemy metadata create_all for a simple first step.
Use Alembic for production migrations as the next step.
"""

from __future__ import annotations

def init_database() -> bool:
    try:
        from backend.db.models import Base
        from backend.db.session import get_engine, is_database_enabled
    except ModuleNotFoundError:
        return False
    if not is_database_enabled():
        return False
    Base.metadata.create_all(bind=get_engine())
    return True
