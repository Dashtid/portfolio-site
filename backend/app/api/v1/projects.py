"""
Project API endpoints
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.middleware.rate_limit import rate_limit_public
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/projects", tags=["projects"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


@router.get("/", response_model=list[ProjectResponse])
@rate_limit_public
async def get_projects(request: Request, db: DbSession):
    """Get all projects"""
    _ = request  # Required for rate limiting
    result = await db.execute(
        select(Project).options(selectinload(Project.company)).order_by(Project.order_index)
    )
    return result.scalars().all()


@router.get("/{project_id}", response_model=ProjectResponse)
@rate_limit_public
async def get_project(request: Request, project_id: str, db: DbSession):
    """Get a specific project by ID"""
    _ = request  # Required for rate limiting
    result = await db.execute(
        select(Project).options(selectinload(Project.company)).where(Project.id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    db: DbSession,
    current_user: AdminUser,
):
    """Create a new project (requires admin authentication)"""
    _ = current_user  # Used for authentication
    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    """Update a project (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    # Whitelist of fields that can be updated (defense-in-depth)
    allowed_update_fields = frozenset(
        {
            "name",
            "description",
            "detailed_description",
            "technologies",
            "github_url",
            "live_url",
            "image_url",
            "company_id",
            "featured",
            "order_index",
            "video_url",
            "video_title",
            "map_url",
            "map_title",
            "responsibilities",
        }
    )

    for field, value in project_update.model_dump(exclude_unset=True).items():
        if field in allowed_update_fields:
            setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: DbSession,
    current_user: AdminUser,
):
    """Delete a project (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    try:
        await db.delete(project)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception(f"Failed to delete project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete project"
        ) from e
