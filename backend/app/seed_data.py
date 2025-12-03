"""
Seed data script to populate database with initial portfolio content
"""

import asyncio
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine
from app.models.company import Company
from app.models.education import Education
from app.models.project import Project
from app.models.skill import Skill


async def clear_existing_data(session: AsyncSession):
    """Clear existing data from tables"""
    # Delete in order to respect foreign key constraints
    await session.execute(select(Project).delete())
    await session.execute(select(Skill).delete())
    await session.execute(select(Company).delete())
    await session.execute(select(Education).delete())
    await session.commit()
    print("[OK] Cleared existing data")


async def seed_companies(session: AsyncSession):
    """Seed company/experience data"""
    companies = [
        {
            "name": "Hermes Medical Solutions",
            "title": "Security Specialist & System Developer",
            "description": "Leading cybersecurity initiatives for medical software systems, implementing ISO 27001 compliance, and developing secure healthcare solutions. Managing vulnerability assessments, security audits, and DevSecOps practices.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2022, 9, 1),
            "end_date": None,
            "website": "https://hermesmedical.com",
            "order_index": 1,
        },
        {
            "name": "KTH Royal Institute of Technology",
            "title": "Research Assistant - Medical Imaging",
            "description": "Developed machine learning models for medical image analysis, focusing on MRI and CT scan processing. Published research on deep learning applications in radiology.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2021, 1, 1),
            "end_date": datetime(2022, 6, 30),
            "website": "https://www.kth.se",
            "order_index": 2,
        },
        {
            "name": "Stockholm Innovation Hub",
            "title": "Tech Consultant",
            "description": "Provided technical consulting for healthcare startups, specializing in regulatory compliance and secure system architecture.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2020, 6, 1),
            "end_date": datetime(2020, 12, 31),
            "website": None,
            "order_index": 3,
        },
    ]

    for company_data in companies:
        company = Company(**company_data)
        session.add(company)

    await session.commit()
    print(f"[OK] Seeded {len(companies)} companies")


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
    print(f"[OK] Seeded {len(projects)} projects")


async def seed_skills(session: AsyncSession):
    """Seed skills data"""
    skills = [
        # Programming Languages
        {
            "name": "Python",
            "category": "Programming",
            "proficiency": 95,
            "years_experience": 6,
            "order_index": 1,
        },
        {
            "name": "JavaScript/TypeScript",
            "category": "Programming",
            "proficiency": 85,
            "years_experience": 4,
            "order_index": 2,
        },
        {
            "name": "SQL",
            "category": "Programming",
            "proficiency": 80,
            "years_experience": 5,
            "order_index": 3,
        },
        {
            "name": "Bash/PowerShell",
            "category": "Programming",
            "proficiency": 75,
            "years_experience": 4,
            "order_index": 4,
        },
        # Frameworks
        {
            "name": "FastAPI",
            "category": "Frameworks",
            "proficiency": 90,
            "years_experience": 3,
            "order_index": 5,
        },
        {
            "name": "Vue.js",
            "category": "Frameworks",
            "proficiency": 80,
            "years_experience": 2,
            "order_index": 6,
        },
        {
            "name": "Django",
            "category": "Frameworks",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 7,
        },
        {
            "name": "React",
            "category": "Frameworks",
            "proficiency": 75,
            "years_experience": 2,
            "order_index": 8,
        },
        # DevOps & Cloud
        {
            "name": "Docker",
            "category": "DevOps",
            "proficiency": 90,
            "years_experience": 4,
            "order_index": 9,
        },
        {
            "name": "Kubernetes",
            "category": "DevOps",
            "proficiency": 80,
            "years_experience": 3,
            "order_index": 10,
        },
        {
            "name": "Azure",
            "category": "Cloud",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 11,
        },
        {
            "name": "GitHub Actions",
            "category": "DevOps",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 12,
        },
        # Security
        {
            "name": "Security Auditing",
            "category": "Security",
            "proficiency": 95,
            "years_experience": 4,
            "order_index": 13,
        },
        {
            "name": "Vulnerability Assessment",
            "category": "Security",
            "proficiency": 90,
            "years_experience": 4,
            "order_index": 14,
        },
        {
            "name": "ISO 27001",
            "category": "Security",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 15,
        },
        {
            "name": "OWASP",
            "category": "Security",
            "proficiency": 85,
            "years_experience": 3,
            "order_index": 16,
        },
        # Medical/Healthcare
        {
            "name": "IEC 62304",
            "category": "Medical",
            "proficiency": 80,
            "years_experience": 2,
            "order_index": 17,
        },
        {
            "name": "DICOM",
            "category": "Medical",
            "proficiency": 75,
            "years_experience": 2,
            "order_index": 18,
        },
        {
            "name": "HL7/FHIR",
            "category": "Medical",
            "proficiency": 70,
            "years_experience": 2,
            "order_index": 19,
        },
    ]

    for skill_data in skills:
        skill = Skill(**skill_data)
        session.add(skill)

    await session.commit()
    print(f"[OK] Seeded {len(skills)} skills")


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
    print(f"[OK] Seeded {len(education_items)} education items")


async def main():
    """Main seeding function"""
    print("[*] Starting database seeding...")

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

            print("[+] Database seeding completed successfully!")

        except Exception as e:
            print(f"[-] Error during seeding: {e}")
            await session.rollback()
            raise

    # Dispose of the engine
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
