"""cv skills taxonomy — stop filing security standards under "Medical"

Owner, 2026-08-22: "isn't a bunch of these medical ones also security
frameworks? Feels weird calling them medical." He is right, and his own
hand-made CV already had the honest split. The old "Medical" bucket mixed
three different kinds of thing: security/lifecycle STANDARDS (IEC 81001-5-1
is a health-software security standard, FDA 524B is statutory premarket
cybersecurity, IEC 62304 lifecycle, GAMP 5 validation) and interoperability
PROTOCOLS (DICOM, HL7). NIS 2 sat under "Security" but is a directive, not a
practice. Regrouped:

- Programming            <- Programming + Frameworks merged (six items; a
                            two-item "Frameworks" group earned its label
                            nothing)
- DevOps                 (unchanged)
- Security Engineering   <- "Security" minus NIS 2: the hands-on practice
                            areas only
- Regulatory & Standards Compliance <- NIS 2 + IEC 62304 + IEC 81001-5-1 + GAMP 5 +
                            FDA 524B (strongest first: the FDA/81001 pair is
                            the core of the current role)
- Healthcare IT          <- DICOM + HL7

Same pattern as d4b7a91c3e58: data-only, keyed on exact names, idempotent,
EMPTY table -> no-op (seed_data.py carries the same set for fresh DBs),
no-op downgrade. Rows this migration does not know by name keep their
category and order untouched.

Revision ID: e7c9d24a5b13
Revises: d4b7a91c3e58
Create Date: 2026-08-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "e7c9d24a5b13"
down_revision: str | Sequence[str] | None = "d4b7a91c3e58"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_skills = sa.table(
    "skills",
    sa.column("name", sa.String()),
    sa.column("category", sa.String()),
    sa.column("order_index", sa.Integer()),
)

# name -> (category, order_index); the full canonical set, mirrored in
# seed_data.py and cv/resume.json. Category order on the CV follows the
# lowest order_index per category.
_TAXONOMY = {
    "Python": ("Programming", 1),
    "JavaScript/TypeScript": ("Programming", 2),
    "SQL": ("Programming", 3),
    "Bash/PowerShell": ("Programming", 4),
    "FastAPI": ("Programming", 5),
    "Vue.js": ("Programming", 6),
    "Docker": ("DevOps", 7),
    "Kubernetes": ("DevOps", 8),
    "GitHub Actions": ("DevOps", 9),
    "Application Security": ("Security Engineering", 10),
    "Threat Modeling": ("Security Engineering", 11),
    "Secure SDLC": ("Security Engineering", 12),
    "Software Supply-Chain Security (SBOM)": ("Security Engineering", 13),
    "Vulnerability Management": ("Security Engineering", 14),
    "FDA Premarket Cybersecurity (524B)": ("Regulatory & Standards Compliance", 15),
    "IEC 81001-5-1": ("Regulatory & Standards Compliance", 16),
    "IEC 62304": ("Regulatory & Standards Compliance", 17),
    "GAMP 5": ("Regulatory & Standards Compliance", 18),
    "NIS 2": ("Regulatory & Standards Compliance", 19),
    "DICOM": ("Healthcare IT", 20),
    "HL7": ("Healthcare IT", 21),
}


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    count = bind.execute(sa.select(sa.func.count()).select_from(_skills)).scalar_one()
    if not count:
        # Fresh DB: seed_skills() owns the canonical set.
        return

    for name, (category, order_index) in _TAXONOMY.items():
        bind.execute(
            _skills.update()
            .where(_skills.c.name == name)
            .values(category=category, order_index=order_index)
        )


def downgrade() -> None:
    """Deliberate no-op — the old grouping was the defect."""
