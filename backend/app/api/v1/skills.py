"""
Skill API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate

router = APIRouter(prefix="/skills", tags=["skills"])


@router.get("/", response_model=list[SkillResponse])
async def get_skills(db: AsyncSession = Depends(get_db)):
    """Get all skills"""
    result = await db.execute(select(Skill).order_by(Skill.order_index))
    skills = result.scalars().all()
    return skills


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(skill_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific skill by ID"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill with ID {skill_id} not found"
        )

    return skill


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new skill (requires admin authentication)"""
    db_skill = Skill(**skill.dict())
    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)
    return db_skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_update: SkillUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update a skill (requires admin authentication)"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill with ID {skill_id} not found"
        )

    # Update only provided fields
    for field, value in skill_update.dict(exclude_unset=True).items():
        setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete a skill (requires admin authentication)"""
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Skill with ID {skill_id} not found"
        )

    await db.delete(skill)
    await db.commit()
