"""
Company API endpoints
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]


@router.get("/", response_model=list[CompanyResponse])
async def get_companies(db: DbSession):
    """Get all companies"""
    result = await db.execute(select(Company).order_by(Company.order_index))
    return result.scalars().all()


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, db: DbSession):
    """Get a specific company by ID"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Company with ID {company_id} not found"
        )

    return company


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company: CompanyCreate,
    db: DbSession,
    current_user: AdminUser,
):
    """Create a new company (requires admin authentication)"""
    _ = current_user  # Used for authentication
    db_company = Company(**company.model_dump())
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)
    return db_company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_update: CompanyUpdate,
    db: DbSession,
    current_user: AdminUser,
):
    """Update a company (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Company with ID {company_id} not found"
        )

    for field, value in company_update.model_dump(exclude_unset=True).items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    db: DbSession,
    current_user: AdminUser,
):
    """Delete a company (requires admin authentication)"""
    _ = current_user  # Used for authentication
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Company with ID {company_id} not found"
        )

    await db.delete(company)
    await db.commit()


# NOTE: rebuild_complete_data_temp endpoint has been REMOVED for security reasons.
# This endpoint allowed database manipulation and should not exist in production.
# If needed for development, use the migration scripts in the backend directory instead:
#   - migrate_data.py
#   - migrate_real_content.py
#   - populate_experience_details.py
