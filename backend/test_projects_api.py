"""
Test script to diagnose Projects API serialization issue
"""
import asyncio
import sys
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Add app to path
sys.path.insert(0, ".")

from app.models.project import Project
from app.schemas.project import ProjectResponse

DATABASE_URL = "sqlite+aiosqlite:///./portfolio.db"

async def test_projects():
    """Test project serialization"""
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session_maker() as session:
        # Fetch projects
        result = await session.execute(select(Project).order_by(Project.order_index))
        projects = result.scalars().all()

        print(f"Found {len(projects)} projects in database")

        if projects:
            for i, project in enumerate(projects, 1):
                print(f"\n--- Project {i}: {project.name} ---")
                print(f"ID: {project.id}")
                print(f"Description: {project.description[:50] if project.description else None}...")
                print(f"Technologies: {project.technologies}")
                print(f"Detailed Description: {project.detailed_description}")
                print(f"Video URL: {project.video_url}")
                print(f"Responsibilities: {project.responsibilities}")

                # Try to serialize with Pydantic
                try:
                    response = ProjectResponse.model_validate(project)
                    print(f"[OK] Pydantic serialization SUCCESS")
                    print(f"  Response JSON length: {len(response.model_dump_json())} chars")
                except Exception as e:
                    print(f"[FAIL] Pydantic serialization FAILED:")
                    print(f"  Error: {type(e).__name__}: {e}")
                    import traceback
                    traceback.print_exc()
        else:
            print("No projects found in database!")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_projects())
