"""oss_contributions table for admin OSS dashboard (OSS-DASH-01)

Persistence for the admin /oss endpoint: one row per tracked PR or Issue
across the 8 upstream repos in TRACKED_REPOS, replaced wholesale on each
refresh. Bucket classification (NOW / WAITING / WATCHING / DONE) lives
on the row; LATER entries are hardcoded in code and never persisted.

Revision ID: d8a4c92b1f73
Revises: c3f1d96a4b27
Create Date: 2026-06-14

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "d8a4c92b1f73"
down_revision: str | Sequence[str] | None = "c3f1d96a4b27"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "oss_contributions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("github_node_id", sa.String(length=64), nullable=False),
        sa.Column("kind", sa.String(length=16), nullable=False),
        sa.Column("repo_name_with_owner", sa.String(length=255), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("state", sa.String(length=16), nullable=False),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("author_login", sa.String(length=255), nullable=True),
        sa.Column("bucket", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        op.f("ix_oss_contributions_github_node_id"),
        "oss_contributions",
        ["github_node_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_oss_contributions_repo_name_with_owner"),
        "oss_contributions",
        ["repo_name_with_owner"],
        unique=False,
    )
    op.create_index(
        op.f("ix_oss_contributions_bucket"),
        "oss_contributions",
        ["bucket"],
        unique=False,
    )
    op.create_index(
        "ix_oss_contributions_bucket_repo_activity",
        "oss_contributions",
        ["bucket", "repo_name_with_owner", "last_activity_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_oss_contributions_bucket_repo_activity", table_name="oss_contributions")
    op.drop_index(op.f("ix_oss_contributions_bucket"), table_name="oss_contributions")
    op.drop_index(op.f("ix_oss_contributions_repo_name_with_owner"), table_name="oss_contributions")
    op.drop_index(op.f("ix_oss_contributions_github_node_id"), table_name="oss_contributions")
    op.drop_table("oss_contributions")
