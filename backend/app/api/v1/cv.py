"""
Admin-only CV export (Campaign 2026-08 Sprint 2).

The public site IS the CV; there is no public /cv page. This router lets the
owner (admin-authenticated) edit the CV profile prose + private contact and
download a COMPLETE CV assembled from the DB they already curate through the
admin CMS — companies (experience), education and skills — so keeping the
site current keeps the CV current.

Every route here is admin-gated via ``get_current_admin_user``. The assembled
export payload carries the owner's private contact and MUST NOT be exposed on
any public / unauthenticated route.
"""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_admin_user
from app.database import get_db
from app.models.company import Company
from app.models.cv_profile import CvProfile
from app.models.education import Education
from app.models.skill import Skill
from app.models.user import User
from app.schemas.cv_profile import CvProfileResponse, CvProfileUpdate

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]
AdminUser = Annotated[User, Depends(get_current_admin_user)]

# Defense-in-depth whitelist mirroring the CRUD routers: only these columns
# can be written through the update endpoint.
_PROFILE_UPDATE_FIELDS = frozenset(
    {
        "name",
        "label",
        "summary",
        "focus",
        "location_city",
        "location_region",
        "location_country",
        "url",
        "linkedin_url",
        "github_url",
        "languages",
        "email",
        "phone",
        "personnummer",
    }
)


async def _get_or_create_profile(db: AsyncSession) -> CvProfile:
    """Return the singleton CV profile, creating an empty one if absent.

    Seeding creates the row in normal operation; this keeps the endpoints
    robust on a fresh DB where the seed has not run.
    """
    result = await db.execute(select(CvProfile).order_by(CvProfile.id).limit(1))
    profile = result.scalar_one_or_none()
    if profile is None:
        # Fixed PK enforces the singleton: two concurrent first-time creates
        # collide on id=1 instead of inserting a second orphan row. The loser
        # rolls back and re-reads the winner's row.
        profile = CvProfile(id=1)
        db.add(profile)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            result = await db.execute(select(CvProfile).order_by(CvProfile.id).limit(1))
            profile = result.scalar_one()
        else:
            await db.refresh(profile)
    return profile


def _fmt_ym(value: date | None) -> str:
    """JSON Resume month precision (YYYY-MM); empty string for a null date."""
    return value.strftime("%Y-%m") if value else ""


@router.get("/profile", response_model=CvProfileResponse)
async def get_cv_profile(db: DbSession, current_user: AdminUser) -> CvProfile:
    """Return the CV profile (admin-only; includes private contact)."""
    _ = current_user  # admin gate only
    return await _get_or_create_profile(db)


@router.put("/profile", response_model=CvProfileResponse)
async def update_cv_profile(
    profile_update: CvProfileUpdate,
    db: DbSession,
    current_user: AdminUser,
) -> CvProfile:
    """Partial-update the CV profile (requires admin authentication)."""
    _ = current_user  # admin gate only
    profile = await _get_or_create_profile(db)

    for field, value in profile_update.model_dump(exclude_unset=True).items():
        # Every column is NOT NULL, so an explicitly-provided JSON null would
        # 500 on commit. Treat a provided null as "leave unchanged".
        if field in _PROFILE_UPDATE_FIELDS and value is not None:
            # languages is validated as list[LanguageItem]; model_dump turns
            # each item back into a plain dict for the JSON column.
            setattr(profile, field, value)

    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/export")
async def export_cv(db: DbSession, current_user: AdminUser) -> dict[str, Any]:
    """Assemble a complete JSON Resume from the DB the owner curates.

    Admin-only: the payload carries private contact (email / phone and, if
    set, personnummer). Experience, education and skills come straight from
    the same tables that render the public homepage, so the export always
    reflects the current site.
    """
    _ = current_user  # admin gate only
    profile = await _get_or_create_profile(db)

    companies = (await db.execute(select(Company).order_by(Company.order_index))).scalars().all()
    education_rows = (
        (await db.execute(select(Education).order_by(Education.order_index))).scalars().all()
    )
    skills = (await db.execute(select(Skill).order_by(Skill.order_index))).scalars().all()

    work: list[dict[str, Any]] = []
    for c in companies:
        # DB stores bullets as responsibilities + quantified outcomes (D3-UX-03);
        # a CV highlight list is the concatenation. Fall back to the summary
        # paragraph only when a role has no structured bullets at all.
        highlights = list(c.responsibilities or []) + list(c.outcomes or [])
        if not highlights and c.description:
            highlights = [c.description]
        work.append(
            {
                "name": c.name,
                "position": c.title or "",
                "location": c.location or "",
                "startDate": _fmt_ym(c.start_date),
                "endDate": _fmt_ym(c.end_date),
                "highlights": highlights,
            }
        )

    education: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    for e in education_rows:
        if e.is_certification:
            certificates.append(
                {
                    "name": e.degree,
                    "issuer": e.institution,
                    "date": _fmt_ym(e.end_date),
                    "url": e.certificate_url or "",
                }
            )
        else:
            education.append(
                {
                    "institution": e.institution,
                    "studyType": e.degree,
                    "area": e.field_of_study or "",
                    "startDate": _fmt_ym(e.start_date),
                    "endDate": _fmt_ym(e.end_date),
                    "courses": [e.description] if e.description else [],
                }
            )

    # Group the flat Skill rows by category, preserving first-seen order so
    # the CV sections stay stable across exports.
    skill_groups: dict[str, list[str]] = {}
    for s in skills:
        skill_groups.setdefault(s.category or "Skills", []).append(s.name)
    skills_out = [{"name": cat, "keywords": kws} for cat, kws in skill_groups.items()]

    profiles: list[dict[str, str]] = []
    if profile.linkedin_url:
        profiles.append({"network": "LinkedIn", "url": profile.linkedin_url})
    if profile.github_url:
        profiles.append({"network": "GitHub", "url": profile.github_url})

    basics: dict[str, Any] = {
        "name": profile.name,
        "label": profile.label,
        "email": profile.email,
        "phone": profile.phone,
        "url": profile.url,
        "summary": profile.summary,
        "focus": profile.focus,
        "location": {
            "city": profile.location_city,
            "region": profile.location_region,
            "countryCode": profile.location_country,
        },
        "profiles": profiles,
    }
    # Optional and off by default — only present when the owner filled it in.
    if profile.personnummer:
        basics["personalNumber"] = profile.personnummer

    return {
        "basics": basics,
        "work": work,
        "education": education,
        "certificates": certificates,
        "skills": skills_out,
        "languages": profile.languages or [],
    }
