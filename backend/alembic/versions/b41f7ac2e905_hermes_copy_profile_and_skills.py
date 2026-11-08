"""Hermes row copy, cv_profile label and summary, three regulatory skills

Data-only. Four things change on the deployed database:

1. `companies.cv_highlights` on the row named _HERMES is set to _HIGHLIGHTS.
2. `companies.description` on the same row is set to _DESCRIPTION; this
   string renders on the public homepage.
3. `cv_profile.summary` (_SUMMARY_OLD -> _SUMMARY_NEW) and `cv_profile.label`
   (_LABEL_OLD -> _LABEL_NEW).
4. `skills` — MDR, ISO 13485 and EU AI Act are inserted into Regulatory &
   Standards Compliance when no row has that name, and GAMP 5 / NIS 2 /
   DICOM / HL7 are renumbered (17-20) to keep the group ordered. The CV export
   reads skills from THIS table; cv/resume.json is a reference copy that
   never reaches the generated document.

[!] The companies row is matched on its name alone and updated
UNCONDITIONALLY, unlike the exact-previous-value guard used elsewhere (see
c9a4e7b21f83 and f3d8b17c6e42). The previous values are not recorded in this
file, so there is nothing to match them against: an edit made to this row
through /admin/cv before the upgrade is overwritten.

`cv_profile` keeps the exact-previous-value guard: each update matches the
exact previous value, so an edited summary or label is left alone. The skills
inserts check names only, so a re-run, or a row an admin already added by
hand, converges instead of colliding on the unique name.

The companies and cv_profile updates match nothing on empty tables. There is
no empty-table early return for skills: on an empty skills table the three
rows are inserted. Downgrade is a deliberate no-op: the previous companies
values are not recorded here.

Revision ID: b41f7ac2e905
Revises: a7f3c81d9b24
Create Date: 2026-09-06

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "b41f7ac2e905"
down_revision: str | Sequence[str] | None = "a7f3c81d9b24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_HERMES = "Hermes Medical Solutions"

_HIGHLIGHTS = [
    "Author product cybersecurity documentation supporting regulatory submissions "
    "- threat models, security risk assessments and premarket security evidence - "
    "inside an ISO 13485 quality system.",
    "Build and present every product STRIDE threat model, and translate them into "
    "traceable, product-specific security requirements.",
    "Run gap analyses against IEC 81001-5-1 and FDA premarket cybersecurity "
    "requirements (FD&C Act section 524B), and drive the secure-SDLC improvements "
    "that come out of them.",
    "Compile SBOMs by hand from SOUP lists and shipped artifacts, at artifact level "
    "and on demand, and analyze them with Grype; triage findings into risk "
    "assessments and post-market surveillance.",
    "Authored the product's build-time security analyzer ruleset (Roslyn CA rules, "
    "warning-level), derived from the threat model so that every enabled rule "
    "traces to a modelled threat.",
    "Introduced black-box dynamic security testing into the product verification approach.",
    "EU AI Act readiness is the other named half of the role: the applicability and "
    "gap assessment has started, and Article 15 - accuracy, robustness, "
    "cybersecurity - is where it extends the product-security work.",
    "Began the organization's ISO 27001-aligned ISMS build-out, extending the remit "
    "from product security to the organization around it.",
]

_DESCRIPTION = (
    "Product security for regulated medical software: threat modeling, FDA premarket "
    "security documentation, IEC 81001-5-1 secure-lifecycle work, SBOM and vulnerability "
    "management — alongside QA/RA responsibility for V&V and market clearance."
)

_LABEL_OLD = "Product & Application Security Engineer — Regulated Medical Software"
_LABEL_NEW = (
    "Product & Application Security Engineer — Regulated Medical Software "
    "(FDA 524B, IEC 81001-5-1, EU AI Act)"
)

_SUMMARY_OLD = (
    "Biomedical Engineer focused on product cybersecurity for regulated medical "
    "software. Experienced in extending STRIDE-based threat models into concrete, "
    "product-specific security requirements and supporting vulnerability evaluation "
    "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
    "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
    "evidence and SDLC improvements."
)

_SUMMARY_NEW = (
    "Security specialist in regulated medical software. Since 2024 I have authored the "
    "product cybersecurity evidence inside a medical-device manufacturer's ISO 13485 "
    "quality system — threat models, security risk assessments and the premarket "
    "security documentation — against FDA premarket cybersecurity requirements "
    "(FD&C Act section 524B) and IEC 81001-5-1. EU AI Act readiness is the other named "
    "half of the role, and the applicability and gap assessment has started: Article "
    "15's accuracy, robustness and cybersecurity requirements extend the same evidence "
    "work to a second regulatory regime."
)

_companies = sa.table(
    "companies",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
    sa.column("description", sa.Text()),
    sa.column("cv_highlights", sa.JSON()),
)

_cv_profile = sa.table(
    "cv_profile",
    sa.column("id", sa.Integer()),
    sa.column("label", sa.String()),
    sa.column("summary", sa.Text()),
)

_skills = sa.table(
    "skills",
    sa.column("id", sa.String()),
    sa.column("name", sa.String()),
    sa.column("category", sa.String()),
    sa.column("proficiency_level", sa.Integer()),
    sa.column("years_of_experience", sa.Float()),
    sa.column("order_index", sa.Integer()),
)

_REGULATORY = "Regulatory & Standards Compliance"

# Each tuple is name, proficiency level, years of experience, order index.
_NEW_SKILLS = [
    ("MDR", 80, 2.0, 14),
    ("ISO 13485", 80, 2.0, 15),
    ("EU AI Act", 60, 1.0, 16),
]

# Existing rows shift down so the three new rows (14-16) sit above GAMP 5 and
# NIS 2, and Healthcare IT stays last.
_RENUMBERED = {"GAMP 5": 17, "NIS 2": 18, "DICOM": 19, "HL7": 20}


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    # Matched on the row name alone - see the module docstring.
    bind.execute(
        _companies.update()
        .where(_companies.c.name == _HERMES)
        .values(cv_highlights=_HIGHLIGHTS, description=_DESCRIPTION)
    )

    bind.execute(
        _cv_profile.update()
        .where(_cv_profile.c.summary == _SUMMARY_OLD)
        .values(summary=_SUMMARY_NEW)
    )
    bind.execute(
        _cv_profile.update().where(_cv_profile.c.label == _LABEL_OLD).values(label=_LABEL_NEW)
    )

    # Skills: insert-if-absent, so a re-run and an owner who already added one
    # by hand both converge instead of colliding on the unique name.
    existing = {row[0] for row in bind.execute(sa.select(_skills.c.name)).fetchall()}
    for name, proficiency, years, order_index in _NEW_SKILLS:
        if name in existing:
            continue
        bind.execute(
            _skills.insert().values(
                id=str(uuid.uuid4()),
                name=name,
                category=_REGULATORY,
                proficiency_level=proficiency,
                years_of_experience=years,
                order_index=order_index,
            )
        )
    for name, order_index in _RENUMBERED.items():
        bind.execute(_skills.update().where(_skills.c.name == name).values(order_index=order_index))


def downgrade() -> None:
    """Deliberate no-op - the previous values are not recorded here."""
