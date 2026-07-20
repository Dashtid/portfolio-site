"""add companies.outcomes (D3-UX-03)

Quantified outcome bullets per role, stored like responsibilities /
technologies: a nullable JSON list of strings. Guarded add_column because
non-production environments may already carry the column via the
create_all() bootstrap before this revision runs.

Revision ID: f2b8d61c4a93
Revises: da9f04bf81a7
Create Date: 2026-07-20

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "f2b8d61c4a93"
down_revision: str | Sequence[str] | None = "da9f04bf81a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("companies")}
    if "outcomes" not in columns:
        op.add_column("companies", sa.Column("outcomes", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    inspector = sa.inspect(op.get_bind())
    columns = {col["name"] for col in inspector.get_columns("companies")}
    if "outcomes" in columns:
        op.drop_column("companies", "outcomes")
