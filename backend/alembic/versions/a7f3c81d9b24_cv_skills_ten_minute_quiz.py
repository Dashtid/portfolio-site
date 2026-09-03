"""skills: apply the owner's ten-minute-quiz rule to the site

Owner rule, set 2026-08-29 during the LinkedIn alignment and recorded in
cv/source/linkedin-alignment-2026-08-29.txt: a skill is listed only if the
owner would be comfortable being quizzed on it for ten minutes. He applied it
to LinkedIn himself that day and did NOT list SQL, JavaScript, TypeScript,
FastAPI or Vue.js. The CV followed on 2026-09-03 (01bbb99). This migration is
the third and last surface — the site's skills table — so the three no longer
disagree.

DELETE: JavaScript/TypeScript, SQL, FastAPI, Vue.js.
Programming is left with Python and Bash/PowerShell, which is the honest set.

What deliberately does NOT change, because it is a different kind of claim:
the "Portfolio Site" project row keeps `technologies` = Vue.js, TypeScript,
FastAPI, PostgreSQL, Docker, CI/CD, and its description still says the site is
built with Vue 3 + TypeScript and FastAPI + PostgreSQL. That is a fact about
the artifact, not a claim about the author, and the owner ruled it stays
(2026-08-29, restated 2026-09-03). Deleting a skill row does not hide how the
site is built; it stops the stack being sold as expertise.

Renumbering: order_index is renumbered 1..17 over the surviving rows in their
existing relative order, because the CV export derives CATEGORY order from the
first row it meets per category after ORDER BY order_index. Leaving four holes
would not break that, but a contiguous set is what every previous skills
migration has left behind and drift here is invisible until the CV reorders
itself. Names not listed (future owner additions) are untouched.

Same shape as b5d21e04c7a9 and d4b7a91c3e58: data-only, narrow, idempotent,
EMPTY table -> no-op (fresh DBs belong to seed_data.py, which carries the same
set). Downgrade is a deliberate no-op — re-adding claims the owner declined to
make is not a rollback anyone wants.

Revision ID: a7f3c81d9b24
Revises: c9a4e7b21f83
Create Date: 2026-09-03

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "a7f3c81d9b24"
down_revision: str | Sequence[str] | None = "c9a4e7b21f83"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_skills = sa.table(
    "skills",
    sa.column("id", sa.String()),
    sa.column("name", sa.String()),
    sa.column("category", sa.String()),
    sa.column("order_index", sa.Integer()),
)

_DELETE = ("JavaScript/TypeScript", "SQL", "FastAPI", "Vue.js")

# The surviving 17 in their current prod order, renumbered contiguously.
# Category order is load-bearing (Programming, DevOps, Security Engineering,
# Regulatory & Standards Compliance, Healthcare IT) — it is what the CV prints.
_ORDER = (
    "Python",
    "Bash/PowerShell",
    "Docker",
    "Kubernetes",
    "GitHub Actions",
    "Application Security",
    "Threat Modeling",
    "Secure SDLC",
    "Software Supply-Chain Security (SBOM)",
    "Vulnerability Management",
    "FDA Premarket Cybersecurity (524B)",
    "IEC 81001-5-1",
    "IEC 62304",
    "GAMP 5",
    "NIS 2",
    "DICOM",
    "HL7",
)


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    count = bind.execute(sa.select(sa.func.count()).select_from(_skills)).scalar_one()
    if not count:
        return  # fresh DB — seed_data.py already carries the corrected set

    existing = set(bind.execute(sa.select(_skills.c.name)).scalars())

    for name in _DELETE:
        if name in existing:
            bind.execute(_skills.delete().where(_skills.c.name == name))
            existing.discard(name)

    for index, name in enumerate(_ORDER, start=1):
        if name in existing:
            bind.execute(_skills.update().where(_skills.c.name == name).values(order_index=index))


def downgrade() -> None:
    """Downgrade schema — deliberate no-op.

    The upgrade removes claims the owner declined to make about himself.
    Restoring them would re-publish an overclaim, which is never the rollback
    anyone actually wants; the order_index renumbering is cosmetic and its
    previous values carried duplicate-tie problems of their own.
    """
