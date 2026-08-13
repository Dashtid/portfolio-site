"""cv_profile.other_items — Övrigt/Other logistics lines on the CV

CV-generator data requirements (career-plan session 2026-08-06, applied
2026-08-13): "B-körkort" must render as a one-line logistics item at the
BOTTOM of the CV, and must never appear in any certifications section. It
gets its own column — a flat JSON list of strings rendered under "Other" —
so no assembly step can ever classify it as a credential.

Guarded add_column because non-production environments may already carry the
column via the create_all() bootstrap before this revision runs.

The backfill sets the singleton row's value only in the branch where the
column was just added: every row then holds the server default '[]', so the
update cannot clobber owner-entered data. Existing prod reaches this via the
release_command upgrade path (the seed script is NOT re-run there); fresh
DBs get the same value from seed_cv_profile() instead.

Revision ID: a7c3e58d19f4
Revises: f4a1c9d20e57
Create Date: 2026-08-13

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "a7c3e58d19f4"
down_revision: str | Sequence[str] | None = "f4a1c9d20e57"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_DEFAULT_OTHER_ITEMS = ["B-körkort (category B driving licence)"]


def upgrade() -> None:
    """Upgrade schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("cv_profile")}
    if "other_items" in columns:
        return
    op.add_column(
        "cv_profile",
        sa.Column("other_items", sa.JSON(), nullable=False, server_default="[]"),
    )
    # Lightweight table construct so SQLAlchemy's JSON type serializes the
    # list correctly on both Postgres (prod) and SQLite (tests).
    cv_profile = sa.table(
        "cv_profile",
        sa.column("id", sa.Integer()),
        sa.column("other_items", sa.JSON()),
    )
    op.execute(
        cv_profile.update().where(cv_profile.c.id == 1).values(other_items=_DEFAULT_OTHER_ITEMS)
    )


def downgrade() -> None:
    """Downgrade schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {c["name"] for c in inspector.get_columns("cv_profile")}
    if "other_items" in columns:
        op.drop_column("cv_profile", "other_items")
