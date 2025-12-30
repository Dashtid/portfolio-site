"""
Seed data script to populate database with initial portfolio content
"""

import asyncio
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine
from app.models.company import Company
from app.models.education import Education
from app.models.project import Project
from app.models.skill import Skill
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def clear_existing_data(session: AsyncSession):
    """Clear existing data from tables"""
    # Delete in order to respect foreign key constraints
    await session.execute(delete(Project))
    await session.execute(delete(Skill))
    await session.execute(delete(Company))
    await session.execute(delete(Education))
    await session.commit()
    logger.info("Cleared existing data")


async def seed_companies(session: AsyncSession):
    """Seed company/experience data"""
    companies = [
        {
            "name": "Hermes Medical Solutions",
            "title": "QA/RA & Security Specialist",
            "description": "QA/RA & Security Specialist at Hermes Medical Solutions, ensuring NIS2/ISO 27001 compliance, regulatory clearance, and V&V processes for nuclear medicine software solutions.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2024, 5, 1),
            "end_date": None,
            "website": "https://hermesmedical.com",
            "order_index": 1,
        },
        {
            "name": "Philips Healthcare",
            "title": "Incident Support Specialist, Nordics",
            "description": "Remote Service Engineer providing Level 1 support for Intellispace Portal (ISP) and Intellispace Cardiovascular (ISCV) systems across the Nordics.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2022, 3, 1),
            "end_date": datetime(2024, 5, 31),
            "website": "https://www.philips.com",
            "order_index": 2,
        },
        {
            "name": "Karolinska University Hospital",
            "title": "Biomedical Engineer, Medical Imaging and Physiology",
            "description": "First-line support for imaging equipment fleet, incident management for RIS/PACS systems, working with GE, Philips, and Siemens solutions.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2021, 6, 1),
            "end_date": datetime(2021, 12, 31),
            "website": "https://www.karolinska.se",
            "order_index": 3,
        },
        {
            "name": "SoftPro Medical Solutions",
            "title": "Master Thesis Student",
            "description": "Collaborated on thesis project to improve Quality Assurance system at radiology department by integrating inventory system with equipment workflow.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2020, 10, 1),
            "end_date": datetime(2021, 6, 30),
            "website": None,
            "order_index": 4,
        },
        {
            "name": "Södersjukhuset",
            "title": "Biomedical Engineer, Radiology Department",
            "description": "Managed IT systems at radiology department, evaluating supplier contracts, leading workgroups, and streamlining workflows.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2020, 6, 1),
            "end_date": datetime(2021, 6, 30),
            "website": "https://www.sodersjukhuset.se",
            "order_index": 5,
        },
        {
            "name": "Scania Group",
            "title": "Technician, Engine Analysis",
            "description": "Autonomous role managing troubleshooting processes, communicating across production chain, and creating documentation and work routines.",
            "location": "Södertälje, Sweden",
            "start_date": datetime(2016, 6, 1),
            "end_date": datetime(2016, 8, 31),
            "website": "https://www.scania.com",
            "order_index": 6,
        },
        {
            "name": "Finnish Defence Forces",
            "title": "Platoon Leader, 2nd Lieutenant",
            "description": "Marine commando platoon leader with day-to-day command of 150 soldiers and field operation command of 30 soldiers.",
            "location": "Tammisaari, Finland",
            "start_date": datetime(2014, 1, 1),
            "end_date": datetime(2015, 1, 31),
            "website": None,
            "order_index": 7,
        },
        {
            "name": "Scania Group (Early Career)",
            "title": "Technician, Engine Analysis",
            "description": "Junior role working in a team of engineers and technicians as part of second-line support, acquiring troubleshooting skills.",
            "location": "Södertälje, Sweden",
            "start_date": datetime(2012, 6, 1),
            "end_date": datetime(2012, 8, 31),
            "website": "https://www.scania.com",
            "order_index": 8,
        },
    ]

    added_count = 0
    for company_data in companies:
        # Check if company already exists by name
        result = await session.execute(select(Company).where(Company.name == company_data["name"]))
        if result.scalar_one_or_none() is None:
            company = Company(**company_data)
            session.add(company)
            added_count += 1
        else:
            logger.debug("Company '%s' already exists, skipping", company_data["name"])

    await session.commit()
    logger.info(
        "Seeded %d companies (%d already existed)", added_count, len(companies) - added_count
    )


