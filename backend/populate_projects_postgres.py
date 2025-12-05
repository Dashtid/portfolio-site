"""
Populate PostgreSQL database with Projects data

This script populates the production PostgreSQL database on Fly.io with
GitHub projects extracted from dashti.se

Run on Fly.io:
    flyctl ssh console -a dashti-portfolio-backend
    cd /app
    python populate_projects_postgres.py
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models.project import Project

# Projects data extracted from dashti.se GitHub section
# Note: technologies should be a list, NOT json.dumps() - SQLAlchemy JSON column handles serialization
PROJECTS_DATA = [
    {
        "id": str(uuid.uuid4()),
        "name": "DICOM Fuzzer",
        "description": "Security fuzzing tool for DICOM medical imaging protocol. Tests DICOM implementations for vulnerabilities and edge cases in healthcare imaging systems.",
        "detailed_description": "A comprehensive security testing tool designed to identify vulnerabilities in DICOM (Digital Imaging and Communications in Medicine) protocol implementations. Uses fuzzing techniques to send malformed or unexpected data to DICOM servers, helping identify potential security issues in medical imaging systems before they can be exploited.",
        "technologies": ["Python", "DICOM", "Security", "Fuzzing", "Healthcare"],
        "github_url": "https://github.com/Dashtid/dicom-fuzzer",
        "live_url": None,
        "image_url": "/images/projects/dicom-fuzzer.png",
        "featured": True,
        "order_index": 1,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Biomedical AI",
        "description": "Medical image segmentation using U-Net architectures. Deep learning models for automated analysis of medical imaging data.",
        "detailed_description": "Implementation of U-Net and other deep learning architectures for medical image segmentation tasks. Includes pre-processing pipelines for various medical imaging modalities, model training utilities, and evaluation metrics specific to healthcare applications.",
        "technologies": [
            "Python",
            "TensorFlow",
            "PyTorch",
            "U-Net",
            "Medical Imaging",
            "Deep Learning",
        ],
        "github_url": "https://github.com/Dashtid/biomedical-ai",
        "live_url": None,
        "image_url": "/images/projects/biomedical-ai.png",
        "featured": True,
        "order_index": 2,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Sysadmin Toolkit",
        "description": "System administration automation scripts for Windows and Linux environments. Streamlines common IT operations and maintenance tasks.",
        "detailed_description": "A collection of PowerShell and Bash scripts for automating system administration tasks across Windows and Linux platforms. Includes user management, backup automation, system monitoring, log analysis, and security hardening scripts.",
        "technologies": ["PowerShell", "Bash", "Python", "Windows Server", "Linux", "Automation"],
        "github_url": "https://github.com/Dashtid/windows-linux-sysadmin-toolkit",
        "live_url": None,
        "image_url": "/images/projects/sysadmin-toolkit.png",
        "featured": True,
        "order_index": 3,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Defensive Toolkit",
        "description": "Blue team security toolkit with SIEM rules, hardening scripts, and monitoring configurations for enterprise defense.",
        "detailed_description": "Comprehensive defensive security toolkit designed for blue team operations. Includes SIEM detection rules, system hardening scripts, security monitoring dashboards, incident response playbooks, and threat hunting queries for various platforms.",
        "technologies": ["SIEM", "Splunk", "PowerShell", "Python", "Security", "Blue Team"],
        "github_url": "https://github.com/Dashtid/defensive-toolkit",
        "live_url": None,
        "image_url": "/images/projects/defensive-toolkit.png",
        "featured": False,
        "order_index": 4,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Offensive Toolkit",
        "description": "Red team penetration testing tools and scripts for authorized security assessments and vulnerability research.",
        "detailed_description": "Collection of penetration testing tools and scripts for authorized security assessments. Includes reconnaissance utilities, exploitation helpers, post-exploitation scripts, and reporting tools. Designed for ethical security testing and research purposes only.",
        "technologies": ["Python", "Bash", "Security", "Penetration Testing", "Red Team"],
        "github_url": "https://github.com/Dashtid/offensive-toolkit",
        "live_url": None,
        "image_url": "/images/projects/offensive-toolkit.png",
        "featured": False,
        "order_index": 5,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Portfolio Site",
        "description": "Professional portfolio website built with Vue 3 and FastAPI. Features dynamic content management, GitHub OAuth, and CI/CD deployment.",
        "detailed_description": "Modern, production-ready portfolio website with dynamic content management, authentication, and comprehensive testing. Built with Vue 3 + TypeScript frontend and FastAPI + PostgreSQL backend. Deployed on Vercel (frontend) and Fly.io (backend) with automated CI/CD pipelines.",
        "technologies": [
            "Vue.js",
            "TypeScript",
            "FastAPI",
            "Python",
            "PostgreSQL",
            "Docker",
            "CI/CD",
        ],
        "github_url": "https://github.com/Dashtid/portfolio-site",
        "live_url": "https://portfolio-site-jade-five.vercel.app",
        "image_url": "/images/projects/portfolio-site.png",
        "featured": True,
        "order_index": 6,
    },
]


async def populate_projects():
    """Populate projects table with GitHub projects data"""

    print("=" * 70)
    print("PostgreSQL Projects Population Script")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        # Check current count
        result = await db.execute(select(Project))
        existing = result.scalars().all()
        print(f"[INFO] Current projects in database: {len(existing)}")

        # Clear existing projects
        if existing:
            print("[INFO] Clearing existing projects...")
            await db.execute(delete(Project))
            await db.commit()
            print("[OK] Cleared existing projects")

        # Insert new projects
        print()
        print("[INFO] Inserting projects...")
        print("-" * 70)

        for project_data in PROJECTS_DATA:
            project = Project(
                id=project_data["id"],
                name=project_data["name"],
                description=project_data["description"],
                detailed_description=project_data["detailed_description"],
                technologies=project_data["technologies"],
                github_url=project_data["github_url"],
                live_url=project_data["live_url"],
                image_url=project_data["image_url"],
                featured=project_data["featured"],
                order_index=project_data["order_index"],
            )
            db.add(project)
            featured_tag = " [FEATURED]" if project_data["featured"] else ""
            print(f"  [+] {project_data['name']}{featured_tag}")

        await db.commit()
        print("-" * 70)
        print()

        # Verification
        result = await db.execute(select(Project).order_by(Project.order_index))
        projects = result.scalars().all()

        print("=" * 70)
        print("Verification - Projects in database:")
        print("-" * 70)
        for p in projects:
            featured = "[*]" if p.featured else "   "
            print(f"{featured} {p.order_index}. {p.name}")
        print("-" * 70)
        print(
            f"Total: {len(projects)} projects ({sum(1 for p in projects if p.featured)} featured)"
        )
        print("=" * 70)
        print()
        print("[SUCCESS] Projects populated successfully!")
        print("API endpoint: /api/v1/projects/")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(populate_projects())
