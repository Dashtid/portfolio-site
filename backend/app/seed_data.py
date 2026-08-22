"""
Seed data script to populate database with initial portfolio content
"""

import asyncio
from datetime import datetime
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import Base, engine
from app.models.company import Company
from app.models.cv_profile import CvProfile
from app.models.education import Education
from app.models.project import Project
from app.models.skill import Skill
from app.utils.logger import get_logger

logger = get_logger(__name__)


async def _already_seeded(session: AsyncSession, model: type[Base], label: str) -> bool:
    """True (with a log line) when the target table already has rows.

    Each seeder skips itself on a populated table, which makes the whole
    script idempotent. Re-running previously duplicated every project and
    education row, then crashed mid-way on the skills unique constraint —
    leaving the database half-duplicated. It also protects prod content
    curated through the admin UI from being buried under stale seed rows.
    Use clear_existing_data() explicitly for a true reset.
    """
    count = (await session.execute(select(func.count()).select_from(model))).scalar_one()
    if count:
        logger.info("Skipping %s seed: table already has %d rows", label, count)
        return True
    return False


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
    if await _already_seeded(session, Company, "companies"):
        return
    companies = [
        {
            "name": "Hermes Medical Solutions",
            "title": "QA/RA & Security Specialist",
            "description": "Product security for regulated nuclear-medicine software: threat modeling, FDA premarket security documentation, IEC 81001-5-1 secure-lifecycle work, SBOM and vulnerability management — alongside QA/RA responsibility for V&V and market clearance.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2024, 5, 1),
            "end_date": None,
            "website": "https://hermesmedical.com",
            "order_index": 1,
            "video_url": "https://www.youtube.com/embed/bdbevZrjdtU",
            "video_title": "Hermes Medical Solutions - HERMIA Imaging Platform",
            "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d23019.922985510006!2d17.999845284557612!3d59.338079926240894!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77fcd4b7b5e1%3A0xf7dcf06b9ce62c50!2sHermes%20Medical%20Solutions%20AB!5e0!3m2!1ssv!2sse!4v1749928857261!5m2!1ssv!2sse",
            "map_title": "Hermes Medical Solutions Location - Stockholm, Sweden",
        },
        {
            "name": "Philips Healthcare",
            "title": "Incident Support Specialist, Nordics",
            "description": "Level 1 support for IntelliSpace Portal and IntelliSpace Cardiovascular across the Nordics and UK/Ireland — full incident lifecycle, upgrade assessment, and cross-regional knowledge sharing for enterprise imaging informatics.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2022, 3, 1),
            "end_date": datetime(2024, 5, 31),
            "website": "https://www.philips.com",
            "order_index": 2,
            "video_url": "https://www.youtube.com/embed/i2wsMvBen1c",
            "video_title": "Philips Healthcare - Innovation",
            "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d32535.951427291504!2d17.999412838149354!3d59.35804439018847!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9e93436d98c5%3A0x16230b74d42df0ca!2sPhilips%20AB!5e0!3m2!1ssv!2sse!4v1749928636549!5m2!1ssv!2sse",
            "map_title": "Philips Healthcare Location - Stockholm, Sweden",
        },
        {
            "name": "Karolinska University Hospital",
            "title": "Biomedical Engineer, Medical Imaging and Physiology",
            "description": "First-line support for one of Europe's largest imaging-equipment fleets: RIS/PACS incident management, DICOM/HL7 integration work, and multi-vendor coordination across GE, Philips, and Siemens systems.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2021, 6, 1),
            "end_date": datetime(2021, 12, 31),
            "website": "https://www.karolinska.se",
            "order_index": 3,
            "video_url": "https://www.youtube.com/embed/05k9c4zPBWo",
            "video_title": "Karolinska University Hospital - Solna Campus",
            "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d27373.793052339282!2d18.003493380951838!3d59.34014358751482!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9d5fc509b8cd%3A0x6f2520b3e07808ba!2sKarolinska%20Universitetssjukhuset%20Solna!5e0!3m2!1ssv!2sse!4v1749832921700!5m2!1ssv!2sse",
            "map_title": "Karolinska University Hospital Location - Stockholm, Sweden",
        },
        {
            "name": "SoftPro Medical Solutions",
            "title": "Master Thesis Student",
            "description": "Thesis research integrating the Medusa inventory system with radiology equipment workflows — process modeling and multi-actor analysis to improve quality assurance in a radiology department.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2020, 10, 1),
            "end_date": datetime(2021, 6, 30),
            "website": None,
            "order_index": 4,
        },
        {
            "name": "Södersjukhuset - SÖS",
            "title": "Biomedical Engineer, Radiology Department",
            "description": "Radiology IT systems management at one of Stockholm's largest emergency hospitals: PACS/DICOM operations, supplier contract evaluations, workflow optimization, and system documentation.",
            "location": "Stockholm, Sweden",
            "start_date": datetime(2020, 6, 1),
            "end_date": datetime(2021, 6, 30),
            "website": "https://www.sodersjukhuset.se",
            "order_index": 5,
            "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d38737.84701537516!2d18.003017736901185!3d59.31780499604735!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77ec1b565595%3A0x4f818c747249a764!2sS%C3%B6dersjukhuset!5e0!3m2!1ssv!2sse!4v1749832781009!5m2!1ssv!2sse",
            "map_title": "Södersjukhuset Location - Stockholm, Sweden",
        },
        {
            "name": "Scania Group",
            "title": "Technician, Engine Analysis",
            "description": "Owned the engine troubleshooting process end-to-end — case intake to resolution — coordinating across the production chain and establishing documentation and work routines.",
            "location": "Södertälje, Sweden",
            "start_date": datetime(2016, 6, 1),
            "end_date": datetime(2016, 8, 31),
            "website": "https://www.scania.com",
            "order_index": 6,
            "video_url": "https://www.youtube.com/embed/Rm6grXvyX6I",
            "video_title": "Scania Group - Truck Manufacturing",
            "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d130603.48820521029!2d17.67627411091932!3d59.238085496816325!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f12baeb6eae75%3A0x16a5832b5a283d07!2zU0NBTklBIFPDtmRlcnTDpGxqZQ!5e0!3m2!1ssv!2sse!4v1749832105161!5m2!1ssv!2sse",
            "map_title": "Scania Group Location - Södertälje, Sweden",
        },
        {
            "name": "Finnish Defence Forces",
            "title": "Platoon Leader, 2nd Lieutenant",
            "description": "Day-to-day command of 150 marine commandos and field command of a 30-soldier unit — leadership, decision-making under pressure, and personnel development in a coastal defense brigade.",
            "location": "Dragsvik, Finland",
            "start_date": datetime(2014, 1, 1),
            "end_date": datetime(2015, 1, 31),
            "website": None,
            "order_index": 7,
            "video_url": "https://www.youtube.com/embed/AcLYbg2Jk9c?si=LFG4nBnqCZ3WRfSt",
            "video_title": "Finnish Defence Forces - Nyland Brigade",
            "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d720002.5239741812!2d22.654854775421864!3d60.10216545447512!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x468da9e761c88d0f%3A0x8809aeeec13b380b!2sNyland%20Brigade!5e0!3m2!1ssv!2sse!4v1749150985148!5m2!1ssv!2sse",
            "map_title": "Nyland Brigade Location - Dragsvik, Finland",
        },
        {
            # Same name as the 2016 entry above; deduped by (name, start_date)
            # rather than name alone — see the seeding loop below.
            "name": "Scania Group",
            "title": "Technician, Engine Analysis",
            "description": "First industry role, on the second-line engine support team — building troubleshooting fundamentals alongside experienced engineers and learning how a heavy-vehicle production organization works.",
            "location": "Södertälje, Sweden",
            "start_date": datetime(2012, 6, 1),
            "end_date": datetime(2012, 8, 31),
            "website": "https://www.scania.com",
            "order_index": 8,
            "video_url": "https://www.youtube.com/embed/Rm6grXvyX6I",
            "video_title": "Scania Group - Truck Manufacturing",
            "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d130603.48820521029!2d17.67627411091932!3d59.238085496816325!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f12baeb6eae75%3A0x16a5832b5a283d07!2zU0NBTklBIFPDtmRlcnTDpGxqZQ!5e0!3m2!1ssv!2sse!4v1749832105161!5m2!1ssv!2sse",
            "map_title": "Scania Group Location - Södertälje, Sweden",
        },
    ]

    added_count = 0
    for company_data in companies:
        # Dedup by (name, order_index) — order_index is unique per seed entry,
        # so two distinct stints at the same company (e.g. Scania Group 2012
        # vs 2016) are both seeded but neither is duplicated on re-runs.
        result = await session.execute(
            select(Company).where(
                Company.name == company_data["name"],
                Company.order_index == company_data["order_index"],
            )
        )
        if result.scalar_one_or_none() is None:
            company = Company(**company_data)
            session.add(company)
            added_count += 1
        else:
            logger.debug(
                "Company '%s' (order %d) already exists, skipping",
                company_data["name"],
                company_data["order_index"],
            )

    await session.commit()
    logger.info(
        "Seeded %d companies (%d already existed)", added_count, len(companies) - added_count
    )


