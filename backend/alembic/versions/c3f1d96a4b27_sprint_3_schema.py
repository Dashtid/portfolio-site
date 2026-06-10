"""Sprint 3: indexes, server_defaults, bounded lengths

Consolidates the Sprint 3 schema deltas:
- DB-01: server_default on companies/projects/users.updated_at
- DB-02: ix on education.is_certification
- DB-05: bounded VARCHAR lengths on users.github_id / username / email / name
       / avatar_url
- DB-06: server_default on oauth_states.created_at
- DB-09: drop redundant PK-column indexes (oauth_states.state,
         education.id, documents.id)
- PERF-02: ix on oauth_states.expires_at
- PERF-03: composite ix on page_views.(created_at,page_path) and
           page_views.(created_at,country)

DB-07: every CREATE/DROP/ALTER is guarded with an existence check via the
SQLAlchemy inspector so re-running the migration (or running it against a
database that already has some of these from `Base.metadata.create_all`) is
a no-op rather than an error. This is the standard fix for the
fresh-database-vs-stamped-database split logged as DB-07.

Revision ID: c3f1d96a4b27
Revises: b2e9d3f51c80
Create Date: 2026-06-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import inspect

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "c3f1d96a4b27"
down_revision: str | Sequence[str] | None = "b2e9d3f51c80"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# ---- helpers ----------------------------------------------------------------


def _index_names(table: str) -> set[str]:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        return {ix["name"] for ix in insp.get_indexes(table) if ix.get("name")}
    except Exception:
        # Table missing — treat as "no indexes" so subsequent guards skip.
        return set()


def _column_names(table: str) -> set[str]:
    bind = op.get_bind()
    insp = inspect(bind)
    try:
        return {col["name"] for col in insp.get_columns(table)}
    except Exception:
        return set()


def _create_index_if_absent(name: str, table: str, columns: list[str]) -> None:
    if name not in _index_names(table):
        op.create_index(name, table, columns, unique=False)


def _drop_index_if_present(name: str, table: str) -> None:
    if name in _index_names(table):
        op.drop_index(name, table_name=table)


# ---- upgrade / downgrade ----------------------------------------------------


def upgrade() -> None:
    """Upgrade schema."""

    # PERF-02: index oauth_states.expires_at (used by the periodic
    # cleanup_oauth_states_periodically() task every 5 minutes).
    if "expires_at" in _column_names("oauth_states"):
        _create_index_if_absent(op.f("ix_oauth_states_expires_at"), "oauth_states", ["expires_at"])

    # DB-09: drop the redundant explicit index on oauth_states.state — the
    # PK already provides one. Index name SQLAlchemy generated previously.
    _drop_index_if_present(op.f("ix_oauth_states_state"), "oauth_states")

    # DB-06: server_default for oauth_states.created_at. SQLite can't ALTER
    # to add a server default, but batch_alter_table copies the table with
    # the new spec — works on both dialects.
    if "created_at" in _column_names("oauth_states"):
        with op.batch_alter_table("oauth_states") as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                server_default=sa.text("CURRENT_TIMESTAMP"),
                existing_nullable=False,
            )

    # DB-02: index education.is_certification (filtered by public listing).
    if "is_certification" in _column_names("education"):
        _create_index_if_absent(
            op.f("ix_education_is_certification"),
            "education",
            ["is_certification"],
        )

    # DB-09: drop redundant index on education.id / documents.id (both PKs).
    _drop_index_if_present(op.f("ix_education_id"), "education")
    _drop_index_if_present(op.f("ix_documents_id"), "documents")

    # PERF-03: composite indexes for the analytics aggregation queries.
    _create_index_if_absent("ix_page_views_created_path", "page_views", ["created_at", "page_path"])
    _create_index_if_absent(
        "ix_page_views_created_country", "page_views", ["created_at", "country"]
    )

    # DB-05: bound VARCHAR lengths on users.* and DB-01: server_default on
    # users.updated_at. Existing rows are unaffected — SQLite stores all
    # strings as TEXT; Postgres applies the length cap going forward.
    user_cols = _column_names("users")
    if user_cols:
        with op.batch_alter_table("users") as batch_op:
            if "github_id" in user_cols:
                batch_op.alter_column(
                    "github_id",
                    existing_type=sa.String(),
                    type_=sa.String(length=20),
                    existing_nullable=False,
                )
            if "username" in user_cols:
                batch_op.alter_column(
                    "username",
                    existing_type=sa.String(),
                    type_=sa.String(length=39),
                    existing_nullable=False,
                )
            if "email" in user_cols:
                batch_op.alter_column(
                    "email",
                    existing_type=sa.String(),
                    type_=sa.String(length=254),
                    existing_nullable=True,
                )
            if "name" in user_cols:
                batch_op.alter_column(
                    "name",
                    existing_type=sa.String(),
                    type_=sa.String(length=255),
                    existing_nullable=True,
                )
            if "avatar_url" in user_cols:
                batch_op.alter_column(
                    "avatar_url",
                    existing_type=sa.String(),
                    type_=sa.String(length=500),
                    existing_nullable=True,
                )
            if "updated_at" in user_cols:
                batch_op.alter_column(
                    "updated_at",
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                    existing_nullable=True,
                )

    # DB-01: server_default on companies.updated_at + projects.updated_at.
    for table in ("companies", "projects"):
        if "updated_at" in _column_names(table):
            with op.batch_alter_table(table) as batch_op:
                batch_op.alter_column(
                    "updated_at",
                    existing_type=sa.DateTime(timezone=True),
                    server_default=sa.text("CURRENT_TIMESTAMP"),
                    existing_nullable=True,
                )


def downgrade() -> None:
    """Downgrade schema."""

    # Reverse companies/projects updated_at server_default.
    for table in ("companies", "projects"):
        if "updated_at" in _column_names(table):
            with op.batch_alter_table(table) as batch_op:
                batch_op.alter_column(
                    "updated_at",
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=True,
                )

    # Reverse users.* type widening + updated_at server_default.
    user_cols = _column_names("users")
    if user_cols:
        with op.batch_alter_table("users") as batch_op:
            if "updated_at" in user_cols:
                batch_op.alter_column(
                    "updated_at",
                    existing_type=sa.DateTime(timezone=True),
                    server_default=None,
                    existing_nullable=True,
                )
            for col in ("github_id", "username", "email", "name", "avatar_url"):
                if col in user_cols:
                    batch_op.alter_column(
                        col,
                        existing_type=sa.String(length=255),
                        type_=sa.String(),
                        existing_nullable=col not in {"github_id", "username"},
                    )

    # Drop composite page_views indexes.
    _drop_index_if_present("ix_page_views_created_country", "page_views")
    _drop_index_if_present("ix_page_views_created_path", "page_views")

    # Restore the redundant PK indexes that used to exist (idempotent guard).
    if "documents" in inspect(op.get_bind()).get_table_names():
        _create_index_if_absent(op.f("ix_documents_id"), "documents", ["id"])
    if "education" in inspect(op.get_bind()).get_table_names():
        _create_index_if_absent(op.f("ix_education_id"), "education", ["id"])

    # Drop education.is_certification index.
    _drop_index_if_present(op.f("ix_education_is_certification"), "education")

    # Reverse oauth_states.created_at server_default and restore the
    # redundant index on .state.
    if "created_at" in _column_names("oauth_states"):
        with op.batch_alter_table("oauth_states") as batch_op:
            batch_op.alter_column(
                "created_at",
                existing_type=sa.DateTime(timezone=True),
                server_default=None,
                existing_nullable=False,
            )
    if "oauth_states" in inspect(op.get_bind()).get_table_names():
        _create_index_if_absent(op.f("ix_oauth_states_state"), "oauth_states", ["state"])

    # Drop oauth_states.expires_at index.
    _drop_index_if_present(op.f("ix_oauth_states_expires_at"), "oauth_states")
