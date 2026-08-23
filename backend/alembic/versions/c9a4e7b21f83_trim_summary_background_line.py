"""trim the summary's two-clocks tail — owner review verdict 2026-08-23

The f3d8b17c6e42 pack appended "Background: five years across medical
imaging and healthcare IT, in a formal security role since 2024." to the
CV summary. On review the owner rejected exactly that sentence ("I dont
like this part") and approved everything else, so this migration takes
the tail back out and nothing more.

Guarded on the EXACT post-pack summary, so an owner edit made in
/admin/cv after the pack landed is never trampled. Fresh databases are
seeded with the trimmed text directly; this only converges databases the
pack already touched. Downgrade is a deliberate no-op.

Revision ID: c9a4e7b21f83
Revises: f3d8b17c6e42
Create Date: 2026-08-23

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "c9a4e7b21f83"
down_revision: str | Sequence[str] | None = "f3d8b17c6e42"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_SUMMARY_WITH_TAIL = (
    "Biomedical Engineer focused on product cybersecurity for regulated medical "
    "software. Experienced in extending STRIDE-based threat models into concrete, "
    "product-specific security requirements and supporting vulnerability evaluation "
    "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
    "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
    "evidence and SDLC improvements. Background: five years across medical imaging "
    "and healthcare IT, in a formal security role since 2024."
)

_SUMMARY_TRIMMED = (
    "Biomedical Engineer focused on product cybersecurity for regulated medical "
    "software. Experienced in extending STRIDE-based threat models into concrete, "
    "product-specific security requirements and supporting vulnerability evaluation "
    "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
    "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
    "evidence and SDLC improvements."
)

_cv_profile = sa.table(
    "cv_profile",
    sa.column("id", sa.Integer()),
    sa.column("summary", sa.Text()),
)


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()
    bind.execute(
        _cv_profile.update()
        .where(_cv_profile.c.summary == _SUMMARY_WITH_TAIL)
        .values(summary=_SUMMARY_TRIMMED)
    )


def downgrade() -> None:
    """Deliberate no-op — the trim is a content decision, not schema."""