async def seed_projects(session: AsyncSession):
    """Seed project data"""
    if await _already_seeded(session, Project, "projects"):
        return

    # Annotated because `technologies` is now a real list (it is a JSON column)
    # while its siblings are str/bool/int, so the inferred value type widens to
    # `object` and Project(**project_data) stops being a valid mapping unpack.
    #
    # Every project here must be a repo a logged-out recruiter can OPEN.
    #
    # The previous seed listed five projects, four of which were inventions --
    # "Medical Device Security Framework", "Vulnerability Scanner Dashboard",
    # "DICOM Processing Pipeline", "Compliance Automation Tool" -- with no
    # github_url and no corresponding repo anywhere, plus a fifth pointing at
    # the pre-rename portfolio-migration. They also passed `technologies` as a
    # comma-string into a JSON list column, so a fresh install stored a string
    # where every reader expects a list. All four inventions are gone; the
    # names below were verified to return 200 unauthenticated on 2026-08-05.
    #
    # Inclusion rule: a project is listed only if its github_url resolves 200
    # unauthenticated. Advertising a repo behind a 404 proof link is worse for a
    # security candidate than not advertising it at all. Repos that do not meet
    # the bar are simply absent; this file does not name them or say why, because
    # it is world-readable and the explanation would undo the omission.
    projects: list[dict[str, Any]] = [
        {
            "name": "subvectors",
            "description": "Cited, versioned conformance vectors for CI/CD OIDC trust decisions — the answer key for whether a workload-identity trust condition actually matches, and whether it is safe.",
            "technologies": ["Python", "OIDC", "GitHub Actions", "AWS IAM", "Azure", "GCP"],
            "github_url": "https://github.com/Dashtid/subvectors",
            "live_url": None,
            "featured": True,
            "order_index": 1,
        },
        {
            "name": "subcheck",
            "description": "CI gate against cloud trust-policy drift: decodes a GitHub Actions OIDC token's claims and checks them against an expected-claims policy before an over-broad trust policy lets the wrong branch assume a role.",
            "technologies": ["Python", "OIDC", "JWT", "GitHub Actions", "AWS IAM"],
            "github_url": "https://github.com/Dashtid/subcheck",
            "live_url": None,
            "featured": True,
            "order_index": 2,
        },
        {
            "name": "Portfolio Site",
            "description": "This site. Vue 3 + TypeScript static build with a FastAPI/PostgreSQL backend, hash-based CSP, SHA-pinned actions and a full CI/CD pipeline.",
            "technologies": ["Vue 3", "TypeScript", "FastAPI", "PostgreSQL", "Docker", "CI/CD"],
            "github_url": "https://github.com/Dashtid/portfolio-site",
            "live_url": "https://dashti.se",
            "featured": True,
            "order_index": 3,
        },
        {
            "name": "Sysadmin Toolkit",
            "description": "System administration automation for Windows and Linux: maintenance, monitoring, backup and hardening scripts.",
            "technologies": ["PowerShell", "Bash", "Python", "Windows Server", "Linux"],
            "github_url": "https://github.com/Dashtid/sysadmin-toolkit",
            "live_url": None,
            "featured": False,
            "order_index": 4,
        },
    ]

    for project_data in projects:
        project = Project(**project_data)
        session.add(project)

    await session.commit()
    logger.info("Seeded %d projects", len(projects))


