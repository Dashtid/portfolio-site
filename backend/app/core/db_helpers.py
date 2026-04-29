"""
Shared database helpers for API endpoint handlers.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def db_mutation(db: AsyncSession, *, action: str) -> AsyncIterator[None]:
    """
    Wrap a database mutation block with commit/rollback + 500 error mapping.

    Usage:
        async with db_mutation(db, action="delete company"):
            await db.delete(company)

    HTTPException raised inside the block (e.g. a 404 from validation) is
    re-raised unchanged so endpoints can still emit non-500 errors. Any other
    exception triggers rollback, logs the full trace, and surfaces a generic
    500 with the action interpolated into the user-facing message.

    Args:
        db: The active AsyncSession.
        action: Verb-noun phrase used in the 500 detail (``"Failed to {action}"``)
            and the log line. Example: ``"delete company"``.
    """
    try:
        yield
        await db.commit()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to %s", action)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to {action}",
        ) from e
