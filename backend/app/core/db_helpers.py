"""
Shared database helpers for API endpoint handlers.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.logger import get_logger

logger = get_logger(__name__)


class Pagination(BaseModel):
    """Optional pagination params, shared across public list endpoints.

    PERF-08: previously every list endpoint returned the full table. That's
    fine while content fits in <20 rows but a single bulk import or a
    runaway admin POST could turn a public GET into a multi-MB payload
    over the wire. Bound it with `limit` (hard cap 100, default 100 so
    today's clients see identical behaviour) and `offset` for clients
    that opt into paging.

    Returns a list (not a paginated envelope) so existing API consumers
    keep working without changes — the params are opt-in.
    """

    limit: int = 100
    offset: int = 0


def pagination_params(
    limit: Annotated[int, Query(ge=1, le=100, description="Max rows to return (1-100)")] = 100,
    offset: Annotated[int, Query(ge=0, description="Number of rows to skip")] = 0,
) -> Pagination:
    return Pagination(limit=limit, offset=offset)


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
