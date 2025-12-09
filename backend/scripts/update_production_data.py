"""
Update PostgreSQL database with detailed content for all companies.

This script populates detailed_description, technologies, and responsibilities
for all companies based on the content from dashti.se.

Run on Fly.io:
    flyctl ssh console -a dashti-portfolio-backend
    cd /app
    python scripts/update_production_data.py
"""
import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.company import Company


# Detailed content extracted from dashti.se - using exact company names from database
COMPANY_DETAILS = {
    "Hermes Medical Solutions": {
        "detailed_description": """**Hermes Medical Solutions** is a healthcare technology company that develops software solutions for nuclear medicine, supporting medical professionals with diagnostic imaging and treatment planning tools.

As a **Multidisciplinary Specialist** focusing on Quality Assurance, Regulatory Affairs, and Cybersecurity, I work at the intersection of software quality, regulatory compliance, and information security for nuclear medicine software systems.

**Regulatory Compliance:** I ensure our software meets regulatory standards including NIS2 and ISO 27001, supporting market clearance processes for medical device software across multiple jurisdictions.

**Quality Assurance:** I lead Verification and Validation (V&V) activities for nuclear medicine software, maintaining rigorous testing protocols that ensure diagnostic imaging tools meet the highest standards of accuracy and reliability.

**Technical Development:** Working with DICOM protocols and enterprise healthcare architectures, I contribute to system integration efforts that connect our solutions with hospital information systems and clinical workflows.

**Data Security:** I conduct security assessments and implement data protection measures, ensuring patient data remains secure while maintaining compliance with healthcare data regulations.

**Cross-Functional Collaboration:** I coordinate across development, clinical, and regulatory teams to deliver software solutions that meet both technical specifications and clinical needs.""",
        "technologies": ["Windows Server", "Docker", "PowerShell", "Git", "Python", "DICOM", "ISO 27001", "NIS2"],
        "responsibilities": [
            "Ensure regulatory compliance with NIS2 and ISO 27001 standards",
            "Support market clearance processes for medical device software",
            "Lead Verification and Validation (V&V) for nuclear medicine software",
            "Maintain testing protocols for diagnostic imaging tools",
            "Conduct security assessments and data protection implementation",
            "Coordinate across development, clinical, and regulatory teams"
        ]
    },
    "Scania Engines": {
        "detailed_description": """**Scania** is a leading Swedish manufacturer of commercial vehicles, buses, and industrial engines, with a strong focus on sustainable transport solutions.

As a **Technician in Engine Analysis**, I worked in the troubleshooting and diagnostics department at Scania's main facility in Sodertalje, Sweden. My career at Scania spanned two separate periods of employment, each providing unique growth opportunities.

**Initial Engagement (2012):** I joined as a member of the second-line support team, where I developed foundational skills in engine diagnostics and troubleshooting methodologies. This role introduced me to systematic problem-solving approaches in a high-volume manufacturing environment.

**Advanced Engagement (2016):** Returning to Scania in a more independent capacity, I took on end-to-end responsibility for troubleshooting cases. This included initial case intake from the manufacturing line, diagnostic analysis, resolution implementation, and comprehensive documentation for future reference.

**Key Achievements:** I developed strong collaboration skills working with both manufacturing line personnel and construction engineers, contributing to process improvements and documentation standards that enhanced team efficiency.""",
        "technologies": ["Engine Diagnostics", "Technical Documentation", "Manufacturing Systems", "Quality Control"],
        "responsibilities": [
            "Perform engine analysis and diagnostics troubleshooting",
            "Handle complete case lifecycle from intake to resolution",
            "Collaborate with manufacturing line and construction engineers",
            "Create and maintain technical documentation",
            "Implement process improvements for team efficiency"
        ]
    },
    "Finnish Defence Forces": {
        "detailed_description": """**Finnish Defence Forces (Puolustusvoimat)** - specifically **Nylands Brigad** - is a Swedish-speaking coastal defense unit specializing in amphibious operations and marine commando training.

As a **Platoon Leader** with the rank of **2nd Lieutenant**, I commanded military personnel in both garrison and field environments, developing leadership skills under pressure that translate directly to civilian project management and team leadership.

**Command Responsibilities:** I was responsible for the daily welfare and operational readiness of approximately 150 soldiers, while directly leading a tactical unit of 30 soldiers during field operations and exercises.

**Training and Development:** I managed training schedules, personnel development programs, and equipment readiness, ensuring my unit maintained the highest standards of operational capability.

**Leadership Under Pressure:** The role required decisive decision-making in high-stress situations, balancing mission objectives with personnel safety and welfare. This experience developed my ability to remain calm and effective under pressure.

**Selection and Training:** The officer program at Nylands Brigad is highly selective, focusing on physical capabilities, mental resilience, and leadership potential. The training emphasized amphibious warfare, coastal defense, and rapid deployment operations.""",
        "technologies": ["Leadership", "Strategic Planning", "Team Management", "Crisis Management", "Training Development"],
        "responsibilities": [
            "Command and welfare of 150 soldiers in garrison",
            "Lead 30-soldier tactical unit in field operations",
            "Manage training schedules and personnel development",
            "Make decisions under operational pressure",
            "Ensure mission success while maintaining personnel safety"
        ]
    },
    "Karolinska University Hospital": {
        "detailed_description": """**Karolinska University Hospital** is one of Europe's largest and most prestigious university hospitals, affiliated with the Karolinska Institute which awards the Nobel Prize in Physiology or Medicine.

As a **Biomedical Engineer** in the Medical Imaging and Physiology department, I provided technical support and expertise for the hospital's extensive fleet of diagnostic imaging equipment.

**Equipment Support:** I served as the primary technical resource for medical imaging equipment, handling first-line support for a diverse range of diagnostic systems including CT, MRI, X-ray, and nuclear medicine equipment.

**Multi-Vendor Integration:** I gained extensive experience working with equipment from major medical imaging vendors including GE Healthcare, Philips Healthcare, and Siemens Healthineers, understanding the unique characteristics and integration requirements of each platform.

**Systems Architecture:** I developed expertise in healthcare IT systems, particularly RIS/PACS integration with the Hospital Information System. This included working with DICOM and HL7 protocols for seamless clinical data flow.

**Infrastructure Management:** I contributed to IT infrastructure management, including Active Directory administration and implementation of ITIL framework practices for service management.""",
        "technologies": ["DICOM", "HL7", "RIS/PACS", "Active Directory", "GE Healthcare", "Philips", "Siemens", "ITIL"],
        "responsibilities": [
            "Provide first-line technical support for medical imaging equipment",
            "Manage multi-vendor equipment relationships (GE, Philips, Siemens)",
            "Support RIS/PACS integration with Hospital Information System",
            "Work with DICOM and HL7 healthcare communication protocols",
            "Administer Active Directory and implement ITIL practices"
        ]
    },
    "Philips Healthcare": {
        "detailed_description": """**Philips Healthcare** (Enterprise Informatics division) provides advanced medical imaging visualization and cardiovascular PACS solutions to healthcare organizations worldwide.

As an **Incident Support Specialist** for the Nordic region (with dotted-line responsibility to UK/Ireland), I provided Level 1 support for enterprise healthcare informatics solutions.

**Product Expertise:** I specialized in supporting Intellispace Portal (ISP) for advanced medical imaging visualization and Intellispace Cardiovascular (ISCV) for cardiology-specific PACS functionality.

**Incident Management:** I managed the complete incident lifecycle, from initial customer contact through diagnosis, resolution, or escalation to specialized engineering teams. This required strong technical skills combined with excellent customer communication.

**Regional Leadership:** I took on leadership responsibilities for Nordic operations, including mentoring junior Level 1 engineers and facilitating knowledge sharing across regional teams.

**Quality Improvement:** I contributed to upgrade success assessments and identified opportunities for process improvements, helping to enhance service delivery and customer satisfaction across the region.

**Healthcare IT Integration:** I developed deep expertise in healthcare IT integration, including HL7 messaging, broker engines, and enterprise system connectivity.""",
        "technologies": ["Intellispace Portal", "Intellispace Cardiovascular", "HL7", "PACS", "Healthcare IT", "ITIL"],
        "responsibilities": [
            "Provide Level 1 support for Intellispace Portal and Cardiovascular",
            "Manage complete incident lifecycle from contact to resolution",
            "Lead Nordic operations and mentor junior engineers",
            "Facilitate cross-regional knowledge sharing",
            "Assess upgrade success and identify process improvements"
        ]
    },
    "Södersjukhuset - SÖS": {
        "detailed_description": """**Södersjukhuset (SÖS)** is one of Stockholm's largest emergency hospitals, providing comprehensive healthcare services including advanced radiology and medical imaging.

As a **Biomedical Engineer** in the Radiology Department, I managed IT infrastructure and medical imaging systems, contributing to the efficient operation of diagnostic services.

**IT Infrastructure:** I was responsible for managing the department's IT infrastructure, including PACS systems, DICOM networks, and medical imaging equipment interfaces.

**System Optimization:** I analyzed workflows and implemented optimizations to improve efficiency and reduce downtime, ensuring clinical staff could focus on patient care.

**Cross-Departmental Collaboration:** I worked closely with clinical staff, IT teams, and administrative personnel to ensure seamless integration of technology with clinical workflows.

**Regulatory Compliance:** I contributed to maintaining compliance with healthcare regulatory requirements, including ISO 13485 for medical device quality management.

**Contract and Vendor Management:** I participated in equipment evaluations and contract reviews, providing technical input to support procurement decisions.""",
        "technologies": ["PACS", "DICOM", "Medical Imaging", "Healthcare IT", "ISO 13485", "Radiology Systems"],
        "responsibilities": [
            "Manage radiology IT infrastructure including PACS and DICOM",
            "Optimize clinical workflows and reduce system downtime",
            "Collaborate across clinical, IT, and administrative teams",
            "Maintain healthcare regulatory compliance (ISO 13485)",
            "Support equipment evaluations and procurement decisions"
        ]
    },
    "SoftPro Medical Solutions": {
        "detailed_description": """**SoftPro Medical Solutions** develops healthcare software solutions, including the Medusa inventory management system for medical equipment and supplies.

As a **Master Thesis Student**, I conducted research on improving quality assurance processes for radiology equipment through process modeling and multi-actor system analysis.

**Research Focus:** My thesis, titled 'Improving Quality Assurance of Radiology Equipment Using Process Modelling and Multi-actor System Analysis', examined how systematic process analysis could enhance QA workflows in healthcare settings.

**System Integration:** I worked on integrating the Medusa inventory management system with radiology department workflows, exploring opportunities for automation and efficiency improvements.

**Academic Contribution:** The research contributed to understanding how healthcare organizations can optimize their quality assurance processes while maintaining regulatory compliance.""",
        "technologies": ["Process Modeling", "Quality Assurance", "Healthcare Software", "Research Methods"],
        "responsibilities": [
            "Conduct master's thesis research on QA process improvement",
            "Analyze radiology equipment quality assurance workflows",
            "Integrate Medusa inventory system with clinical processes",
            "Apply process modeling and multi-actor system analysis"
        ]
    }
}


