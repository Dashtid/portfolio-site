"""
Database cleanup script for portfolio production database.
Fixes data issues found during bug hunting:
1. Remove duplicate Hermes company entry
2. Add missing company logos and websites
3. Add missing education logos
4. Fix project data (rename Portfolio Migration to Portfolio Site)

Run on Fly.io with:
    flyctl ssh console -a dashti-portfolio-backend -C 'python scripts/cleanup_database.py'
"""

import asyncio
import os
import sys

# Add the app directory to path for imports
sys.path.insert(0, "/app")

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


async def cleanup_database():
    """Main cleanup function"""
    # Get database URL from environment
    database_url = os.environ.get("DATABASE_URL", "")

    if not database_url:
        print("[-] DATABASE_URL not set")
        return

    # Convert postgres:// to postgresql+asyncpg://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    print(f"[*] Connecting to database...")

    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 1. Remove duplicate Hermes company entry
            print("\n[1/4] Removing duplicate Hermes company entry...")
            duplicate_id = "9f2a8d1b-ffdf-4f23-88bb-431990275d5b"
            result = await session.execute(
                delete(Company).where(Company.id == duplicate_id)
            )
            if result.rowcount > 0:
                print(f"    [+] Deleted duplicate Hermes entry (ID: {duplicate_id})")
            else:
                print("    [i] Duplicate already removed or not found")

            # 2. Update company logos and websites
            print("\n[2/4] Updating company logos and websites...")

            company_updates = [
                {
                    "id": "b1e21013-a9a9-491f-a5d3-fadb8c20bea2",  # KTH
                    "logo_url": "/images/KTH.png",
                    "website": "https://www.kth.se",
                },
                {
                    "id": "d4f2c56b-d5ee-48dc-98e7-de2556f27eb5",  # Stockholm Innovation Hub
                    "logo_url": "/images/innovation-hub.png",
                    "website": "https://stockholminnovation.com",
                },
                {
                    "id": "9ca80fd5-2015-4cff-acc8-1b900ed495e0",  # SOS
                    "website": "https://www.sodersjukhuset.se",
                },
                {
                    "id": "0225d2d1-d740-438c-bf4c-4bdcd8e4a88a",  # Finnish Defence Forces
                    "website": "https://puolustusvoimat.fi",
                },
                {
                    "id": "71821db5-b797-4592-b827-1205aae07cb4",  # SoftPro
                    "website": "https://softpro.se",
                },
                {
                    "id": "1e82215f-e961-4c62-8c7c-ee4c80ff4f6d",  # Karolinska
                    "website": "https://www.karolinska.se",
                },
            ]

            for update_data in company_updates:
                company_id = update_data.pop("id")
                if update_data:  # Only update if there are fields to update
                    result = await session.execute(
                        update(Company)
                        .where(Company.id == company_id)
                        .values(**update_data)
                    )
                    if result.rowcount > 0:
                        print(f"    [+] Updated company {company_id}")

            # 3. Update education logos
            print("\n[3/4] Updating education logos...")

            education_updates = [
                {
                    "id": 5,  # KTH M.Sc.
                    "logo_url": "/images/KTH.png",
                },
                {
                    "id": 6,  # Lund Exchange
                    "logo_url": "/images/LTH.png",
                    "location": "Lund, Sweden",
                },
                {
                    "id": 7,  # Foretagsuniversitetet cert
                    "logo_url": "/images/foretagsuniversitet.png",
                },
                {
                    "id": 8,  # Microsoft AZ-500
                    "logo_url": "/images/microsoft.png",
                },
                {
                    "id": 9,  # EC-Council CEH
                    "logo_url": "/images/ec-council.png",
                },
            ]

            for update_data in education_updates:
                edu_id = update_data.pop("id")
                if update_data:
                    result = await session.execute(
                        update(Education)
                        .where(Education.id == edu_id)
                        .values(**update_data)
                    )
                    if result.rowcount > 0:
                        print(f"    [+] Updated education {edu_id}")

            # 4. Fix project data - remove duplicate Portfolio Migration
            print("\n[4/4] Cleaning up projects...")

            # Delete the old "Portfolio Migration" entry (keep Portfolio Site)
            result = await session.execute(
                delete(Project).where(Project.id == "e55e8ca2-a6f0-42ec-8ee8-fb0b637a8087")
            )
            if result.rowcount > 0:
                print("    [+] Removed duplicate 'Portfolio Migration' project")

            # Update Portfolio Site with correct live URL
            result = await session.execute(
                update(Project)
                .where(Project.id == "9730820d-4c11-4ca6-bc66-6991f8e516c0")
                .values(live_url="https://dashti.se")
            )
            if result.rowcount > 0:
                print("    [+] Updated Portfolio Site live URL to dashti.se")

            # Remove broken project image URLs (images don't exist yet)
            project_image_fixes = [
                "73d16292-68dd-49c5-9428-4aac92818046",  # DICOM Fuzzer
                "594eb414-c835-491b-9adc-88335918d3cd",  # Biomedical AI
                "71526f9f-feb6-49de-8769-1e9ed188127c",  # Sysadmin Toolkit
                "4b8a8c04-6c9a-4d83-9656-f5c8e2eca90c",  # Defensive Toolkit
                "c7ed2cc5-40a3-4f15-9609-cd8f3ce31e9f",  # Offensive Toolkit
                "9730820d-4c11-4ca6-bc66-6991f8e516c0",  # Portfolio Site
            ]
            for project_id in project_image_fixes:
                result = await session.execute(
                    update(Project)
                    .where(Project.id == project_id)
                    .values(image_url=None)
                )
            print("    [+] Cleared broken project image URLs")

            await session.commit()
            print("\n[+] Database cleanup completed successfully!")

        except Exception as e:
            print(f"\n[-] Error during cleanup: {e}")
            await session.rollback()
            raise

    await engine.dispose()


# Import models after path is set
try:
    from app.models.company import Company
    from app.models.education import Education
    from app.models.project import Project
except ImportError:
    print("[-] Could not import models. Make sure to run from /app directory.")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(cleanup_database())
