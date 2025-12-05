"""
Update production database with COMPLETE experience data including all media (YouTube + Google Maps)
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models.company import Company


async def update_complete_data_with_media():
    """Update database with all experience details INCLUDING YouTube videos and Google Maps"""

    async with AsyncSessionLocal() as db:
        try:
            # Clear existing companies to start fresh
            await db.execute(delete(Company))
            await db.commit()

            companies_data = [
                {
                    "name": "Scania",
                    "title": "Technician, Engine Analysis",
                    "description": "Two separate engagements (2012 and 2016) at Scania Södertälje working on engine analysis and troubleshooting.",
                    "detailed_description": """Scania is a leading Swedish manufacturer of commercial vehicles, buses, and industrial engines with focus on sustainable transport and engineering excellence in heavy-duty vehicles.

**2012 Engagement:**
- Served on second-line support team alongside experienced engineers and technicians
- Developed fundamental troubleshooting capabilities
- Learned organizational structure and production processes

**2016 Engagement:**
- Performed autonomous troubleshooting work
- Managed full case lifecycle from intake through resolution
- Reported findings to supervisors
- Collaborated across production chain from manufacturing line staff to construction engineers
- Created technical documentation
- Established work procedures and routines""",
                    "location": "Scania Södertälje, Sweden",
                    "start_date": "2012-01-01",
                    "end_date": "2016-12-31",
                    "website": "https://www.scania.com",
                    "video_url": "https://www.youtube.com/embed/Rm6grXvyX6I",
                    "video_title": "Scania Truck Manufacturing Process",
                    "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d130603.48820521029!2d17.67627411091932!3d59.238085496816325!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f12baeb6eae75%3A0x16a5832b5a283d07!2zU0NBTklBIFPDtmRlcnTDpGxqZQ!5e0!3m2!1ssv!2sse!4v1749832105161!5m2!1ssv!2sse",
                    "map_title": "Scania Södertälje Location",
                    "order_index": 1,
                    "responsibilities": [
                        "Second-line support team member (2012)",
                        "Autonomous troubleshooting and case management (2016)",
                        "Technical documentation creation",
                        "Cross-functional collaboration across production chain",
                        "Work procedure establishment",
                    ],
                    "technologies": [
                        "Engine analysis systems",
                        "Manufacturing troubleshooting tools",
                        "Production documentation systems",
                    ],
                },
                {
                    "name": "Finnish Defence Forces - Nyland Brigade",
                    "title": "Platoon Leader, 2nd Lieutenant",
                    "description": "Commissioned officer in specialized coastal defense unit, leading garrison and field operations.",
                    "detailed_description": """Finland's military organization responsible for national defense. Nyland Brigade functions as a specialized coastal defense unit. Underwent an intensive transformation from recruit to commissioned officer within this demanding marine commando unit.

**Garrison Duties:**
- Command and welfare oversight of 150 soldiers
- Training schedules management
- Personnel development

**Field Operations:**
- Leadership of specialized 30-person unit in tactical scenarios
- Coordination and split-second decision-making
- Physical and mental resilience under pressure

**Key Competencies:**
- Selection and screening evaluation
- Organizational skills and stress management
- Clear communication and decisive action under pressure
- Team cohesion maintenance""",
                    "location": "Nyland Brigade, Finland",
                    "start_date": "2015-01-01",
                    "end_date": "2015-12-31",
                    "video_url": "https://www.youtube.com/embed/AcLYbg2Jk9c?si=LFG4nBnqCZ3WRfSt",
                    "video_title": "Finnish Defence Forces",
                    "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d720002.5239741812!2d22.654854775421864!3d60.10216545447512!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x468da9e761c88d0f%3A0x8809aeeec13b380b!2sNyland%20Brigade!5e0!3m2!1ssv!2sse!4v1749150985148!5m2!1ssv!2sse",
                    "map_title": "Nyland Brigade Location",
                    "order_index": 2,
                    "responsibilities": [
                        "Command of 150 soldiers in garrison",
                        "Leadership of 30-person tactical unit",
                        "Training schedule management",
                        "Personnel development and welfare",
                        "Tactical coordination and decision-making",
                    ],
                    "technologies": [
                        "Military command systems",
                        "Tactical communication equipment",
                        "Personnel management systems",
                    ],
                },
                {
                    "name": "Hermes Medical Solutions AB",
                    "title": "Multidisciplinary Specialist (QA, Regulatory, Cybersecurity)",
                    "description": "Healthcare technology company developing software solutions for nuclear medicine, supporting diagnostic imaging and treatment planning tools.",
                    "detailed_description": """Hermes Medical Solutions develops software solutions for nuclear medicine, supporting medical professionals with diagnostic imaging and treatment planning tools.

**Key Responsibilities:**

**Regulatory Compliance:**
- Ensures software meets NIS2 and ISO 27001 standards for European healthcare markets
- Supports market clearance processes across jurisdictions

