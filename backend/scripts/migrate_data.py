#!/usr/bin/env python
"""
One-time data migration script for portfolio content.

Applies hardcoded company/education/skill data corrections that were previously
running on every application startup (~500 lines in main.py lifespan).

Usage:
    cd backend
    python -m scripts.migrate_data

This script is idempotent — safe to run multiple times. Each migration checks
current state before applying changes.
"""

import asyncio
import logging
import uuid
from datetime import date

from sqlalchemy import delete, select, update
from sqlalchemy.exc import OperationalError

from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.education import Education
from app.models.skill import Skill

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


async def cleanup_duplicate_scania_entries() -> None:
    """Remove duplicate Scania Group entries, keeping one entry per year bucket (2016, 2012)."""

    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Company).where(
                    Company.name.in_(["Scania Group", "Scania Group (Early Career)"])
                )
            )
            scania_entries = result.scalars().all()

            if not scania_entries:
                return

            year_2016 = [e for e in scania_entries if e.start_date and e.start_date.year == 2016]
            year_2012 = [e for e in scania_entries if e.start_date and e.start_date.year == 2012]

            ids_to_keep: set[str] = set()
            if year_2016:
                canonical = next((e for e in year_2016 if e.order_index == 6), year_2016[0])
                ids_to_keep.add(canonical.id)
            if year_2012:
                canonical = next((e for e in year_2012 if e.order_index == 8), year_2012[0])
                ids_to_keep.add(canonical.id)

            for entry in scania_entries:
                if not entry.start_date and entry.order_index in (6, 8):
                    ids_to_keep.add(entry.id)

            ids_to_delete = [e.id for e in scania_entries if e.id not in ids_to_keep]
            if ids_to_delete:
                logger.warning(
                    "Found %d Scania entries, removing %d duplicate(s)",
                    len(scania_entries),
                    len(ids_to_delete),
                )
                await session.execute(delete(Company).where(Company.id.in_(ids_to_delete)))
                await session.commit()
    except OperationalError:
        pass


async def migrate_company_data() -> None:
    """Update company dates, titles, and detailed content from LinkedIn data."""

    await cleanup_duplicate_scania_entries()

    company_updates = {
        "Hermes Medical Solutions": ("QA/RA & Security Specialist", date(2024, 5, 1), None, 1),
        "Philips Healthcare": (
            "Incident Support Specialist, Nordics",
            date(2022, 3, 1),
            date(2024, 5, 31),
            2,
        ),
        "Karolinska University Hospital": (
            "Biomedical Engineer, Medical Imaging and Physiology",
            date(2021, 6, 1),
            date(2021, 12, 31),
            3,
        ),
        "SoftPro Medical Solutions": (
            "Master Thesis Student",
            date(2020, 10, 1),
            date(2021, 6, 30),
            4,
        ),
        "Södersjukhuset - SÖS": (
            "Biomedical Engineer, Radiology Department",
            date(2020, 6, 1),
            date(2021, 6, 30),
            5,
        ),
        "Södersjukhuset": (
            "Biomedical Engineer, Radiology Department",
            date(2020, 6, 1),
            date(2021, 6, 30),
            5,
        ),
        "Scania Engines": ("Technician, Engine Analysis", date(2016, 6, 1), date(2016, 8, 31), 6),
        "Finnish Defence Forces": (
            "Platoon Leader, 2nd Lieutenant",
            date(2014, 1, 1),
            date(2015, 1, 31),
            7,
        ),
    }

    try:
        async with AsyncSessionLocal() as session:
            for name, (title, start_date, end_date, order_index) in company_updates.items():
                try:
                    stmt = (
                        update(Company)
                        .where(Company.name == name)
                        .values(
                            title=title,
                            start_date=start_date,
                            end_date=end_date,
                            order_index=order_index,
                        )
                    )
                    result = await session.execute(stmt)
                    if result.rowcount > 0:
                        logger.info("Updated company: %s", name)
                except Exception as e:
                    logger.warning("Company update failed for %s: %s", name, e)

            # Rename Scania Engines -> Scania Group
            stmt = (
                update(Company).where(Company.name == "Scania Engines").values(name="Scania Group")
            )
            result = await session.execute(stmt)
            if result.rowcount > 0:
                logger.info("Renamed Scania Engines to Scania Group")

            # Update Scania 2016 entry
            stmt = (
                update(Company)
                .where(Company.name == "Scania Group", Company.start_date == date(2016, 6, 1))
                .values(
                    title="Technician, Engine Analysis",
                    description="Autonomous role managing troubleshooting processes, communicating across production chain, and creating documentation and work routines.",
                    end_date=date(2016, 8, 31),
                    order_index=6,
                    logo_url="/images/scania.svg",
                    video_url="https://www.youtube.com/embed/Rm6grXvyX6I",
                    video_title="Manufacturing Process at the Truck Factory",
                )
            )
            await session.execute(stmt)

            # Update Scania 2012 rename
            stmt = (
                update(Company)
                .where(Company.name == "Scania Group (Early Career)")
                .values(name="Scania Group", logo_url="/images/scania.svg")
            )
            await session.execute(stmt)

            # Fix Scania 2012 dates if corrupted
            stmt = (
                update(Company)
                .where(Company.name == "Scania Group", Company.order_index == 8)
                .values(
                    start_date=date(2012, 6, 1),
                    end_date=date(2012, 8, 31),
                    title="Technician, Engine Analysis",
                    description="Junior role working in a team of engineers and technicians as part of second-line support, acquiring troubleshooting skills.",
                )
            )
            await session.execute(stmt)

            # Create Scania 2012 if it doesn't exist
            result = await session.execute(
                select(Company).where(
                    Company.start_date == date(2012, 6, 1), Company.name == "Scania Group"
                )
            )
            if result.scalars().first() is None:
                result = await session.execute(
                    select(Company).where(Company.name == "Scania Group (Early Career)")
                )
                if result.scalars().first() is None:
                    session.add(
                        Company(
                            id=str(uuid.uuid4()),
                            name="Scania Group",
                            title="Technician, Engine Analysis",
                            description="Junior role working in a team of engineers and technicians as part of second-line support, acquiring troubleshooting skills.",
                            location="Södertälje, Sweden",
                            start_date=date(2012, 6, 1),
                            end_date=date(2012, 8, 31),
                            website="https://www.scania.com",
                            logo_url="/images/scania.svg",
                            order_index=8,
                        )
                    )
                    logger.info("Added Scania 2012 entry")

            # Fix Finnish Defence Forces location
            stmt = (
                update(Company)
                .where(Company.name == "Finnish Defence Forces")
                .values(location="Dragsvik, Finland")
            )
            await session.execute(stmt)

            await session.commit()
            logger.info("Company data migration completed")
    except OperationalError:
        pass


