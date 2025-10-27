"""
Initialize database and create tables
"""

import asyncio
from datetime import date

from app.database import AsyncSessionLocal, Base, engine
from app.models import Company, Project, Skill


async def init_db():
    """Create all tables"""
    async with engine.begin() as conn:
        # Drop all tables (for development only)
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("[OK] Database tables created successfully!")


async def seed_data():
    """Add initial seed data"""
    async with AsyncSessionLocal() as session:
        try:
            # Add companies
            companies = [
                Company(
                    name="Hermes Medical Solutions",
                    title="DevOps Engineer",
                    description="Working on medical imaging software and infrastructure automation. Implementing CI/CD pipelines, containerization with Docker/Kubernetes, and monitoring solutions.",
                    location="Stockholm, Sweden",
                    start_date=date(2023, 1, 1),
                    end_date=None,  # Current job
                    logo_url="/images/hermes-logo.png",
                    website="https://www.hermesmedical.com",
                    order_index=1,
                ),
                Company(
                    name="Scania",
                    title="IT Consultant",
                    description="Developed automation solutions and improved IT infrastructure. Worked with Azure DevOps, PowerShell scripting, and system integration.",
                    location="Södertälje, Sweden",
                    start_date=date(2021, 6, 1),
                    end_date=date(2022, 12, 31),
                    logo_url="/images/scania-logo.png",
                    website="https://www.scania.com",
                    order_index=2,
                ),
                Company(
                    name="Philips",
                    title="Technical Support Engineer",
                    description="Provided technical support for medical devices and healthcare IT systems. Troubleshooting, customer training, and system maintenance.",
                    location="Stockholm, Sweden",
                    start_date=date(2019, 3, 1),
                    end_date=date(2021, 5, 31),
                    logo_url="/images/philips-logo.png",
                    website="https://www.philips.com",
                    order_index=3,
                ),
            ]

            for company in companies:
                session.add(company)

            # Add skills
            skills = [
                # Languages
                Skill(
                    name="Python",
                    category="language",
                    proficiency=5,
                    years_experience=5.0,
                    order_index=1,
                ),
                Skill(
                    name="JavaScript",
                    category="language",
                    proficiency=4,
                    years_experience=4.0,
                    order_index=2,
                ),
                Skill(
                    name="TypeScript",
                    category="language",
                    proficiency=4,
                    years_experience=2.0,
                    order_index=3,
                ),
                Skill(
                    name="PowerShell",
                    category="language",
                    proficiency=5,
                    years_experience=6.0,
                    order_index=4,
                ),
                Skill(
                    name="Bash",
                    category="language",
                    proficiency=4,
                    years_experience=4.0,
                    order_index=5,
                ),
                # Frameworks
                Skill(
                    name="FastAPI",
                    category="framework",
                    proficiency=4,
                    years_experience=1.0,
                    order_index=6,
                ),
                Skill(
                    name="Vue.js",
                    category="framework",
                    proficiency=3,
                    years_experience=1.0,
                    order_index=7,
                ),
                Skill(
                    name="React",
                    category="framework",
                    proficiency=3,
                    years_experience=2.0,
                    order_index=8,
                ),
                # Tools
                Skill(
                    name="Docker",
                    category="tool",
                    proficiency=5,
                    years_experience=4.0,
                    order_index=9,
                ),
                Skill(
                    name="Kubernetes",
                    category="tool",
                    proficiency=4,
                    years_experience=3.0,
                    order_index=10,
                ),
                Skill(
                    name="Git", category="tool", proficiency=5, years_experience=6.0, order_index=11
                ),
                Skill(
                    name="Azure DevOps",
                    category="tool",
                    proficiency=5,
                    years_experience=4.0,
                    order_index=12,
                ),
                Skill(
                    name="Terraform",
                    category="tool",
                    proficiency=3,
                    years_experience=2.0,
                    order_index=13,
                ),
                # Databases
                Skill(
                    name="PostgreSQL",
                    category="database",
                    proficiency=4,
                    years_experience=3.0,
                    order_index=14,
                ),
                Skill(
                    name="MongoDB",
                    category="database",
                    proficiency=3,
                    years_experience=2.0,
                    order_index=15,
                ),
                Skill(
                    name="Redis",
                    category="database",
                    proficiency=3,
                    years_experience=2.0,
                    order_index=16,
                ),
            ]

            for skill in skills:
                session.add(skill)

            # Save first company to add projects to it
            await session.flush()
            hermes = companies[0]

            # Add projects
            projects = [
                Project(
                    name="Infrastructure Automation Platform",
                    description="Automated deployment and monitoring solution using Kubernetes, Terraform, and GitHub Actions",
                    technologies=["Kubernetes", "Terraform", "Python", "Prometheus"],
                    github_url="https://github.com/yourusername/infra-automation",
                    company_id=hermes.id,
                    featured=True,
                    order_index=1,
                ),
                Project(
                    name="CI/CD Pipeline Framework",
                    description="Comprehensive CI/CD pipeline using Azure DevOps, Docker, and automated testing",
                    technologies=["Azure DevOps", "Docker", "PowerShell", "YAML"],
                    company_id=hermes.id,
                    featured=True,
                    order_index=2,
                ),
                Project(
                    name="Portfolio Website",
                    description="Modern portfolio website built with Vue 3 and FastAPI",
                    technologies=["Vue.js", "FastAPI", "PostgreSQL", "Docker"],
                    github_url="https://github.com/yourusername/portfolio",
                    live_url="https://dashti.se",
                    featured=True,
                    order_index=3,
                ),
            ]

            for project in projects:
                session.add(project)

            # Commit all changes
            await session.commit()
            print("[OK] Seed data added successfully!")

        except Exception as e:
            await session.rollback()
            print(f"[ERROR] Failed to seed data: {e}")
            raise


async def main():
    """Initialize database and seed data"""
    print("Initializing database...")
    await init_db()
    print("Adding seed data...")
    await seed_data()
    print("[OK] Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())
