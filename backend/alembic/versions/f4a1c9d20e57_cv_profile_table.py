"""cv_profile singleton table (Campaign 2026-08 Sprint 2)

Backs the admin-only CV export. A single-row table holding the CV prose
(summary / label / focus / location), public links, languages, and the
owner's private contact (email / phone / optional personnummer). The private
columns are surfaced only through admin-authenticated endpoints.

Guarded create_table because non-production environments may already carry
the table via the create_all() bootstrap before this revision runs.

Revision ID: f4a1c9d20e57
Revises: f2b8d61c4a93
Create Date: 2026-07-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "f4a1c9d20e57"
down_revision: str | Sequence[str] | None = "f2b8d61c4a93"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    inspector = sa.inspect(op.get_bind())
    if "cv_profile" in inspector.get_table_names():
        return
    cv_profile_table = op.create_table(
        "cv_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False, server_default=""),
        sa.Column("label", sa.String(length=300), nullable=False, server_default=""),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("focus", sa.Text(), nullable=False, server_default=""),
        sa.Column("location_city", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("location_region", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("location_country", sa.String(length=2), nullable=False, server_default=""),
        sa.Column("url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("linkedin_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("github_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("languages", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("email", sa.String(length=320), nullable=False, server_default=""),
        sa.Column("phone", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("personnummer", sa.String(length=64), nullable=False, server_default=""),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )

    # Seed the singleton with the curated public prose so an EXISTING prod DB
    # — where this migration runs via the upgrade path and the seed script is
    # NOT re-invoked — still gets a populated CV profile. Private contact stays
    # blank; the owner fills email/phone through the admin CV form after deploy,
    # so nothing personal is committed. A fresh DB is instead populated by
    # seed_cv_profile() (the seed runs, this migration is stamped not executed),
    # so the two paths never both insert. Seeding here also removes the
    # empty-table window behind the singleton create-race and the
    # "blank lazy row suppresses the seed" edge.
    op.bulk_insert(
        cv_profile_table,
        [
            {
                "name": "David Dashti",
                "label": "Product & Application Security Engineer — Regulated Medical Software",
                "summary": (
                    "Biomedical Engineer focused on product cybersecurity for regulated "
                    "medical software. Experienced extending STRIDE-based threat models into "
                    "concrete, product-specific security requirements and supporting "
                    "vulnerability evaluation using SBOM-driven SCA. Comfortable translating "
                    "FDA premarket cybersecurity guidance (Section 524B) and IEC 81001-5-1 "
                    "expectations into structured security evidence and SDLC improvements."
                ),
                "focus": (
                    "Cloud & CI/CD security (OIDC/IAM, AWS/Terraform) and secure-SDLC for "
                    "regulated software"
                ),
                "location_city": "Stockholm",
                "location_region": "Stockholm",
                "location_country": "SE",
                "url": "https://dashti.se",
                "linkedin_url": "https://www.linkedin.com/in/david-dashti/",
                "github_url": "https://github.com/Dashtid",
                "languages": [
                    {"language": "Swedish", "fluency": "Native"},
                    {"language": "English", "fluency": "Fluent"},
                ],
                "email": "",
                "phone": "",
                "personnummer": "",
            }
        ],
    )


def downgrade() -> None:
    """Downgrade schema."""
    inspector = sa.inspect(op.get_bind())
    if "cv_profile" in inspector.get_table_names():
        op.drop_table("cv_profile")
