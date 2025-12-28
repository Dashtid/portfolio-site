"""
Skill API endpoints
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.middleware.rate_limit import rate_limit_public
from app.models.skill import Skill
from app.models.user import User
from app.schemas.skill import SkillCreate, SkillResponse, SkillUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/skills", tags=["skills"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


@router.get("/", response_model=list[SkillResponse])
@rate_limit_public
async def get_skills(request: Request, db: DbSession):
    """Get all skills"""
    _ = request  # Required for rate limiting
    result = await db.execute(select(Skill).order_by(Skill.order_index))
    return result.scalars().all()


@router.get("/{skill_id}", response_model=SkillResponse)
@rate_limit_public
async def get_skill(request: Request, skill_id: str, db: DbSession):
    """Get a specific skill by ID"""
    _ = request  # Required for rate limiting
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return skill


@router.post("/", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill: SkillCreate,
    db: DbSession,
    current_user: AdminUser,
):
    """Create a new skill (requires admin authentication)"""
    _ = current_user  # Used for authentication
    db_skill = Skill(**skill.model_dump())
    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)
    return db_skill


@router.put("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: str,
    skill_update: SkillUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    """Update a skill (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    # Whitelist of fields that can be updated (defense-in-depth)
    allowed_update_fields = frozenset(
        {"name", "category", "proficiency_level", "years_of_experience", "order_index"}
    )

    for field, value in skill_update.model_dump(exclude_unset=True).items():
        if field in allowed_update_fields:
            setattr(skill, field, value)

    await db.commit()
    await db.refresh(skill)
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: str,
    db: DbSession,
    current_user: AdminUser,
):
    """Delete a skill (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill = result.scalar_one_or_none()

    if not skill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    try:
        await db.delete(skill)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception(f"Failed to delete skill {skill_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete skill"
        ) from e
