"""
Document API Endpoints

Endpoints for managing academic documents, theses, and papers.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.middleware.rate_limit import rate_limit_public
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Type alias for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[DocumentResponse])
@rate_limit_public
async def get_documents(
    request: Request,
    db: DbSession,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum records to return"),
):
    """
    Get documents ordered by order_index, then published_date (most recent first).

    Supports pagination via ``skip`` and ``limit`` query params. Default
    ``limit=50`` covers all current documents in one request; clients that
    need more must page explicitly.
    """
    try:
        result = await db.execute(
            select(Document)
            .order_by(Document.order_index.asc(), Document.published_date.desc())
            .offset(skip)
            .limit(limit)
        )
        documents = result.scalars().all()
        logger.info("Retrieved %d documents (skip=%d, limit=%d)", len(documents), skip, limit)
    except Exception as e:
        logger.exception("Error fetching documents")
        raise HTTPException(status_code=500, detail="Failed to fetch documents") from e
    else:
        return documents


@router.get("/{document_id}", response_model=DocumentResponse)
@rate_limit_public
async def get_document(request: Request, document_id: str, db: DbSession):
    """
    Get a specific document by ID.

    Args:
        document_id: Document unique identifier

    Returns:
        Document details

    Raises:
        404: Document not found
    """
    try:
        result = await db.execute(select(Document).where(Document.id == document_id))
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        logger.info("Retrieved document: %s", document.title)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error fetching document %s", document_id)
        raise HTTPException(status_code=500, detail="Failed to fetch document") from e
    else:
        return document