**Quality Assurance:**
- Leads Verification & Validation activities
- Rigorous testing protocols and documentation
- Meets internal and external requirements

**Technical Development:**
- Works with DICOM protocols
- Enterprise architecture design
- Medical imaging systems integration

**Data Security:**
- Assesses security practices
- Implements internal controls
- Maintains data protection standards

**Cross-Functional Collaboration:**
- Partners with development teams
- Works with clinical specialists
- Engages regulatory experts""",
                    "location": "Stockholm, Sweden",
                    "start_date": "2022-09-01",
                    "end_date": None,
                    "website": "https://hermesmedical.com",
                    "video_url": "https://www.youtube.com/embed/bdbevZrjdtU",
                    "video_title": "HERMIA Molecular Imaging Software",
                    "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d23019.922985510006!2d17.999845284557612!3d59.338079926240894!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77fcd4b7b5e1%3A0xf7dcf06b9ce62c50!2sHermes%20Medical%20Solutions%20AB!5e0!3m2!1ssv!2sse!4v1749928857261!5m2!1ssv!2sse",
                    "map_title": "Hermes Medical Solutions AB Location",
                    "order_index": 3,
                    "responsibilities": [
                        "Regulatory compliance (NIS2, ISO 27001)",
                        "Quality Assurance and V&V leadership",
                        "DICOM protocol implementation",
                        "Enterprise architecture development",
                        "Security assessment and controls",
                        "Cross-functional team collaboration",
                    ],
                    "technologies": [
                        "Windows Server",
                        "Docker",
                        "PowerShell",
                        "Git",
                        "Python",
                        "DICOM protocols",
                    ],
                },
                {
                    "name": "Södersjukhuset (SÖS)",
                    "title": "Biomedical Engineer, Radiology Department",
                    "description": "One of Stockholm's largest hospitals, providing healthcare services to southern Stockholm with advanced medical technology.",
                    "detailed_description": """Södersjukhuset is one of Stockholm's largest hospitals, providing healthcare services to the southern Stockholm region with advanced medical technology. Role involved supporting clinical operations through technology management.

**Key Responsibilities:**
- IT infrastructure management covering PACS systems, DICOM protocols, and medical imaging equipment interfaces
- Ensuring systems functionality and optimization for clinical workflows
- Cross-functional collaboration with clinical staff, IT specialists, and administrative teams
- Technology implementation alignment with operational requirements
- IT systems analysis for operational efficiency and security improvements
- Healthcare compliance assurance including ISO 13485 standards""",
                    "location": "Stockholm, Sweden",
                    "start_date": "2021-01-01",
                    "end_date": "2022-08-31",
                    "website": "https://www.sodersjukhuset.se",
                    "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d38737.84701537516!2d18.003017736901185!3d59.31780499604735!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77ec1b565595%3A0x4f818c747249a764!2sS%C3%B6dersjukhuset!5e0!3m2!1ssv!2sse!4v1749832781009!5m2!1ssv!2sse",
                    "map_title": "Södersjukhuset Location",
                    "order_index": 4,
                    "responsibilities": [
                        "PACS systems management",
                        "DICOM protocol administration",
                        "Medical imaging equipment interface support",
                        "Clinical workflow optimization",
                        "Cross-functional collaboration",
                        "ISO 13485 compliance",
                    ],
                    "technologies": [
                        "PACS",
                        "DICOM",
                        "Medical imaging equipment",
                        "Healthcare IT infrastructure",
                        "ISO 13485",
                    ],
                },
                {
                    "name": "SoftPro Medical Solutions",
                    "title": "Master Thesis Student",
                    "description": "Master thesis student integrating Medusa inventory management with radiology workflows and optimizing quality assurance processes for medical equipment.",
                    "detailed_description": """Master's thesis work at SoftPro Medical Solutions focusing on healthcare IT integration and quality assurance optimization.

**Thesis Focus:**
Integration of Medusa inventory management system with radiology workflows to improve medical equipment tracking and quality assurance processes.

**Key Contributions:**
- Analyzed current inventory management workflows in radiology departments
- Designed integration architecture between Medusa and existing healthcare IT systems
- Developed quality assurance optimization strategies for medical equipment
- Evaluated impact on operational efficiency and regulatory compliance

**Technologies:**
- Medusa inventory management platform
- Radiology information systems (RIS)
- Healthcare IT integration protocols
- Quality management systems""",
                    "location": "Stockholm, Sweden",
                    "start_date": "2020-01-01",
                    "end_date": "2020-12-31",
                    "order_index": 5,
                    "responsibilities": [
                        "Medusa inventory system integration analysis",
                        "Radiology workflow optimization",
                        "Quality assurance process improvement",
                        "Healthcare IT integration design",
                        "Master's thesis research and documentation",
                    ],
                    "technologies": [
                        "Medusa inventory management",
                        "RIS (Radiology Information Systems)",
                        "Healthcare IT integration",
                        "Quality management systems",
                        "Medical equipment tracking",
                    ],
                },
                {
                    "name": "Karolinska University Hospital",
                    "title": "Biomedical Engineer, Medical Imaging and Physiology",
                    "description": "One of Europe's largest and most prestigious university hospitals, affiliated with Karolinska Institute.",
                    "detailed_description": """One of Europe's largest and most prestigious university hospitals, affiliated with the Karolinska Institute which administers the Nobel Prize in Physiology or Medicine. Role at the intersection of advanced medical technology and patient care.

