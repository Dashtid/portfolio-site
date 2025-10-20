"""
Migrate real content from original portfolio-site to database
This script populates the database with actual portfolio data
"""
import asyncio
import sys
from pathlib import Path

# Add app to path
sys.path.append(str(Path(__file__).parent))

from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.education import Education
from sqlalchemy import select, delete


async def clear_existing_data():
    """Clear existing sample data"""
    async with AsyncSessionLocal() as db:
        try:
            # Delete all existing companies
            await db.execute(delete(Company))
            # Delete all existing education
            await db.execute(delete(Education))
            await db.commit()
            print("[+] Cleared existing data")
        except Exception as e:
            print(f"[-] Error clearing data: {e}")
            await db.rollback()


async def populate_companies():
    """Populate companies/experience from original portfolio"""
    async with AsyncSessionLocal() as db:
        try:
            companies = [
                {
                    "name": "Hermes Medical Solutions",
                    "title": "QA/RA & Security Specialist",
                    "description": "QA/RA & Security Specialist at Hermes Medical Solutions, ensuring NIS2/ISO 27001 compliance, regulatory clearance, and V&V processes for nuclear medicine software solutions.",
                    "location": "Stockholm, Sweden",
                    "start_date": "2022-01-01",
                    "end_date": None,
                    "website": "https://hermesmedical.com",
                    "order_index": 1
                },
                {
                    "name": "Scania Engines",
                    "title": "Engineering Role",
                    "description": "Contributed to troubleshooting processes in an engineering role at Scania Södertälje, addressing cases, communicating with production teams including manufacturing and construction, and assisting with the creation of documentation and work routines.",
                    "location": "Södertälje, Sweden",
                    "start_date": "2020-01-01",
                    "end_date": "2021-12-31",
                    "website": "https://www.scania.com",
                    "order_index": 2
                },
                {
                    "name": "Finnish Defence Forces",
                    "title": "Platoon Leader (2nd Lieutenant)",
                    "description": "Platoon Leader (2nd Lieutenant) in the Finnish Defence Forces' marine commandos, responsible for the day-to-day command of 150 soldiers and field operation command of 30 soldiers, with intensive training in leadership, stress resilience, and organizational skills.",
                    "location": "Finland",
                    "start_date": "2018-06-01",
                    "end_date": "2019-06-01",
                    "website": None,
                    "order_index": 3
                },
                {
                    "name": "Södersjukhuset - SÖS",
                    "title": "Radiology Support",
                    "description": "Supported radiology equipment and IT system management in a radiology department, contributing to contract evaluations, participating in workgroups, analyzing IT systems for operational improvements, assisting with workflow optimization, and maintaining system documentation.",
                    "location": "Stockholm, Sweden",
                    "start_date": "2019-01-01",
                    "end_date": "2020-06-01",
                    "website": None,
                    "order_index": 4
                },
                {
                    "name": "SoftPro Medical Solutions",
                    "title": "Master Thesis Student",
                    "description": "Master Thesis Student at SoftPro Medical Solutions, integrating Medusa inventory management with radiology workflows and optimizing quality assurance processes for medical equipment.",
                    "location": "Stockholm, Sweden",
                    "start_date": "2020-01-01",
                    "end_date": "2020-06-01",
                    "website": None,
                    "order_index": 5
                },
                {
                    "name": "Karolinska University Hospital",
                    "title": "Biomedical Engineer",
                    "description": "Biomedical Engineer at Karolinska University Hospital, providing first-line support for imaging equipment and managing RIS/PACS incidents, gaining expertise in clinical workflows, system architecture, DICOM/HL7, Active Directory, and ITIL.",
                    "location": "Stockholm, Sweden",
                    "start_date": "2017-06-01",
                    "end_date": "2018-12-31",
                    "website": None,
                    "order_index": 6
                },
                {
                    "name": "Philips Healthcare",
                    "title": "Remote Service Engineer",
                    "description": "Remote Service Engineer providing Level 1 support for Intellispace Portal (ISP) and Intellispace Cardiovascular (ISCV) in the Nordics and UK/Ireland, troubleshooting incidents and supporting system deployments.",
                    "location": "Stockholm, Sweden",
                    "start_date": "2016-01-01",
                    "end_date": "2017-05-31",
                    "website": "https://www.philips.com",
                    "order_index": 7
                }
            ]

            for company_data in companies:
                company = Company(**company_data)
                db.add(company)

            await db.commit()
            print(f"[+] Added {len(companies)} companies")
        except Exception as e:
            print(f"[-] Error adding companies: {e}")
            await db.rollback()


async def populate_education():
    """Populate education from original portfolio"""
    async with AsyncSessionLocal() as db:
        try:
            education_entries = [
                {
                    "institution": "Lund University",
                    "degree": "Bachelor of Science - BS",
                    "field_of_study": "Biomedical Engineering",
                    "description": "Bachelor's Thesis - 'Development of a User-friendly Method of Processing Data from Ergonomics Measurements Utilizing Inclinometers'",
                    "start_date": "2011-09-01",
                    "end_date": "2014-06-01",
                    "order_index": 1
                },
                {
                    "institution": "KTH Royal Institute of Technology",
                    "degree": "Master of Science - MS",
                    "field_of_study": "Biomedical Engineering - Computer Science",
                    "description": "Master's Thesis - 'Improving Quality Assurance of Radiology Equipment Using Process Modelling and Multi-actor System Analysis'",
                    "start_date": "2014-09-01",
                    "end_date": "2016-06-01",
                    "order_index": 2
                },
                {
                    "institution": "Företagsuniversitet",
                    "degree": "Certificate",
                    "field_of_study": "Cybersecurity Fundamentals Course",
                    "description": "10 weeks of intensive training in cybersecurity fundamentals, including: Introduction to Cybersecurity, Threat Actors, Threat Landscapes, and Influence Operations, Systematic Cybersecurity Work, Incident Management, Digital Transformations and Secure Ecosystems",
                    "start_date": "2023-01-01",
                    "end_date": "2023-03-01",
                    "order_index": 3
                },
                {
                    "institution": "CompTIA",
                    "degree": "Security+ Certification",
                    "field_of_study": "Cybersecurity",
                    "description": "12 weeks intensive Cybersecurity Course. Ongoing.",
                    "start_date": "2024-01-01",
                    "end_date": None,
                    "order_index": 4
                }
            ]

            for edu_data in education_entries:
                education = Education(**edu_data)
                db.add(education)

            await db.commit()
            print(f"[+] Added {len(education_entries)} education entries")
        except Exception as e:
            print(f"[-] Error adding education: {e}")
            await db.rollback()


async def main():
    """Main migration function"""
    print("=" * 60)
    print("Portfolio Content Migration")
    print("=" * 60)
    print()

    print("[*] Step 1: Clearing existing data...")
    await clear_existing_data()
    print()

    print("[*] Step 2: Populating companies/experience...")
    await populate_companies()
    print()

    print("[*] Step 3: Populating education...")
    await populate_education()
    print()

    print("=" * 60)
    print("[+] Migration Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Verify data: http://localhost:8001/api/v1/companies/")
    print("  2. Verify education: http://localhost:8001/api/v1/education/")
    print("  3. Check frontend: http://localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
