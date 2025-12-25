"""
Education API endpoints
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.models.education import Education
from app.models.user import User
from app.schemas.education import Education as EducationSchema
from app.schemas.education import EducationCreate, EducationUpdate

router = APIRouter(prefix="/education", tags=["education"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


@router.get("/", response_model=list[EducationSchema])
async def get_all_education(db: DbSession):
    """Get all education records"""
    result = await db.execute(
        select(Education).order_by(Education.order, Education.start_date.desc())
    )
    return result.scalars().all()


@router.get("/degrees/", response_model=list[EducationSchema])
async def get_degrees(db: DbSession):
    """Get only degree education records (not certifications)"""
    result = await db.execute(
        select(Education)
        .where(Education.is_certification.is_(False))
        .order_by(Education.order, Education.start_date.desc())
    )
    return result.scalars().all()


@router.get("/certifications/", response_model=list[EducationSchema])
async def get_certifications(db: DbSession):
    """Get only certification records"""
    result = await db.execute(
        select(Education)
        .where(Education.is_certification.is_(True))
        .order_by(Education.order, Education.end_date.desc())
    )
    return result.scalars().all()


@router.get("/{education_id}/", response_model=EducationSchema)
async def get_education(education_id: int, db: DbSession):
    """Get a single education record by ID"""
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


@router.put("/{education_id}/", response_model=EducationSchema)
async def update_education(
    education_id: int,
    education_update: EducationUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    """Update an education record (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Education).where(Education.id == education_id))
    db_education = result.scalar_one_or_none()
    if not db_education:
        raise HTTPException(status_code=404, detail="Education record not found")

    update_data = education_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_education, field, value)

    await db.commit()
    await db.refresh(db_education)
    return db_education


@router.delete("/{education_id}/")
async def delete_education(
    education_id: int,
    db: DbSession,
    current_user: AdminUser,
):
    """Delete an education record (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Education).where(Education.id == education_id))
    db_education = result.scalar_one_or_none()
    if not db_education:
        raise HTTPException(status_code=404, detail="Education record not found")

    await db.delete(db_education)
    await db.commit()
    return {"message": "Education record deleted successfully"}
