"""capture production schema drift accumulated under create_all() bootstrapping.

Prod was originally bootstrapped via Base.metadata.create_all() and never
stamped/upgraded through Alembic. Over time the model evolved (client_ip
was added to oauth_states for CSRF IP-binding, refresh_tokens for token
rotation, oss_contributions for the admin OSS dashboard) but no ALTER
migrations were ever applied to prod. This migration captures everything
that's missing using if-absent guards so it's safe to run on:

  - prod (drifted): creates whatever's missing, leaves the rest alone.
  - fresh databases (created via create_all + stamped): the guards no-op
    since the tables/columns already match the model.
  - dev DBs already at head via the prior chain: same no-op.

Future schema changes should go through proper alembic migrations from
here forward — fly.toml now runs `alembic upgrade head` on every deploy.

Revision ID: e9b1c47d2f86
Revises: d8a4c92b1f73
Create Date: 2026-06-15

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op  # type: ignore[attr-defined]

revision: str = "e9b1c47d2f86"
down_revision: str | Sequence[str] | None = "d8a4c92b1f73"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_exists(table: str) -> bool:
    return inspect(op.get_bind()).has_table(table)


def _column_names(table: str) -> set[str]:
    if not _table_exists(table):
        return set()
    return {col["name"] for col in inspect(op.get_bind()).get_columns(table)}


def _index_names(table: str) -> set[str]:
    if not _table_exists(table):
        return set()
    return {ix["name"] for ix in inspect(op.get_bind()).get_indexes(table) if ix.get("name")}


def upgrade() -> None:
    """Upgrade schema."""

    # Fresh database: skip the whole drift capture — the baseline revision
    # at the head of the chain creates everything at current model spec.
    # Creating refresh_tokens/oss_contributions here first would freeze
    # them at this revision's snapshot instead of the current one.
    if not _table_exists("users"):
        return

    if "client_ip" not in _column_names("oauth_states"):
        op.add_column("oauth_states", sa.Column("client_ip", sa.String(length=45), nullable=True))

    if not _table_exists("refresh_tokens"):
        op.create_table(
            "refresh_tokens",
            sa.Column("jti", sa.String(length=64), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "issued_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                nullable=False,
            ),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        )
    if "ix_refresh_tokens_user_id" not in _index_names("refresh_tokens"):
        op.create_index(
            op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False
        )
    if "ix_refresh_tokens_expires_at" not in _index_names("refresh_tokens"):
        op.create_index(
            op.f("ix_refresh_tokens_expires_at"), "refresh_tokens", ["expires_at"], unique=False
        )

    if not _table_exists("oss_contributions"):
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
    if "ix_oss_contributions_github_node_id" not in _index_names("oss_contributions"):
        op.create_index(
            op.f("ix_oss_contributions_github_node_id"),
            "oss_contributions",
            ["github_node_id"],
            unique=True,
        )
    if "ix_oss_contributions_repo_name_with_owner" not in _index_names("oss_contributions"):
        op.create_index(
            op.f("ix_oss_contributions_repo_name_with_owner"),
            "oss_contributions",
            ["repo_name_with_owner"],
            unique=False,
        )
    if "ix_oss_contributions_bucket" not in _index_names("oss_contributions"):
        op.create_index(
            op.f("ix_oss_contributions_bucket"),
            "oss_contributions",
            ["bucket"],
            unique=False,
        )
    if "ix_oss_contributions_bucket_repo_activity" not in _index_names("oss_contributions"):
        op.create_index(
            "ix_oss_contributions_bucket_repo_activity",
            "oss_contributions",
            ["bucket", "repo_name_with_owner", "last_activity_at"],
            unique=False,
        )


def downgrade() -> None:
    """Downgrade schema.

    Reverses each step only when the corresponding object exists, so the
    downgrade is also safe on partially-drifted databases.
    """

    if _table_exists("oss_contributions"):
        op.drop_table("oss_contributions")
    if _table_exists("refresh_tokens"):
        op.drop_table("refresh_tokens")
    if "client_ip" in _column_names("oauth_states"):
        op.drop_column("oauth_states", "client_ip")
