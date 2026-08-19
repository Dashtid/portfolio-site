"""Curated CV bullets per role + a private headshot on the CV profile.

Two columns and one backfill.

`companies.cv_highlights` exists because a CV bullet list is not the website's
bullet list. The export used to concatenate `responsibilities` (terse, present
tense) with `outcomes` (narrative, past tense) — two parallel descriptions of
the same role, written months apart for the public detail page where they
render as separate blocks. Concatenated, that produced 64 bullets across 8
roles (11 for one job), with 21 of 25 outcomes restating a responsibility
almost word for word, and a 6-page PDF where the owner's real CV is 3.

The backfill seeds the curated list from `cv/resume.json`, the hand-edited
JSON Resume the owner already sends out — 13 bullets total, matching the real
CV exactly. Keyed on start month rather than company name: the DB and
resume.json disagree on names ("Philips Healthcare" vs "Philips",
"Karolinska University Hospital" vs "Karolinska Universitetssjukhuset"),
while start months are unique across all 8 roles.

`cv_profile.photo` holds a `data:` URI rather than a path because this row is
401-gated and both the repo and the host are public — a portrait under
frontend/public/ would be world-readable.

Revision ID: c9e2f7a4b681
Revises: b5d21e04c7a9
Create Date: 2026-08-19
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

revision: str = "c9e2f7a4b681"
down_revision: str | Sequence[str] | None = "b5d21e04c7a9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# start month (YYYY-MM) -> curated CV bullets, verbatim from cv/resume.json.
_CURATED: dict[str, list[str]] = {
    "2024-05": [
        "Extending STRIDE-based threat models with product-specific threats and "
        "translating them into actionable, traceable security requirements for "
        "medical software.",
        "Conducting SBOM-based SCA by manually compiling SBOMs from SOUP lists and "
        "analyzing with Grype; triaging vulnerabilities and feeding results into risk "
        "assessments and post-market monitoring.",
        "Improving secure development practices by advocating Roslyn-based static "
        "analysis (rules tailored to a desktop DICOM viewer) and introducing DICOM "
        "fuzzing as dynamic security testing, supporting FDA premarket cybersecurity "
        "guidance and IEC 81001-5-1 documentation needs.",
    ],
    "2022-03": [
        "Spearheaded Level 1 support for image processing systems in healthcare IT "
        "across Nordics, UK&I, and IIG.",
        "Collaborated with installation teams to resolve support cases and improve "
        "system integrations.",
    ],
    "2021-06": [
        "Provided support for imaging IT systems and a large imaging equipment fleet "
        "at two hospital sites.",
    ],
    "2020-10": [
        "Drove digital transformation by integrating Medusa with the workflow for "
        "maintenance of radiology equipment, enhancing QA processes.",
    ],
    "2020-06": [
        "Provided support for IT systems and imaging equipment for a radiology department.",
    ],
    "2016-06": [
        "Handled troubleshooting cases from intake to resolution while coordinating "
        "with production teams.",
    ],
    "2014-01": [
        "Day-to-day command of 150 soldiers.",
        "Field operation command of 30 soldiers.",
        "In-depth officer training in stress resilience and organizational skills.",
    ],
    "2012-06": [
        "Supported a team of engineers and technicians, acquiring foundational "
        "troubleshooting skills.",
    ],
}


def _has_column(table: str, column: str) -> bool:
    inspector = sa.inspect(op.get_bind())
    return column in {c["name"] for c in inspector.get_columns(table)}


def upgrade() -> None:
    if not _has_column("companies", "cv_highlights"):
        op.add_column("companies", sa.Column("cv_highlights", sa.JSON(), nullable=True))
    if not _has_column("cv_profile", "photo"):
        # server_default so the NOT NULL add succeeds against existing rows.
        # env.py does not enable compare_server_default, so this cannot show up
        # as drift in the autogenerate test.
        op.add_column(
            "cv_profile",
            sa.Column("photo", sa.Text(), nullable=False, server_default=""),
        )

    companies = sa.table(
        "companies",
        sa.column("id", sa.String()),
        sa.column("start_date", sa.DateTime()),
        sa.column("cv_highlights", sa.JSON()),
    )
    bind = op.get_bind()

    rows = bind.execute(
        sa.select(companies.c.id, companies.c.start_date).where(companies.c.cv_highlights.is_(None))
    ).fetchall()
    # Empty table = a fresh database; seed_data owns that case.
    if not rows:
        return

    for row in rows:
        if row.start_date is None:
            continue
        bullets = _CURATED.get(f"{row.start_date.year:04d}-{row.start_date.month:02d}")
        if not bullets:
            # Unknown role (added since this migration was written): leave NULL
            # so the export falls back to outcomes rather than blanking it.
            continue
        bind.execute(
            companies.update().where(companies.c.id == row.id).values(cv_highlights=list(bullets))
        )


def downgrade() -> None:
    if _has_column("cv_profile", "photo"):
        op.drop_column("cv_profile", "photo")
    if _has_column("companies", "cv_highlights"):
        op.drop_column("companies", "cv_highlights")
