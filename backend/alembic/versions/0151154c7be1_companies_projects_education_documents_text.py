"""companies, projects, education and documents: text columns on eight rows

Data-only. Each update finds its row by name, by institution or by the
column's exact current value, and changes the column only while it still
holds the value listed in this file:

- companies.description on the rows named in _COMPANY_DESCRIPTIONS; the same
  UPDATE sets companies.updated_at, which the sitemap's lastmod reads.
- projects.description on the rows named in _PROJECT_DESCRIPTIONS; the same
  UPDATE sets projects.updated_at.
- education.location on the rows named in _EDUCATION_LOCATIONS, only where
  the column is NULL or empty.
- documents.title and documents.description on the two thesis rows, matched on
  the exact current value of each column (_DOCUMENT_TITLES,
  _DOCUMENT_DESCRIPTIONS).

A value edited in /admin no longer matches its guard and is left alone, and a
re-run changes nothing. On empty tables every update matches nothing; fresh
databases are seeded by seed_data.py, which already carries the companies,
projects and education values. Downgrade is a deliberate no-op.

Revision ID: 0151154c7be1
Revises: b41f7ac2e905
Create Date: 2026-11-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "0151154c7be1"
down_revision: str | Sequence[str] | None = "b41f7ac2e905"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# companies.name -> (exact current description, new description)
_COMPANY_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "Hermes Medical Solutions": (
        "Product security for regulated medical software: threat modeling, FDA premarket "
        "security documentation, IEC 81001-5-1 secure-lifecycle work, SBOM and vulnerability "
        "management — alongside QA/RA responsibility for V&V and market clearance.",
        "Product security for regulated medical software: threat modeling, FDA premarket "
        "security documentation, IEC 81001-5-1 secure-lifecycle work, SBOM and vulnerability "
        "management — alongside QA/RA work on V&V and regulatory submissions.",
    ),
    "Philips Healthcare": (
        "Level 1 support for Intellispace Portal and Cardiovascular across the Nordics and "
        "UK/Ireland — full incident lifecycle, upgrade assessment, and cross-regional "
        "knowledge sharing for enterprise imaging informatics.",
        "Level 1 support for IntelliSpace Portal and IntelliSpace Cardiovascular across the "
        "Nordics and UK/Ireland — full incident lifecycle, upgrade assessment, and "
        "cross-regional knowledge sharing for enterprise imaging informatics.",
    ),
}

# projects.name -> (exact current description, new description)
_PROJECT_DESCRIPTIONS: dict[str, tuple[str, str]] = {
    "subvectors": (
        "Cited, versioned conformance vectors for CI/CD OIDC trust decisions — the answer "
        "key for whether a workload-identity trust condition actually matches, and whether "
        "it is safe.",
        "Cited, versioned conformance vectors for CI/CD OIDC trust decisions — the answer "
        "key for whether a workload-identity trust condition actually matches, and whether "
        "it is safe. Finished: 0.7.0 on PyPI is the final release.",
    ),
    "Portfolio Site": (
        "Professional portfolio website built with Vue 3 and FastAPI. Features dynamic "
        "content management, GitHub OAuth, and CI/CD deployment.",
        "This site: a Vue 3 + TypeScript static build on a FastAPI and PostgreSQL backend, "
        "with a hash-locked content-security policy, SHA-pinned GitHub Actions and a "
        "post-deploy check of the production security headers.",
    ),
}

# education.institution -> location written where the column is NULL or empty
_EDUCATION_LOCATIONS: dict[str, str] = {
    "KTH Royal Institute of Technology": "Stockholm, Sweden",
    "Lund University": "Lund, Sweden",
}

# Each pair reads: exact current value, new value.
_DOCUMENT_TITLES: tuple[tuple[str, str], ...] = (
    (
        "Master Thesis: Improving Quality Assurance of Radiology Equipment Using Process "
        "Modelling and Multi-actor System Analysis",
        "Master's Thesis: Improving Quality Assurance of Radiology Equipment Using Process "
        "Modelling and Multi-actor System Analysis",
    ),
    (
        "Bachelor Thesis: Development of a User-friendly Method of Processing Data from "
        "Ergonomics Measurements Utilizing Inclinometers",
        "Bachelor's Thesis: Development of a User-friendly Method of Processing Data from "
        "Ergonomics Measurements Utilizing Inclinometers",
    ),
)

_DOCUMENT_DESCRIPTIONS: tuple[tuple[str, str], ...] = (
    (
        "Research conducted at KTH Royal Institute of Technology in collaboration with "
        "SoftPro Medical Solutions. The thesis investigates methods to improve QA processes "
        "for radiology equipment through process modelling techniques and multi-actor system "
        "analysis, contributing to enhanced medical device quality management.",
        "Research at KTH Royal Institute of Technology, in collaboration with SoftPro Medical "
        "Solutions: methods to improve quality assurance of radiology equipment through "
        "process modelling and multi-actor system analysis.",
    ),
    (
        "Research project at Lund University focusing on developing user-friendly data "
        "processing methods for ergonomics measurements using inclinometer sensors. The "
        "thesis explores practical applications in occupational health and workplace "
        "ergonomics assessment.",
        "Research at Lund University: a user-friendly method for processing ergonomics "
        "measurements from inclinometer sensors, for occupational-health and workplace "
        "ergonomics assessment.",
    ),
)

_companies = sa.table(
    "companies",
    sa.column("name", sa.String()),
    sa.column("description", sa.Text()),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

_projects = sa.table(
    "projects",
    sa.column("name", sa.String()),
    sa.column("description", sa.Text()),
    sa.column("updated_at", sa.DateTime(timezone=True)),
)

_education = sa.table(
    "education",
    sa.column("institution", sa.String()),
    sa.column("location", sa.String()),
)

_documents = sa.table(
    "documents",
    sa.column("title", sa.String()),
    sa.column("description", sa.Text()),
)


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    for name, (old, new) in _COMPANY_DESCRIPTIONS.items():
        bind.execute(
            _companies.update()
            .where(_companies.c.name == name)
            .where(_companies.c.description == old)
            .values(description=new, updated_at=sa.func.now())
        )

    for name, (old, new) in _PROJECT_DESCRIPTIONS.items():
        bind.execute(
            _projects.update()
            .where(_projects.c.name == name)
            .where(_projects.c.description == old)
            .values(description=new, updated_at=sa.func.now())
        )

    for institution, location in _EDUCATION_LOCATIONS.items():
        bind.execute(
            _education.update()
            .where(_education.c.institution == institution)
            .where(sa.or_(_education.c.location.is_(None), _education.c.location == ""))
            .values(location=location)
        )

    for old, new in _DOCUMENT_TITLES:
        bind.execute(_documents.update().where(_documents.c.title == old).values(title=new))

    for old, new in _DOCUMENT_DESCRIPTIONS:
        bind.execute(
            _documents.update().where(_documents.c.description == old).values(description=new)
        )


def downgrade() -> None:
    """Deliberate no-op, like the other data-only revisions: rows keep their text."""