async def seed_skills(session: AsyncSession):
    """Seed skills data - matches dashti.se content"""
    if await _already_seeded(session, Skill, "skills"):
        return

    # Canonical keyword set decided 2026-08-06 (career-plan session; applied
    # 2026-08-13). One set across LinkedIn / CV / site. IN: NIS 2, GAMP 5,
    # IEC 62304, IEC 81001-5-1, threat modeling, application security,
    # software supply-chain security (SBOM), secure SDLC, vulnerability
    # management, Kubernetes. OUT (claim-gated): ISO 27001, "OWASP Top 10",
    # pentest wording, unearned certs. NIS 2 + GAMP 5 tier-map gate was
    # signed off by the owner 2026-08-13. Categories mirror the live DB.
    # proficiency_level / years are ADMIN-ONLY (public serializer strips
    # them since 25ad158) and are never rendered anywhere public.
    skills = [
        {
            "name": "Python",
            "category": "Programming",
            "proficiency_level": 90,
            "years_of_experience": 5,
            "order_index": 1,
        },
        {
            "name": "JavaScript/TypeScript",
            "category": "Programming",
            "proficiency_level": 80,
            "years_of_experience": 4,
            "order_index": 2,
        },
        {
            "name": "SQL",
            "category": "Programming",
            "proficiency_level": 80,
            "years_of_experience": 5,
            "order_index": 3,
        },
        {
            "name": "Bash/PowerShell",
            "category": "Programming",
            "proficiency_level": 85,
            "years_of_experience": 5,
            "order_index": 4,
        },
        {
            "name": "FastAPI",
            "category": "Frameworks",
            "proficiency_level": 85,
            "years_of_experience": 3,
            "order_index": 5,
        },
        {
            "name": "Vue.js",
            "category": "Frameworks",
            "proficiency_level": 80,
            "years_of_experience": 3,
            "order_index": 6,
        },
        {
            "name": "Docker",
            "category": "DevOps",
            "proficiency_level": 90,
            "years_of_experience": 4,
            "order_index": 7,
        },
        {
            "name": "Kubernetes",
            "category": "DevOps",
            "proficiency_level": 75,
            "years_of_experience": 3,
            "order_index": 8,
        },
        {
            "name": "GitHub Actions",
            "category": "DevOps",
            "proficiency_level": 85,
            "years_of_experience": 3,
            "order_index": 9,
        },
        {
            "name": "Vulnerability Management",
            "category": "Security",
            "proficiency_level": 85,
            "years_of_experience": 4,
            "order_index": 10,
        },
        {
            "name": "Application Security",
            "category": "Security",
            "proficiency_level": 85,
            "years_of_experience": 4,
            "order_index": 11,
        },
        {
            "name": "Threat Modeling",
            "category": "Security",
            "proficiency_level": 85,
            "years_of_experience": 3,
            "order_index": 12,
        },
        {
            "name": "Secure SDLC",
            "category": "Security",
            "proficiency_level": 85,
            "years_of_experience": 3,
            "order_index": 13,
        },
        {
            "name": "Software Supply-Chain Security (SBOM)",
            "category": "Security",
            "proficiency_level": 85,
            "years_of_experience": 3,
            "order_index": 14,
        },
        {
            "name": "NIS 2",
            "category": "Security",
            "proficiency_level": 75,
            "years_of_experience": 2,
            "order_index": 15,
        },
        {
            "name": "IEC 62304",
            "category": "Medical",
            "proficiency_level": 85,
            "years_of_experience": 4,
            "order_index": 16,
        },
        {
            "name": "IEC 81001-5-1",
            "category": "Medical",
            "proficiency_level": 85,
            "years_of_experience": 3,
            "order_index": 17,
        },
        {
            "name": "GAMP 5",
            "category": "Medical",
            "proficiency_level": 80,
            "years_of_experience": 3,
            "order_index": 18,
        },
        {
            "name": "DICOM",
            "category": "Medical",
            "proficiency_level": 85,
            "years_of_experience": 5,
            "order_index": 20,
        },
        {
            "name": "HL7",
            "category": "Medical",
            "proficiency_level": 75,
            "years_of_experience": 4,
            "order_index": 21,
        },
        {
            "name": "FDA Premarket Cybersecurity (524B)",
            "category": "Medical",
            "proficiency_level": 85,
            "years_of_experience": 2,
            "order_index": 19,
        },
    ]
    for skill_data in skills:
        skill = Skill(**skill_data)
        session.add(skill)

    await session.commit()
    logger.info("Seeded %d skills", len(skills))


