"""
Document API Endpoints

Endpoints for managing academic documents, theses, and papers.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
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
async def get_documents(request: Request, db: DbSession):
    """
    Get all documents.

    Returns:
        List of all documents ordered by order_index, then published_date (most recent first)
    """
    try:
        result = await db.execute(
            select(Document).order_by(Document.order_index.asc(), Document.published_date.desc())
        )
        documents = result.scalars().all()
        logger.info("Retrieved %d documents", len(documents))
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
