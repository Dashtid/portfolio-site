"""Curated CV bullets per role + a private headshot on the CV profile.

Two columns and one backfill.

`companies.cv_highlights` (JSON, nullable) holds the bullet list the CV
export uses for a role. Before this column the export concatenated
`responsibilities` and `outcomes`, two parallel descriptions of the same role
written for the public detail page. A NULL value makes the export fall back
to `outcomes`, then `responsibilities`, then the company description.

The backfill writes the lists in _CURATED, taken from `cv/resume.json` (the
"2024-05" list was replaced on 2026-09-06; see the comment there), and only
into rows whose `cv_highlights` is NULL:
a re-run, or a row edited in /admin/cv since, is left alone. Rows with no
start_date, or with a start month not in _CURATED, stay NULL. When no row
has a NULL `cv_highlights` (an empty table, for example) the backfill does
nothing. Keyed on start month rather than company name: the DB and
resume.json disagree on names ("Philips Healthcare" vs "Philips",
"Karolinska University Hospital" vs "Karolinska Universitetssjukhuset"),
while start months are unique across all 8 roles.

`cv_profile.photo` (Text, NOT NULL, server default "") holds a `data:` URI
rather than a path because this row is 401-gated and both the repo and the
host are public — a portrait under frontend/public/ would be world-readable.

Each add_column is skipped when the column already exists. Downgrade drops
both columns when they exist.

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
    # Edited 2026-09-06, after this revision had been applied. Editing an applied
    # migration changes only the tracked text: deployed rows are rewritten by the
    # later forward migration b41f7ac2e905.
    "2024-05": [
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
