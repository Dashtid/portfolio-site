"""user.is_admin NOT NULL with server_default false (DB-04)

Backfills any NULL rows to False, then enforces NOT NULL with a server
default. Prevents the BUGS-01 family of fail-open scenarios where a row
inserted out-of-band ends up with NULL and `if user.is_admin` reads as
unset rather than admin/non-admin.

Revision ID: 7a4f2c8e15d3
Revises: 19fd54de976f
Create Date: 2026-06-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "7a4f2c8e15d3"
down_revision: str | Sequence[str] | None = "19fd54de976f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Fresh database (no legacy schema): skip. The baseline revision at
    # the head of the chain creates every table at current model spec —
    # replaying this historical delta against nothing just crashes. Same
    # early-out pattern as the root revision.
    if not sa.inspect(op.get_bind()).has_table("users"):
        return

    # Backfill any pre-existing NULL rows before tightening the constraint.
    op.execute("UPDATE users SET is_admin = 0 WHERE is_admin IS NULL")
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "is_admin",
            existing_type=sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "is_admin",
            existing_type=sa.Boolean(),
            nullable=True,
            server_default=None,
        )
