from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.database import get_db
from app.models.education import Education
from app.schemas.education import Education as EducationSchema, EducationCreate, EducationUpdate

router = APIRouter(
    prefix="/education",
    tags=["education"]
)

@router.get("/", response_model=List[EducationSchema])
async def get_all_education(db: AsyncSession = Depends(get_db)):
    """Get all education records"""
    result = await db.execute(
        select(Education).order_by(Education.order, Education.start_date.desc())
    )
    education = result.scalars().all()
    return education

@router.get("/degrees/", response_model=List[EducationSchema])
async def get_degrees(db: AsyncSession = Depends(get_db)):
    """Get only degree education records (not certifications)"""
    result = await db.execute(
        select(Education)
        .where(Education.is_certification == False)
        .order_by(Education.order, Education.start_date.desc())
    )
    degrees = result.scalars().all()
    return degrees

@router.get("/certifications/", response_model=List[EducationSchema])
async def get_certifications(db: AsyncSession = Depends(get_db)):
    """Get only certification records"""
    result = await db.execute(
        select(Education)
        .where(Education.is_certification == True)
        .order_by(Education.order, Education.end_date.desc())
    )
    certifications = result.scalars().all()
    return certifications

@router.get("/{education_id}/", response_model=EducationSchema)
async def get_education(education_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single education record by ID"""
    result = await db.execute(select(Education).where(Education.id == education_id))
    education = result.scalar_one_or_none()
    if not education:
        raise HTTPException(status_code=404, detail="Education record not found")
    return education

@router.post("/", response_model=EducationSchema)
async def create_education(education: EducationCreate, db: AsyncSession = Depends(get_db)):
    """Create a new education record"""
    db_education = Education(**education.dict())
    db.add(db_education)
    await db.commit()
    await db.refresh(db_education)
    return db_education

@router.put("/{education_id}/", response_model=EducationSchema)
async def update_education(
    education_id: int,
    education_update: EducationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an education record"""
    # Check if education exists
    result = await db.execute(select(Education).where(Education.id == education_id))
    db_education = result.scalar_one_or_none()
    if not db_education:
        raise HTTPException(status_code=404, detail="Education record not found")

    # Update fields
    update_data = education_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_education, field, value)

    await db.commit()
    await db.refresh(db_education)
    return db_education

@router.delete("/{education_id}/")
async def delete_education(education_id: int, db: AsyncSession = Depends(get_db)):
    """Delete an education record"""
    result = await db.execute(select(Education).where(Education.id == education_id))
    db_education = result.scalar_one_or_none()
    if not db_education:
        raise HTTPException(status_code=404, detail="Education record not found")

    await db.delete(db_education)
    await db.commit()
    return {"message": "Education record deleted successfully"}