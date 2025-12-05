"""
Test script to diagnose Companies API serialization issue
"""

import asyncio
import sys
import traceback

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add app to path
sys.path.insert(0, ".")

from app.models.company import Company
from app.schemas.company import CompanyResponse

DATABASE_URL = "sqlite+aiosqlite:///./portfolio.db"


async def test_companies():
    """Test company serialization"""
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        # Fetch companies
        result = await session.execute(select(Company).order_by(Company.order_index))
        companies = result.scalars().all()

        print(f"Found {len(companies)} companies in database")

        if companies:
            for i, company in enumerate(companies, 1):
                print(f"\n--- Company {i}: {company.name} ---")
                print(f"ID: {company.id} (type: {type(company.id)})")
                print(f"Title: {company.title}")
                print(f"Start Date: {company.start_date} (type: {type(company.start_date)})")
                print(f"End Date: {company.end_date} (type: {type(company.end_date)})")
                print(
                    f"Responsibilities: {company.responsibilities} (type: {type(company.responsibilities)})"
                )
                print(f"Technologies: {company.technologies} (type: {type(company.technologies)})")
                print(f"Created At: {company.created_at} (type: {type(company.created_at)})")
                print(f"Updated At: {company.updated_at} (type: {type(company.updated_at)})")

                # Try to serialize with Pydantic
                try:
                    response = CompanyResponse.model_validate(company)
                    print("✓ Pydantic serialization SUCCESS")
                    print(f"  Response: {response.model_dump_json()[:200]}...")
                except Exception as e:
                    print("[FAIL] Pydantic serialization FAILED:")
                    print(f"  Error: {type(e).__name__}: {e}")
                    traceback.print_exc()
        else:
            print("No companies found in database!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_companies())