async def migrate_education_data() -> None:
    """Update education dates and order from LinkedIn data."""

    education_updates = {
        "KTH Royal Institute of Technology": (date(2018, 8, 1), date(2021, 6, 30), 1, None, ...),
        "Lund University": (date(2015, 8, 1), date(2018, 6, 30), 2, None, ...),
        "Företagsuniversitet": (
            date(2024, 10, 1),
            date(2024, 12, 31),
            3,
            "https://foretagsuniversitetet-yh.trueoriginal.com/utbildningsbevis-226768-datacourse-select-title-4436/?ref=linkedin-profile&lang=en",
            None,
        ),
        "CompTIA": (None, None, 4, None, "Ongoing certification."),
    }

    async with AsyncSessionLocal() as session:
        for institution, (
            start_date,
            end_date,
            order_index,
            cert_url,
            description,
        ) in education_updates.items():
            try:
                update_values: dict[str, object] = {"order_index": order_index}
                if start_date is not None:
                    update_values["start_date"] = start_date
                if end_date is not None:
                    update_values["end_date"] = end_date
                if cert_url:
                    update_values["certificate_url"] = cert_url
                if description is not ...:
                    update_values["description"] = description

                stmt = (
                    update(Education)
                    .where(Education.institution == institution)
                    .values(**update_values)
                )
                result = await session.execute(stmt)
                if result.rowcount > 0:
                    logger.info("Updated education: %s", institution)
            except Exception as e:
                logger.warning("Education update failed for %s: %s", institution, e)

        await session.commit()
        logger.info("Education data migration completed")


async def migrate_skill_proficiency() -> None:
    """Convert skill proficiency values from 1-5 scale to 0-100 scale."""

    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(Skill).where(Skill.proficiency_level <= 5, Skill.proficiency_level > 0)
            )
            old_scale_skills = result.scalars().all()

            if old_scale_skills:
                for skill in old_scale_skills:
                    new_value = skill.proficiency_level * 20
                    stmt = (
                        update(Skill)
                        .where(Skill.id == skill.id)
                        .values(proficiency_level=new_value)
                    )
                    await session.execute(stmt)
                    logger.info(
                        "Updated skill %s proficiency: %d -> %d",
                        skill.name,
                        skill.proficiency_level,
                        new_value,
                    )
                await session.commit()
                logger.info("Skill proficiency migration completed")
        except Exception as e:
            logger.warning("Skill proficiency migration skipped: %s", e)


async def main() -> None:
    """Run all data migrations."""
    logger.info("Starting data migrations...")
    await migrate_company_data()
    await migrate_education_data()
    await migrate_skill_proficiency()
    logger.info("All data migrations completed.")


if __name__ == "__main__":
    asyncio.run(main())
