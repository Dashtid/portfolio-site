"""
Tests for seed_data.py - database seeding functionality
"""

import pytest
from sqlalchemy import select

from app.database import Base
from app.models.company import Company
from app.models.education import Education
from app.models.project import Project
from app.models.skill import Skill
from app.seed_data import (
    clear_existing_data,
    seed_companies,
    seed_education,
    seed_projects,
    seed_skills,
)
from tests.conftest import TestSessionLocal, test_engine


@pytest.fixture
async def db_session():
    """Create database tables and provide a session for testing."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


class TestSeedCompanies:
    """Tests for seed_companies function."""

    @pytest.mark.asyncio
    async def test_seed_companies_creates_correct_count(self, db_session):
        """Test that seed_companies creates exactly 8 companies."""
        await seed_companies(db_session)

        result = await db_session.execute(select(Company))
        companies = result.scalars().all()
        assert len(companies) == 8

    @pytest.mark.asyncio
    async def test_seed_companies_idempotent(self, db_session):
        """Test that running seed_companies twice doesn't duplicate data."""
        await seed_companies(db_session)
        await seed_companies(db_session)

        result = await db_session.execute(select(Company))
        companies = result.scalars().all()
        assert len(companies) == 8

    @pytest.mark.asyncio
    async def test_seed_companies_has_required_fields(self, db_session):
        """Test that seeded companies have all required fields."""
        await seed_companies(db_session)

        result = await db_session.execute(select(Company))
        companies = result.scalars().all()

        for company in companies:
            assert company.name is not None
            assert company.title is not None
            assert company.description is not None
            assert company.location is not None
            assert company.start_date is not None
            assert company.order_index is not None


class TestSeedProjects:
    """Tests for seed_projects function."""

    @pytest.mark.asyncio
    async def test_seed_projects_creates_correct_count(self, db_session):
        """Test that seed_projects creates exactly 5 projects."""
        await seed_projects(db_session)

        result = await db_session.execute(select(Project))
        projects = result.scalars().all()
        assert len(projects) == 5

    @pytest.mark.asyncio
    async def test_seed_projects_has_required_fields(self, db_session):
        """Test that seeded projects have all required fields."""
        await seed_projects(db_session)

        result = await db_session.execute(select(Project))
        projects = result.scalars().all()

        for project in projects:
            assert project.name is not None
            assert project.description is not None
            assert project.technologies is not None
            assert project.order_index is not None


class TestSeedSkills:
    """Tests for seed_skills function."""

    @pytest.mark.asyncio
    async def test_seed_skills_creates_correct_count(self, db_session):
        """Test that seed_skills creates exactly 20 skills."""
        await seed_skills(db_session)

        result = await db_session.execute(select(Skill))
        skills = result.scalars().all()
        assert len(skills) == 20

    @pytest.mark.asyncio
    async def test_seed_skills_column_mapping(self, db_session):
        """Test that skill data maps to correct model columns.

        This test validates that proficiency_level and years_of_experience
        are correctly set (not None) on created skills.
        """
        await seed_skills(db_session)

        result = await db_session.execute(select(Skill))
        skills = result.scalars().all()

        for skill in skills:
            assert skill.name is not None
            assert skill.category is not None
            assert skill.proficiency_level is not None, (
                f"Skill '{skill.name}' has None proficiency_level - "
                "check seed_data.py column mapping"
            )
            assert skill.years_of_experience is not None, (
                f"Skill '{skill.name}' has None years_of_experience - "
                "check seed_data.py column mapping"
            )
            assert skill.order_index is not None

    @pytest.mark.asyncio
    async def test_seed_skills_proficiency_range(self, db_session):
        """Test that proficiency levels are within valid range (0-100)."""
        await seed_skills(db_session)

        result = await db_session.execute(select(Skill))
        skills = result.scalars().all()

        for skill in skills:
            if skill.proficiency_level is not None:
                assert 0 <= skill.proficiency_level <= 100, (
                    f"Skill '{skill.name}' has invalid proficiency_level: {skill.proficiency_level}"
                )


class TestSeedEducation:
    """Tests for seed_education function."""

    @pytest.mark.asyncio
    async def test_seed_education_creates_correct_count(self, db_session):
        """Test that seed_education creates exactly 5 education records."""
        await seed_education(db_session)

        result = await db_session.execute(select(Education))
        education_items = result.scalars().all()
        assert len(education_items) == 5

    @pytest.mark.asyncio
    async def test_seed_education_has_required_fields(self, db_session):
        """Test that seeded education items have all required fields."""
        await seed_education(db_session)

        result = await db_session.execute(select(Education))
        education_items = result.scalars().all()

        for edu in education_items:
            assert edu.institution is not None
            assert edu.degree is not None
            assert edu.field_of_study is not None
            assert edu.start_date is not None
            assert edu.end_date is not None
            assert edu.location is not None


class TestClearExistingData:
    """Tests for clear_existing_data function."""

    @pytest.mark.asyncio
    async def test_clear_existing_data_removes_all_records(self, db_session):
        """Test that clear_existing_data removes all records from all tables."""
        # First seed data
        await seed_companies(db_session)
        await seed_projects(db_session)
        await seed_skills(db_session)
        await seed_education(db_session)

        # Verify data exists
        companies = (await db_session.execute(select(Company))).scalars().all()
        assert len(companies) > 0

        # Clear all data
        await clear_existing_data(db_session)

        # Verify all tables are empty
        companies = (await db_session.execute(select(Company))).scalars().all()
        projects = (await db_session.execute(select(Project))).scalars().all()
        skills = (await db_session.execute(select(Skill))).scalars().all()
        education = (await db_session.execute(select(Education))).scalars().all()

        assert len(companies) == 0
        assert len(projects) == 0
        assert len(skills) == 0
        assert len(education) == 0

    @pytest.mark.asyncio
    async def test_clear_existing_data_respects_fk_constraints(self, db_session):
        """Test that clear_existing_data deletes in correct order for FK constraints."""
        # Seed all data
        await seed_companies(db_session)
        await seed_projects(db_session)
        await seed_skills(db_session)
        await seed_education(db_session)

        # This should not raise FK constraint errors
        await clear_existing_data(db_session)

        # If we get here without exception, FK order is correct


class TestSeedDataIntegration:
    """Integration tests for full seeding workflow."""

    @pytest.mark.asyncio
    async def test_full_seed_workflow(self, db_session):
        """Test complete seeding of all data types."""
        await seed_companies(db_session)
        await seed_projects(db_session)
        await seed_skills(db_session)
        await seed_education(db_session)

        # Verify all data was created
        companies = (await db_session.execute(select(Company))).scalars().all()
        projects = (await db_session.execute(select(Project))).scalars().all()
        skills = (await db_session.execute(select(Skill))).scalars().all()
        education = (await db_session.execute(select(Education))).scalars().all()

        assert len(companies) == 8
        assert len(projects) == 5
        assert len(skills) == 20
        assert len(education) == 5

    @pytest.mark.asyncio
    async def test_reseed_after_clear(self, db_session):
        """Test that data can be reseeded after clearing."""
        # First seed
        await seed_companies(db_session)
        await seed_projects(db_session)
        await seed_skills(db_session)
        await seed_education(db_session)

        # Clear
        await clear_existing_data(db_session)

        # Reseed
        await seed_companies(db_session)
        await seed_projects(db_session)
        await seed_skills(db_session)
        await seed_education(db_session)

        # Verify
        companies = (await db_session.execute(select(Company))).scalars().all()
        assert len(companies) == 8
