"""
Company API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("/", response_model=list[CompanyResponse])
async def get_companies(db: AsyncSession = Depends(get_db)):
    """Get all companies"""
    result = await db.execute(select(Company).order_by(Company.order_index))
    companies = result.scalars().all()
    return companies


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(company_id: str, db: AsyncSession = Depends(get_db)):
    """Get a specific company by ID"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Company with ID {company_id} not found"
        )

    return company


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Create a new company (requires admin authentication)"""
    db_company = Company(**company.dict())
    db.add(db_company)
    await db.commit()
    await db.refresh(db_company)
    return db_company


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: str,
    company_update: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Update a company (requires admin authentication)"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Company with ID {company_id} not found"
        )

    # Update only provided fields
    for field, value in company_update.dict(exclude_unset=True).items():
        setattr(company, field, value)

    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
):
    """Delete a company (requires admin authentication)"""
    result = await db.execute(select(Company).where(Company.id == company_id))
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Company with ID {company_id} not found"
        )

    await db.delete(company)
    await db.commit()


@router.post("/rebuild-complete-data-temp", status_code=status.HTTP_200_OK)
async def rebuild_complete_data_temp(
    db: AsyncSession = Depends(get_db),
):
    """TEMPORARY: Rebuild database with complete experience data from original site (NO AUTH - REMOVE AFTER USE)"""
    try:
        # Clear existing companies
        await db.execute(select(Company).delete())
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
                "order_index": 1,
                "responsibilities": [
                    "Second-line support team member (2012)",
                    "Autonomous troubleshooting and case management (2016)",
                    "Technical documentation creation",
                    "Cross-functional collaboration across production chain",
                    "Work procedure establishment"
                ],
                "technologies": [
                    "Engine analysis systems",
                    "Manufacturing troubleshooting tools",
                    "Production documentation systems"
                ]
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
                "order_index": 2,
                "responsibilities": [
                    "Command of 150 soldiers in garrison",
                    "Leadership of 30-person tactical unit",
                    "Training schedule management",
                    "Personnel development and welfare",
                    "Tactical coordination and decision-making"
                ],
                "technologies": [
                    "Military command systems",
                    "Tactical communication equipment",
                    "Personnel management systems"
                ]
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
                "order_index": 3,
                "responsibilities": [
                    "Regulatory compliance (NIS2, ISO 27001)",
                    "Quality Assurance and V&V leadership",
                    "DICOM protocol implementation",
                    "Enterprise architecture development",
                    "Security assessment and controls",
                    "Cross-functional team collaboration"
                ],
                "technologies": [
                    "Windows Server",
                    "Docker",
                    "PowerShell",
                    "Git",
                    "Python",
                    "DICOM protocols"
                ]
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
                "order_index": 4,
                "responsibilities": [
                    "PACS systems management",
                    "DICOM protocol administration",
                    "Medical imaging equipment interface support",
                    "Clinical workflow optimization",
                    "Cross-functional collaboration",
                    "ISO 13485 compliance"
                ],
                "technologies": [
                    "PACS",
                    "DICOM",
                    "Medical imaging equipment",
                    "Healthcare IT infrastructure",
                    "ISO 13485"
                ]
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
                "order_index": 5,
                "responsibilities": [
                    "Technical support for multi-modality imaging equipment",
                    "Primary resource for diagnostic imaging systems",
                    "RIS/PACS system integration",
                    "Hospital Information System connectivity",
                    "Active Directory management"
                ],
                "technologies": [
                    "GE Medical Systems",
                    "Philips Healthcare",
                    "Siemens Healthineers",
                    "DICOM",
                    "HL7",
                    "Active Directory",
                    "ITIL",
                    "RIS/PACS"
                ]
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
                "order_index": 6,
                "responsibilities": [
                    "Level 1 support for ISP and ISCV platforms",
                    "Complete incident lifecycle management",
                    "Quality assurance collaboration",
                    "Primary Nordic contact",
                    "Engineer mentorship",
                    "Dotted-line support for UK & Ireland"
                ],
                "technologies": [
                    "Intellispace Portal (ISP)",
                    "Intellispace Cardiovascular (ISCV)",
                    "HL7 protocol",
                    "Broker engines",
                    "Enterprise architecture",
                    "PACS systems",
                    "Medical imaging workflows"
                ]
            },
            {
                "name": "KTH Royal Institute of Technology",
                "title": "Research Assistant - Medical Imaging",
                "description": "Developed machine learning models for medical image analysis, focusing on MRI and CT scan processing.",
                "detailed_description": """Research work at KTH focusing on machine learning applications in medical imaging. Published research on deep learning applications in radiology, specifically analyzing MRI and CT scan data for diagnostic purposes.""",
                "location": "Stockholm, Sweden",
                "start_date": "2017-01-01",
                "end_date": "2018-12-31",
                "website": "https://www.kth.se",
                "order_index": 7,
                "responsibilities": [
                    "Machine learning model development",
                    "Medical image analysis (MRI/CT)",
                    "Deep learning research",
                    "Radiology applications",
                    "Research publication"
                ],
                "technologies": [
                    "Python",
                    "TensorFlow",
                    "PyTorch",
                    "DICOM",
                    "MRI imaging",
                    "CT imaging",
                    "Deep learning"
                ]
            }
        ]

        # Create companies with all details
        count = 0
        for company_dict in companies_data:
            company = Company(**company_dict)
            db.add(company)
            count += 1

        await db.commit()
        return {"status": "success", "message": f"Successfully rebuilt database with {count} complete companies", "count": count}

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error rebuilding database: {str(e)}"
        )
