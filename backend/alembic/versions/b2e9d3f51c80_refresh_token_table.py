"""refresh_tokens table for jti-based rotation (BUGS-02)

Server-side persistence of refresh-token JTIs so /auth/refresh can rotate
atomically and detect replay of revoked tokens.

Revision ID: b2e9d3f51c80
Revises: 7a4f2c8e15d3
Create Date: 2026-06-08

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "b2e9d3f51c80"
down_revision: str | Sequence[str] | None = "7a4f2c8e15d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
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
    op.create_index(op.f("ix_refresh_tokens_user_id"), "refresh_tokens", ["user_id"], unique=False)
    op.create_index(
        op.f("ix_refresh_tokens_expires_at"), "refresh_tokens", ["expires_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_refresh_tokens_expires_at"), table_name="refresh_tokens")
    op.drop_index(op.f("ix_refresh_tokens_user_id"), table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
