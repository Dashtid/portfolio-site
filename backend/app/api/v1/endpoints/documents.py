"""
Document API Endpoints

Endpoints for managing academic documents, theses, and papers.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/", response_model=list[DocumentResponse])
async def get_documents(db: AsyncSession = Depends(get_db)):  # noqa: B008
    """
    Get all documents.

    Returns:
        List of all documents ordered by published_date (most recent first)
    """
    try:
        result = await db.execute(select(Document).order_by(Document.published_date.desc()))
        documents = result.scalars().all()
        logger.info(f"Retrieved {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch documents") from e


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)):  # noqa: B008
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

        logger.info(f"Retrieved document: {document.title}")
        return document
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch document") from e