async def seed_education(session: AsyncSession):
    """Seed education data"""
    if await _already_seeded(session, Education, "education"):
        return

    education_items = [
        # Reconciled with the live DB (/api/v1/education/, 2026-08-05). These
        # rows had drifted into a different academic history than production:
        # KTH 2017-2022 "M.Sc. Medical Engineering" with a thesis on "AI-driven
        # diagnostic systems" that does not exist, and Lund as a 2020-2021
        # exchange rather than the full 2015-2018 B.Sc. HomeView's static
        # education fallback carried the same wrong values; both now match.
        {
            "institution": "KTH Royal Institute of Technology",
            "degree": "Master of Science - MS",
            "field_of_study": "Biomedical Engineering - Computer Science",
            "start_date": datetime(2018, 8, 1),
            "end_date": datetime(2021, 6, 30),
            "location": "Stockholm, Sweden",
            "description": "Master's Thesis - 'Improving Quality Assurance of Radiology Equipment Using Process Modelling and Multi-actor System Analysis'",
            "is_certification": False,
            "order_index": 1,
        },
        {
            "institution": "Lund University",
            "degree": "Bachelor of Science - BS",
            "field_of_study": "Biomedical Engineering",
            "start_date": datetime(2015, 8, 1),
            "end_date": datetime(2018, 6, 30),
            "location": "Lund, Sweden",
            "description": "Bachelor's Thesis - 'Development of a User-friendly Method of Processing Data from Ergonomics Measurements Utilizing Inclinometers'",
            "is_certification": False,
            "order_index": 2,
        },
        {
            # Honestly labelled as a course (is_certification=False): a
            # completed short course, not a professional certification.
            "institution": "Företagsuniversitetet",
            "degree": "Cybersecurity Fundamentals (Course)",
            "field_of_study": "Information Security",
            "start_date": datetime(2024, 10, 1),
            "end_date": datetime(2024, 12, 31),
            "location": "Stockholm, Sweden",
            "description": "Eight-week YH course covering the threat landscape and cyber kill chain, systematic information security work, incident response and digital forensics, SCADA/ICS security, and secure software development.",
            "is_certification": False,
            "certificate_url": "https://foretagsuniversitetet-yh.trueoriginal.com/utbildningsbevis-226768-datacourse-select-title-4436/?ref=linkedin-profile&lang=en",
            "order_index": 3,
        },
        {
            # The one earned professional certification. Everything else on
            # this list is a degree or a course — no unearned or offensive
            # (CEH/pentest) certs are advertised; the public brand is
            # defensive-first product security for regulated medtech.
            "institution": "CompTIA",
            "degree": "Security+",
            "field_of_study": "Cybersecurity",
            # Verified against the issuer's own Open Badges assertion at
            # credly.com/api/v1/obi/v2/badge_assertions/450d4dcd-...:
            # issuedOn 2026-01-04, expires 2029-01-04 (exam SY0-701).
            # These were 2024-01-01 -> 2026-01-31, which was wrong in BOTH
            # directions and made the site's only earned certification look
            # EXPIRED as of 2026-01-31. It is valid for another three years.
            "start_date": datetime(2026, 1, 4),
            "end_date": datetime(2029, 1, 4),
            "location": "Online",
            "description": "Industry-standard certification covering network security, threats, vulnerabilities, and risk management.",
            "is_certification": True,
            "certificate_url": "https://www.credly.com/badges/450d4dcd-e24c-4906-98b9-2ebb792f9462/public_url",
            "order_index": 4,
        },
    ]

    for edu_data in education_items:
        education = Education(**edu_data)
        session.add(education)

    await session.commit()
    logger.info("Seeded %d education items", len(education_items))


