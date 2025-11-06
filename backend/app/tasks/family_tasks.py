"""Background tasks for Family Banking Hub."""

from __future__ import annotations

import asyncio
import logging
from contextlib import contextmanager

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.family import FamilyGroup, FamilyMember
from app.services.family_service import FamilyService

logger = logging.getLogger(__name__)


@contextmanager
def session_scope() -> Session:
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def family_monitor_loop(interval_seconds: int = 3600) -> None:
    """Periodically evaluate family budgets and member limits."""
    while True:
        try:
            with session_scope() as db:
                family_ids = [fg.id for fg in db.query(FamilyGroup.id).all()]
                for family_id in family_ids:
                    try:
                        FamilyService._evaluate_family_budgets(db, family_id=family_id)
                        member_ids = [fm.id for fm in db.query(FamilyMember.id).filter(FamilyMember.family_id == family_id).all()]
                        for member_id in member_ids:
                            FamilyService._evaluate_member_limits(db, family_id=family_id, member_id=member_id)
                    except Exception as family_error:  # pragma: no cover - defensive
                        logger.exception("Family monitor iteration error for family %s: %s", family_id, family_error)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.exception("Family monitor loop failure: %s", exc)

        await asyncio.sleep(interval_seconds)


