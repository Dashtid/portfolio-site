"""
Document API Endpoints

Endpoints for managing academic documents, theses, and papers.

The public surface (``GET /documents``, ``GET /documents/{id}``) is open;
the admin write surface (``POST``, ``PUT``, ``DELETE``, ``POST /upload``)
requires an admin user. Files uploaded through ``/upload`` are written
to ``static/documents/`` and served back by the ``/static`` mount.
"""

import re
import uuid
from pathlib import Path, PurePosixPath
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_admin_user
from app.database import get_db
from app.middleware.rate_limit import rate_limit_public
from app.models.document import Document
from app.models.user import User
from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Type alias for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]

# Where uploaded files land. settings.UPLOAD_DIR defaults to the repo's
# static/documents for local dev; on Fly it points at the persistent
# volume (/data/uploads/documents) so uploads survive deploys — the
# previous hardcoded path lived on the ephemeral rootfs and every deploy
# wiped them. The ``/media`` mount in main.py serves this directory back
# at ``/media/<filename>``, which is what the admin UI sets as
# ``file_url`` when creating the row. (Seeded PDFs baked into the image
# keep their /static/documents/ URLs via the existing /static mount.)
_UPLOAD_DIR = Path(settings.UPLOAD_DIR)
# Reject anything that isn't a PDF — the public catalogue is academic
# papers + theses, so other types would be out-of-scope content. Add to
# the whitelist when a real use case arrives.
_ALLOWED_CONTENT_TYPES = frozenset({"application/pdf"})
_ALLOWED_EXTENSIONS = frozenset({".pdf"})
# 25 MB hard cap. PDFs above this are usually scanned-image documents
# that should be re-flattened first; in any case the Fly volume is 1GB
# and we don't want a single upload to exhaust it.
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024
# Filenames are normalised to ASCII-safe slugs to make the served URL
# predictable and to dodge a path-traversal pattern that splices ``..``
# or path separators into the upload name.
_FILENAME_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


def _safe_filename(original: str) -> str:
    """Strip directory components and unsafe chars from an upload name.

    Returns a name guaranteed to: have no separators, fit our safe-char
    pattern, and (if the input was empty after cleaning) fall back to a
    UUID-based stem so we never store an empty filename.
    """
    # Backslash is only a separator on Windows, but uploads can carry
    # Windows-style paths regardless of what OS the server runs on —
    # normalise before splitting so the basename is platform-independent.
    just_name = PurePosixPath(original.replace("\\", "/")).name
    cleaned = _FILENAME_SAFE.sub("-", just_name).strip("-.")
    if not cleaned:
        cleaned = uuid.uuid4().hex
    return cleaned


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


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    document: DocumentCreate,
    db: DbSession,
    current_user: AdminUser,
):
    """Create a new document row (admin only).

    The file itself must already exist (uploaded via ``POST /upload``
    or seeded). This endpoint only writes the catalogue row.
    """
    _ = current_user
    existing = (
        await db.execute(select(Document).where(Document.id == document.id))
    ).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Document with this id already exists"
        )
    db_doc = Document(**document.model_dump())
    db.add(db_doc)
    await db.commit()
    await db.refresh(db_doc)
    return db_doc


@router.put("/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: str,
    document_update: DocumentUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    """Update document metadata (admin only).

    Whitelisted field set mirrors the other admin CRUD endpoints — the
    Pydantic schema already constrains shape, but the explicit allowlist
    is defence-in-depth against schema drift.
    """
    _ = current_user
    result = await db.execute(select(Document).where(Document.id == document_id))
    db_doc = result.scalar_one_or_none()
    if not db_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    allowed = frozenset(
        {
            "title",
            "description",
            "document_type",
            "file_path",
            "file_size",
            "file_url",
            "published_date",
            "order_index",
        }
    )
    for field, value in document_update.model_dump(exclude_unset=True).items():
        if field in allowed:
            setattr(db_doc, field, value)

    await db.commit()
    await db.refresh(db_doc)
    return db_doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: DbSession,
    current_user: AdminUser,
):
    """Delete a document row (admin only).

    The underlying file on disk is left alone — surface a manual cleanup
    flow if/when this becomes a real problem; deleting a referenced file
    silently from inside a DELETE handler is too easy to get wrong.
    """
    _ = current_user
    result = await db.execute(select(Document).where(Document.id == document_id))
    db_doc = result.scalar_one_or_none()
    if not db_doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    await db.delete(db_doc)
    await db.commit()


@router.post("/upload")
async def upload_document_file(
    current_user: AdminUser,
    file: Annotated[UploadFile, File(description="The PDF file to upload")],
):
    """Accept a PDF upload, persist it under ``static/documents/``, and
    return the metadata the caller needs to POST a Document row.

    The two-step flow (upload → create row) keeps file storage and
    catalogue concerns separate; the same upload can be referenced by
    a brand-new row or by an existing row whose file is being replaced.
    """
    _ = current_user

    if file.content_type not in _ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only application/pdf uploads are accepted",
        )

    raw_name = file.filename or "document.pdf"
    suffix = Path(raw_name).suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Filename must end in .pdf",
        )

    # Read up to the cap + 1 byte so an oversize upload is rejected
    # without us having to buffer arbitrary data first.
    contents = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(contents) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB limit",
        )

    # Content sniff: a real PDF starts with "%PDF-". The content-type and
    # extension gates above are client-claimed and trivially forged; this
    # is the only check bound to the bytes we actually persist and later
    # serve back from /media.
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File content is not a valid PDF",
        )

    safe_name = _safe_filename(raw_name)
    # Always prefix with a short UUID so two uploads of the same filename
    # don't clobber each other, even if the admin doesn't notice.
    unique_name = f"{uuid.uuid4().hex[:8]}-{safe_name}"
    if not unique_name.lower().endswith(".pdf"):
        unique_name = f"{unique_name}.pdf"

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target_path = _UPLOAD_DIR / unique_name
    target_path.write_bytes(contents)

    relative_path = f"documents/{unique_name}"
    public_url = f"/media/{unique_name}"
    return {
        "file_path": relative_path,
        "file_size": len(contents),
        "file_url": public_url,
        "original_filename": raw_name,
    }


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