async def seed_cv_profile(session: AsyncSession):
    """Seed the singleton CV profile with the curated prose + public links.

    Prose mirrors the accurate cv/resume.json basics (the hand-curated
    source). Private contact (email / phone / personnummer) is intentionally
    left blank — the owner fills those through the admin CV form after deploy,
    so the real values are never committed to the repo. The admin-only CV
    export assembles experience / education / skills from their own tables.
    """
    if await _already_seeded(session, CvProfile, "cv_profile"):
        return

    profile = CvProfile(
        name="David Dashti",
        label="Product & Application Security Engineer — Regulated Medical Software",
        summary=(
            "Biomedical Engineer focused on product cybersecurity for regulated medical "
            "software. Experienced extending STRIDE-based threat models into concrete, "
            "product-specific security requirements and supporting vulnerability evaluation "
            "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
            "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
            "evidence and SDLC improvements."
        ),
        # Evidence-backed wording only: the OIDC trust-policy research is real
        # (subvectors/subcheck); there is no AWS or Terraform work anywhere, so
        # they do not belong even in a "focus" line (2026-08-22 accuracy pass).
        focus=(
            "CI/CD and workload-identity security (OIDC trust policies) and "
            "secure SDLC for regulated software"
        ),
        location_city="Stockholm",
        location_region="Stockholm",
        location_country="SE",
        url="https://dashti.se",
        linkedin_url="https://www.linkedin.com/in/david-dashti/",
        github_url="https://github.com/Dashtid",
        languages=[
            {"language": "Swedish", "fluency": "Native"},
            {"language": "English", "fluency": "Fluent"},
        ],
        # Övrigt / logistics — rendered at the BOTTOM of the CV, never under
        # certificates (CV-generator requirements, 2026-08-06).
        other_items=["B-körkort (category B driving licence)"],
        # photo intentionally left empty: the headshot is personal data and is
        # uploaded through /admin/cv after deploy, exactly like email/phone, so
        # it never lives in this public repo.
    )
    session.add(profile)
    await session.commit()
    logger.info("Seeded CV profile singleton")


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
            await seed_cv_profile(session)

            logger.info("Database seeding completed successfully")

        except Exception as e:
            logger.exception("Error during seeding: %s", e)
            await session.rollback()
            raise

    # Dispose of the engine
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
