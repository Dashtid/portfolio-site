"""cv skills accuracy — prune claims the owner's work cannot back

Owner directive 2026-08-22: "be more accurate with my skills — we really
don't want to overclaim; less is more." Every row was checked against the
owner's actual repositories and the career-plan defensible-claims register
before this migration was written:

- DELETE Django and React: no code in any repo, personal or public — the
  frameworks actually in use are FastAPI and Vue.js, which stay.
- DELETE Azure: no Azure workload anywhere (the OIDC corpus covers Azure
  federated-credential *trust semantics*, offline — that is not "Azure").
  This also empties the Cloud category, which then disappears from the CV.
- DELETE Security Auditing: the vaguest term in the table at the highest
  self-rating; the register's approved framing is "regulatory cybersecurity
  documentation and gap analyses", which lives in the experience bullets.
- RENAME HL7/FHIR -> HL7: the Karolinska integration work was HL7; nothing
  anywhere demonstrates FHIR.
- ADD FDA Premarket Cybersecurity (524B): Tier-1 work-with (core of the
  Hermes role, already claimed verbatim in the CV summary and the owner's
  hand-made CV) — the strongest claim was the one missing from the table.
- education: degree "Security+ Certification" -> "Security+" on the CompTIA
  row (the CV renders it under a "Certificates" heading; the suffix was
  tautological there and on the admin table).
- cv_profile.focus: drop "(OIDC/IAM, AWS/Terraform)" for the evidence-backed
  OIDC wording — there is no AWS or Terraform work anywhere, while the OIDC
  trust-policy research is real and current. Guarded on the exact previous
  string so an owner-edited focus is never trampled.

Same shape as b5d21e04c7a9 (skills keyword sync): data-only, narrow,
idempotent, EMPTY table -> no-op (fresh DBs belong to seed_data.py, which
carries the same set). Downgrade is a deliberate no-op — re-adding unbacked
claims is never a rollback anyone wants.

Revision ID: d4b7a91c3e58
Revises: c9e2f7a4b681
Create Date: 2026-08-22

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "d4b7a91c3e58"
down_revision: str | Sequence[str] | None = "c9e2f7a4b681"
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

_education = sa.table(
    "education",
    sa.column("institution", sa.String()),
    sa.column("degree", sa.String()),
)

_cv_profile = sa.table(
    "cv_profile",
    sa.column("id", sa.Integer()),
    sa.column("focus", sa.Text()),
)

_DELETE = ("Django", "React", "Azure", "Security Auditing")
_RENAME = {"HL7/FHIR": "HL7"}
# (name, category, proficiency, years, order_index) — mirrors seed_data.py;
# proficiency/years are admin-only and never publicly rendered.
_ADD = (("FDA Premarket Cybersecurity (524B)", "Medical", 85, 2, 25),)

_CERT_OLD, _CERT_NEW = "Security+ Certification", "Security+"

# Prod carries duplicate order_index values (17, 18, 19 each twice — left by
# the b5d21e04c7a9 inserts), and the CV export derives its CATEGORY order from
# the first row it meets per category after ORDER BY order_index — a tie makes
# Security-vs-Medical section order database-luck. Renumber the known set
# deterministically; names not listed (future owner additions) are untouched.
_ORDER = (
    "Python",
    "JavaScript/TypeScript",
    "SQL",
    "Bash/PowerShell",
    "FastAPI",
    "Vue.js",
    "Docker",
    "Kubernetes",
    "GitHub Actions",
    "Vulnerability Management",
    "Application Security",
    "Threat Modeling",
    "Secure SDLC",
    "Software Supply-Chain Security (SBOM)",
    "NIS 2",
    "IEC 62304",
    "IEC 81001-5-1",
    "GAMP 5",
    "FDA Premarket Cybersecurity (524B)",
    "DICOM",
    "HL7",
)

_FOCUS_OLD = (
    "Cloud & CI/CD security (OIDC/IAM, AWS/Terraform) and secure-SDLC for regulated software"
)
_FOCUS_NEW = (
    "CI/CD and workload-identity security (OIDC trust policies) and secure SDLC "
    "for regulated software"
)


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    count = bind.execute(sa.select(sa.func.count()).select_from(_skills)).scalar_one()
    if count:
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

        for index, name in enumerate(_ORDER, start=1):
            if name in existing:
                bind.execute(
                    _skills.update().where(_skills.c.name == name).values(order_index=index)
                )

    bind.execute(
        _education.update()
        .where(_education.c.institution == "CompTIA")
        .where(_education.c.degree == _CERT_OLD)
        .values(degree=_CERT_NEW)
    )

    bind.execute(
        _cv_profile.update().where(_cv_profile.c.focus == _FOCUS_OLD).values(focus=_FOCUS_NEW)
    )


def downgrade() -> None:
    """Deliberate no-op — see module docstring."""