async def seed_projects(session: AsyncSession):
    """Seed project data"""
    projects = [
        {
            "name": "Portfolio Migration",
            "description": "Modern portfolio website built with Vue 3 and FastAPI, featuring dynamic content management and GitHub integration",
            "technologies": "Vue 3, FastAPI, SQLAlchemy, PostgreSQL, Docker",
            "github_url": "https://github.com/Dashtid/portfolio-migration",
            "live_url": None,
            "featured": True,
            "order_index": 1,
        },
        {
            "name": "Medical Device Security Framework",
            "description": "Comprehensive security framework for medical devices implementing IEC 62304 and ISO 14971 standards",
            "technologies": "Python, Django, PostgreSQL, Docker, Kubernetes",
            "github_url": None,
            "live_url": None,
            "featured": True,
            "order_index": 2,
        },
        {
            "name": "Vulnerability Scanner Dashboard",
            "description": "Real-time vulnerability scanning and reporting dashboard for healthcare infrastructure",
            "technologies": "React, Node.js, MongoDB, ElasticSearch, Grafana",
            "github_url": None,
            "live_url": None,
            "featured": True,
            "order_index": 3,
        },
        {
            "name": "DICOM Processing Pipeline",
            "description": "Automated pipeline for processing and analyzing DICOM medical imaging files with AI/ML integration",
            "technologies": "Python, TensorFlow, PyDICOM, FastAPI, Redis",
            "github_url": None,
            "live_url": None,
            "featured": False,
            "order_index": 4,
        },
        {
            "name": "Compliance Automation Tool",
            "description": "Automated compliance checking tool for ISO 27001, GDPR, and medical device regulations",
            "technologies": "Python, Flask, SQLite, Docker",
            "github_url": None,
            "live_url": None,
            "featured": False,
            "order_index": 5,
        },
    ]

    for project_data in projects:
        project = Project(**project_data)
        session.add(project)

    await session.commit()
    logger.info("Seeded %d projects", len(projects))


async def seed_skills(session: AsyncSession):
    """Seed skills data - matches dashti.se content"""
    skills = [
        # Technical Skills (from dashti.se)
        {
            "name": "Windows Server",
            "category": "Technical",
            "proficiency": 85,
            "years_experience": 5,
            "order_index": 1,
        },
        {
            "name": "Unix/Linux",
            "category": "Technical",
            "proficiency": 85,
            "years_experience": 5,
            "order_index": 2,
        },
        {
            "name": "Docker",
            "category": "Technical",
            "proficiency": 90,
            "years_experience": 4,
            "order_index": 3,
        },
        {
            "name": "PowerShell",
            "category": "Technical",
            "proficiency": 85,
            "years_experience": 4,
            "order_index": 4,
        },
        {
            "name": "Bash",
            "category": "Technical",
            "proficiency": 85,
            "years_experience": 4,
            "order_index": 5,
        },
        {
            "name": "Python",
            "category": "Technical",
            "proficiency": 90,
            "years_experience": 5,
            "order_index": 6,
        },
        {
            "name": "Git",
            "category": "Technical",
            "proficiency": 90,
            "years_experience": 6,
            "order_index": 7,
        },
        # Domain Expertise (from dashti.se)
        {
            "name": "Cybersecurity",
            "category": "Domain Expertise",
            "proficiency": 90,
            "years_experience": 4,
            "order_index": 8,
        },
        {
            "name": "Medical Software",
            "category": "Domain Expertise",
            "proficiency": 90,
            "years_experience": 5,
            "order_index": 9,
        },
        {
            "name": "Quality Assurance",
            "category": "Domain Expertise",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 10,
        },
        {
            "name": "Regulatory Affairs",
            "category": "Domain Expertise",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 11,
        },
        {
            "name": "Healthcare IT",
            "category": "Domain Expertise",
            "proficiency": 90,
            "years_experience": 6,
            "order_index": 12,
        },
        {
            "name": "DICOM",
            "category": "Domain Expertise",
            "proficiency": 85,
            "years_experience": 5,
            "order_index": 13,
        },
        {
            "name": "PACS",
            "category": "Domain Expertise",
            "proficiency": 85,
            "years_experience": 5,
            "order_index": 14,
        },
        {
            "name": "ISO 27001",
            "category": "Domain Expertise",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 15,
        },
        {
            "name": "NIS2",
            "category": "Domain Expertise",
            "proficiency": 80,
            "years_experience": 2,
            "order_index": 16,
        },
        {
            "name": "EU AI Act",
            "category": "Domain Expertise",
            "proficiency": 75,
            "years_experience": 1,
            "order_index": 17,
        },
        {
            "name": "AI Compliance",
            "category": "Domain Expertise",
            "proficiency": 80,
            "years_experience": 2,
            "order_index": 18,
        },
        {
            "name": "MDR",
            "category": "Domain Expertise",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 19,
        },
        {
            "name": "GDPR",
            "category": "Domain Expertise",
            "proficiency": 85,
            "years_experience": 4,
            "order_index": 20,
        },
    ]

    for skill_data in skills:
        skill = Skill(**skill_data)
        session.add(skill)

    await session.commit()
    logger.info("Seeded %d skills", len(skills))