async def update_company_details():
    """Update all companies with their detailed content"""

    print("=" * 70)
    print("PostgreSQL Company Details Update Script")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        updated_count = 0
        not_found = []

        for company_name, details in COMPANY_DETAILS.items():
            print(f"Updating: {company_name}")

            # Check if company exists
            result = await db.execute(
                select(Company).where(Company.name == company_name)
            )
            company = result.scalar_one_or_none()

            if not company:
                print(f"  [WARN] Company not found: {company_name}")
                not_found.append(company_name)
                continue

            # Update detailed content
            company.detailed_description = details["detailed_description"]
            company.technologies = details["technologies"]
            company.responsibilities = details["responsibilities"]

            await db.commit()
            updated_count += 1

            print(f"  [OK] Updated successfully")
            print(f"    - Description: {len(details['detailed_description'])} chars")
            print(f"    - Technologies: {len(details['technologies'])} items")
            print(f"    - Responsibilities: {len(details['responsibilities'])} items")
            print()

        # Summary
        print("=" * 70)
        print("Summary:")
        print(f"  - Companies updated: {updated_count}/{len(COMPANY_DETAILS)}")
        if not_found:
            print(f"  - Not found: {', '.join(not_found)}")
        print("=" * 70)
        print()

        # Verification query
        print("Verification - Companies with detailed content:")
        print("-" * 70)

        result = await db.execute(
            select(Company).order_by(Company.name)
        )
        companies = result.scalars().all()

        for company in companies:
            has_desc = "Yes" if company.detailed_description else "No"
            has_tech = "Yes" if company.technologies else "No"
            has_resp = "Yes" if company.responsibilities else "No"
            print(f"{company.name:40} Desc: {has_desc:3}  Tech: {has_tech:3}  Resp: {has_resp:3}")

        print("=" * 70)
        print("[SUCCESS] Company details updated successfully!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(update_company_details())