**Key Responsibilities:**
- Provided technical support for hospital's medical imaging equipment fleet across multiple modalities
- Served as primary technical resource for diagnostic imaging systems
- Managed integrations between RIS/PACS systems and Hospital Information System
- Supported seamless operation of sophisticated imaging systems across Karolinska Solna and Huddinge campuses""",
                    "location": "Karolinska Solna and Huddinge, Sweden",
                    "start_date": "2019-01-01",
                    "end_date": "2020-12-31",
                    "website": "https://www.karolinska.se",
                    "video_url": "https://www.youtube.com/embed/05k9c4zPBWo",
                    "video_title": "Karolinska University Hospital",
                    "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d27373.793052339282!2d18.003493380951838!3d59.34014358751482!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9d5fc509b8cd%3A0x6f2520b3e07808ba!2sKarolinska%20Universitetssjukhuset%20Solna!5e0!3m2!1ssv!2sse!4v1749832921700!5m2!1ssv!2sse",
                    "map_title": "Karolinska Solna Campus",
                    "order_index": 6,
                    "responsibilities": [
                        "Technical support for multi-modality imaging equipment",
                        "Primary resource for diagnostic imaging systems",
                        "RIS/PACS system integration",
                        "Hospital Information System connectivity",
                        "Active Directory management",
                    ],
                    "technologies": [
                        "GE Medical Systems",
                        "Philips Healthcare",
                        "Siemens Healthineers",
                        "DICOM",
                        "HL7",
                        "Active Directory",
                        "ITIL",
                        "RIS/PACS",
                    ],
                },
                {
                    "name": "Philips AB",
                    "title": "Incident Support Specialist, Nordics",
                    "description": "Level 1 support role within Philips' Enterprise Informatics division for healthcare IT infrastructure across Northern Europe.",
                    "detailed_description": """Philips Enterprise Informatics ESC - Level 1 support responsible for healthcare IT infrastructure across Northern Europe. Managed complete incident lifecycle for Intellispace platforms with significant autonomy.

**Key Responsibilities:**
- Provided comprehensive Level 1 support for Intellispace Portal (ISP) and Intellispace Cardiovascular (ISCV) platforms
- Managed complete incident lifecycle from initial customer contact through resolution or appropriate escalation
- Collaborated with deployment teams on quality assurance and process improvements
- Served as primary contact for Nordic region operations
- Mentored other Level 1 engineers across UK & Ireland and Nordic teams""",
                    "location": "Nordics (Remote)",
                    "start_date": "2023-01-01",
                    "end_date": "2023-12-31",
                    "website": "https://www.philips.com",
                    "video_url": "https://www.youtube.com/embed/i2wsMvBen1c",
                    "video_title": "Enterprise Informatics ESC 2023",
                    "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d32535.951427291504!2d17.999412838149354!3d59.35804439018847!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9e93436d98c5%3A0x16230b74d42df0ca!2sPhilips%20AB!5e0!3m2!1ssv!2sse!4v1749928636549!5m2!1ssv!2sse",
                    "map_title": "Philips AB Location",
                    "order_index": 7,
                    "responsibilities": [
                        "Level 1 support for ISP and ISCV platforms",
                        "Complete incident lifecycle management",
                        "Quality assurance collaboration",
                        "Primary Nordic contact",
                        "Engineer mentorship",
                        "Dotted-line support for UK & Ireland",
                    ],
                    "technologies": [
                        "Intellispace Portal (ISP)",
                        "Intellispace Cardiovascular (ISCV)",
                        "HL7 protocol",
                        "Broker engines",
                        "Enterprise architecture",
                        "PACS systems",
                        "Medical imaging workflows",
                    ],
                },
            ]

            # Create companies with all details
            count = 0
            for company_dict in companies_data:
                # Convert date strings to date objects
                if company_dict.get("start_date"):
                    company_dict["start_date"] = datetime.fromisoformat(
                        company_dict["start_date"]
                    ).date()
                if company_dict.get("end_date"):
                    company_dict["end_date"] = datetime.fromisoformat(
                        company_dict["end_date"]
                    ).date()

                company = Company(**company_dict)
                db.add(company)
                count += 1
                print(f"[OK] Added: {company.name}")

            await db.commit()
            print(
                f"\n[SUCCESS] Updated {count} companies with COMPLETE data (descriptions + media)!"
            )

        except Exception as e:
            print(f"[ERROR] Error updating data: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(update_complete_data_with_media())
