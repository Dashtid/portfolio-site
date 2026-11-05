"""skills keyword sync — converge an EXISTING skills table to the seed_data.py keywords

seed_skills() early-returns on any populated table, so a deploy alone never
changes the skills rows of an existing database. This migration applies the
seed_data.py keyword changes to such a database; it reaches prod through the
same release_command path as every schema change.

Deliberately narrow so it can never trample admin-curated content (the
migrate_data.py lesson): it only touches the rows named below, only when the
table is already populated, and every operation is guarded:

- EMPTY table -> no-op (fresh DBs are seed_skills() territory; inserting
  here would trip _already_seeded and suppress the rest of the seed).
- Rename "Vulnerability Assessment" -> "Vulnerability Management" (keeps the
  row's curated proficiency/order); if the new name already exists the old
  row is deleted instead (unique name constraint).
- Delete "ISO 27001" and "OWASP" by exact name.
- Insert each row in _ADD with the values listed there; each insert is
  skipped when a row with that name exists.

Idempotent: a re-run finds nothing left to do. Downgrade is a deliberate
no-op: the pre-sync proficiency values of deleted rows are not recorded here.

Revision ID: b5d21e04c7a9
Revises: a7c3e58d19f4
Create Date: 2026-08-13

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "b5d21e04c7a9"
down_revision: str | Sequence[str] | None = "a7c3e58d19f4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_skills = sa.table(
    "skills",
    sa.column("id", sa.String()),
    sa.column("name", sa.String()),
    sa.column("category", sa.String()),
    sa.column("proficiency_level", sa.Integer()),
    sa.column("years_of_experience", sa.Float()),
    sa.column("order_index", sa.Integer()),
)

_DELETE = ("ISO 27001", "OWASP")
_RENAME = {"Vulnerability Assessment": "Vulnerability Management"}
# (name, category, proficiency, years, order_index) — values mirror
# seed_data.py; proficiency/years are admin-only and never publicly rendered.
_ADD = (
    ("Vulnerability Management", "Security", 85, 4, 14),
    ("Application Security", "Security", 85, 4, 15),
    ("Threat Modeling", "Security", 85, 3, 16),
    ("Secure SDLC", "Security", 85, 3, 17),
    ("Software Supply-Chain Security (SBOM)", "Security", 85, 3, 18),
    ("NIS 2", "Security", 75, 2, 19),
    ("IEC 81001-5-1", "Medical", 85, 3, 21),
    ("GAMP 5", "Medical", 80, 3, 22),
)


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    count = bind.execute(sa.select(sa.func.count()).select_from(_skills)).scalar_one()
    if not count:
        # Fresh DB: leave the table to seed_skills(), which owns the full
        # canonical set. Inserting here would make _already_seeded skip it.
        return

    existing = set(bind.execute(sa.select(_skills.c.name)).scalars())

    for old, new in _RENAME.items():
        if old in existing:
            if new in existing:
                bind.execute(_skills.delete().where(_skills.c.name == old))
            else:
                bind.execute(_skills.update().where(_skills.c.name == old).values(name=new))
                existing.add(new)
            existing.discard(old)

    for name in _DELETE:
        if name in existing:
            bind.execute(_skills.delete().where(_skills.c.name == name))
            existing.discard(name)

    for name, category, proficiency, years, order_index in _ADD:
        if name in existing:
            continue
        bind.execute(
            _skills.insert().values(
                # id has a Python-side default only — a core insert must
                # supply it explicitly.
                id=str(uuid.uuid4()),
                name=name,
                category=category,
                proficiency_level=proficiency,
                years_of_experience=years,
                order_index=order_index,
            )
        )
        existing.add(name)


def downgrade() -> None:
    """Deliberate no-op — see module docstring."""
