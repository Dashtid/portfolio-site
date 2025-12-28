"""
Education API endpoints
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.middleware.rate_limit import rate_limit_public
from app.models.education import Education
from app.models.user import User
from app.schemas.education import Education as EducationSchema
from app.schemas.education import EducationCreate, EducationUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/education", tags=["education"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


@router.get("/", response_model=list[EducationSchema])
@rate_limit_public
async def get_all_education(request: Request, db: DbSession):
    """Get all education records"""
    _ = request  # Required for rate limiting
    result = await db.execute(
        select(Education).order_by(Education.order_index, Education.start_date.desc())
    )
    return result.scalars().all()


@router.get("/degrees", response_model=list[EducationSchema])
@rate_limit_public
async def get_degrees(request: Request, db: DbSession):
    """Get only degree education records (not certifications)"""
    _ = request  # Required for rate limiting
    result = await db.execute(
        select(Education)
        .where(Education.is_certification.is_(False))
        .order_by(Education.order_index, Education.start_date.desc())
    )
    return result.scalars().all()


@router.get("/certifications", response_model=list[EducationSchema])
@rate_limit_public
async def get_certifications(request: Request, db: DbSession):
    """Get only certification records"""
    _ = request  # Required for rate limiting
    result = await db.execute(
        select(Education)
        .where(Education.is_certification.is_(True))
        .order_by(Education.order_index, Education.end_date.desc())
    )
    return result.scalars().all()


@router.get("/{education_id}", response_model=EducationSchema)
@rate_limit_public
async def get_education(
    request: Request,
    db: DbSession,
    education_id: int = Path(..., gt=0, description="Education record ID"),
):
    """Get a single education record by ID"""
    _ = request  # Required for rate limiting
    result = await db.execute(select(Education).where(Education.id == education_id))
    education = result.scalar_one_or_none()
    if not education:
        raise HTTPException(status_code=404, detail="Education record not found")
    return education


@router.post("/", response_model=EducationSchema)
async def create_education(
    education: EducationCreate,
    db: DbSession,
    current_user: AdminUser,
):
    """Create a new education record (requires admin authentication)"""
    _ = current_user  # Used for authentication
    db_education = Education(**education.model_dump())
    db.add(db_education)
    await db.commit()
    await db.refresh(db_education)
    return db_education


@router.put("/{education_id}", response_model=EducationSchema)
async def update_education(
    education_update: EducationUpdate,
    db: DbSession,
    current_user: AdminUser,
    education_id: int = Path(..., gt=0, description="Education record ID"),
):
    """Update an education record (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Education).where(Education.id == education_id))
    db_education = result.scalar_one_or_none()
    if not db_education:
        raise HTTPException(status_code=404, detail="Education record not found")

    # Whitelist of fields that can be updated (defense-in-depth)
    allowed_update_fields = frozenset(
        {
            "institution",
            "degree",
            "field_of_study",
            "start_date",
            "end_date",
            "location",
            "description",
            "logo_url",
            "is_certification",
            "certificate_number",
            "certificate_url",
            "order_index",
        }
    )

    update_data = education_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in allowed_update_fields:
            setattr(db_education, field, value)

    await db.commit()
    await db.refresh(db_education)
    return db_education


@router.delete("/{education_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_education(
    db: DbSession,
    current_user: AdminUser,
    education_id: int = Path(..., gt=0, description="Education record ID"),
):
    """Delete an education record (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Education).where(Education.id == education_id))
    db_education = result.scalar_one_or_none()
    if not db_education:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Education record not found"
        )

    try:
        await db.delete(db_education)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception(f"Failed to delete education {education_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete education record",
        ) from e