async def seed_education(session: AsyncSession):
    """Seed education data"""
    education_items = [
        {
            "institution": "KTH Royal Institute of Technology",
            "degree": "M.Sc. Medical Engineering",
            "field_of_study": "Medical Technology and Bioengineering",
            "start_date": datetime(2017, 8, 1),
            "end_date": datetime(2022, 6, 15),
            "location": "Stockholm, Sweden",
            "description": "Specialized in medical imaging, signal processing, and healthcare informatics. Thesis on AI-driven diagnostic systems.",
            "is_certification": False,
            "order": 1,
        },
        {
            "institution": "Lund University (LTH)",
            "degree": "B.Sc. Biomedical Engineering (Exchange)",
            "field_of_study": "Biomedical Engineering",
            "start_date": datetime(2020, 1, 1),
            "end_date": datetime(2021, 6, 1),
            "location": "Lund, Sweden",
            "description": "Exchange program focusing on medical device development and regulatory affairs.",
            "is_certification": False,
            "order": 2,
        },
        {
            "institution": "Företagsuniversitetet",
            "degree": "Certified ISO 27001 Lead Implementer",
            "field_of_study": "Information Security Management",
            "start_date": datetime(2023, 3, 1),
            "end_date": datetime(2023, 3, 5),
            "location": "Stockholm, Sweden",
            "description": "Intensive certification program for implementing and managing ISO 27001 ISMS.",
            "is_certification": True,
            "order": 3,
        },
        {
            "institution": "Microsoft",
            "degree": "Azure Security Engineer Associate (AZ-500)",
            "field_of_study": "Cloud Security",
            "start_date": datetime(2023, 6, 1),
            "end_date": datetime(2023, 6, 30),
            "location": "Online",
            "description": "Azure security services, identity management, and compliance features.",
            "is_certification": True,
            "order": 4,
        },
        {
            "institution": "EC-Council",
            "degree": "Certified Ethical Hacker (CEH)",
            "field_of_study": "Cybersecurity",
            "start_date": datetime(2022, 10, 1),
            "end_date": datetime(2022, 10, 31),
            "location": "Online",
            "description": "Ethical hacking methodologies, penetration testing, and vulnerability assessment.",
            "is_certification": True,
            "order": 5,
        },
    ]

    for edu_data in education_items:
        education = Education(**edu_data)
        session.add(education)

    await session.commit()
    logger.info("Seeded %d education items", len(education_items))


async def main():
    """Main seeding function"""
    logger.info("Starting database seeding...")

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session and seed data
    async with AsyncSession(engine) as session:
        try:
            # Seed all data
            await seed_companies(session)
            await seed_projects(session)
            await seed_skills(session)
            await seed_education(session)

            logger.info("Database seeding completed successfully")

        except Exception as e:
            logger.exception("Error during seeding: %s", e)
            await session.rollback()
            raise

    # Dispose of the engine
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
