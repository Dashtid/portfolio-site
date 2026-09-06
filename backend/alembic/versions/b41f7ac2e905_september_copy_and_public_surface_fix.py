"""September 2026 CV copy — and a public-surface confidentiality fix

Applies the copy approved in career-plan `applications/copy-pack-2026-09.md`
(revision 2, 2026-09-06) to the deployed database. Three things change:

1. `companies.cv_highlights` for the Hermes role — the three-bullet set is
   replaced by the approved eight. The bullet it removes named the employer's
   imaging protocol beside the dynamic-testing technique, which is the pair the
   owner's public-surface rule exists to prevent, on a row that renders next to
   the employer's name.
2. `companies.description` for the same row — "regulated nuclear-medicine
   software" becomes "regulated medical software". The product category is not
   the owner's to publish, and it renders on the same page as the testing work.
3. `cv_profile.label` and `cv_profile.summary` — the September rewrite. The
   summary gains the authorship claim it never had (the August audit's defect
   #1) and the EU AI Act clause; the label gains the standards string.

[!] The Hermes row is updated UNCONDITIONALLY, which deliberately breaks this
repo's guard-on-the-exact-current-value convention (see c9a4e7b21f83 and
f3d8b17c6e42 for the normal pattern). The convention exists so an owner edit
made through /admin/cv is never trampled. It cannot be followed here: writing
the guard would mean committing the exact string this migration exists to
remove, putting it back into a public repo's tracked tree and into every future
clone. A confidentiality fix that preserves the text it is removing is not a
fix. Trampling an admin edit is the accepted cost, and it is the correct
direction — any admin edit descended from the old bullets carries the same
problem.

`cv_profile` keeps the normal guard: its current values contain nothing
sensitive, so the exact-match guard is free.

Empty tables -> no-op. Downgrade is a deliberate no-op: restoring the previous
text would restore the disclosure.

Revision ID: b41f7ac2e905
Revises: a7f3c81d9b24
Create Date: 2026-09-06

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "b41f7ac2e905"
down_revision: str | Sequence[str] | None = "a7f3c81d9b24"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_HERMES = "Hermes Medical Solutions"

_HIGHLIGHTS = [
    "Author product cybersecurity documentation supporting regulatory submissions "
    "- threat models, security risk assessments and premarket security evidence - "
    "inside an ISO 13485 quality system.",
    "Build and present every product STRIDE threat model, and translate them into "
    "traceable, product-specific security requirements.",
    "Run gap analyses against IEC 81001-5-1 and FDA premarket cybersecurity "
    "requirements (FD&C Act section 524B), and drive the secure-SDLC improvements "
    "that come out of them.",
    "Compile SBOMs by hand from SOUP lists and shipped artifacts, at artifact level "
    "and on demand, and analyze them with Grype; triage findings into risk "
    "assessments and post-market surveillance.",
    "Authored the product's build-time security analyzer ruleset (Roslyn CA rules, "
    "warning-level), derived from the threat model so that every enabled rule "
    "traces to a modelled threat.",
    "Introduced black-box dynamic security testing into the product verification approach.",
    "EU AI Act readiness is the other named half of the role: the applicability and "
    "gap assessment has started, and Article 15 - accuracy, robustness, "
    "cybersecurity - is where it extends the product-security work.",
    "Began the organization's ISO 27001-aligned ISMS build-out, extending the remit "
    "from product security to the organization around it.",
]

_DESCRIPTION = (
    "Product security for regulated medical software: threat modeling, FDA premarket "
    "security documentation, IEC 81001-5-1 secure-lifecycle work, SBOM and vulnerability "
    "management — alongside QA/RA responsibility for V&V and market clearance."
)

_LABEL_OLD = "Product & Application Security Engineer — Regulated Medical Software"
_LABEL_NEW = (
    "Product & Application Security Engineer — Regulated Medical Software "
    "(FDA 524B, IEC 81001-5-1, EU AI Act)"
)

_SUMMARY_OLD = (
    "Biomedical Engineer focused on product cybersecurity for regulated medical "
    "software. Experienced in extending STRIDE-based threat models into concrete, "
    "product-specific security requirements and supporting vulnerability evaluation "
    "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
    "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
    "evidence and SDLC improvements."
)

_SUMMARY_NEW = (
    "Security specialist in regulated medical software. Since 2024 I have authored the "
    "product cybersecurity evidence inside a medical-device manufacturer's ISO 13485 "
    "quality system — threat models, security risk assessments and the premarket "
    "security documentation — against FDA premarket cybersecurity requirements "
    "(FD&C Act section 524B) and IEC 81001-5-1. EU AI Act readiness is the other named "
    "half of the role, and the applicability and gap assessment has started: Article "
    "15's accuracy, robustness and cybersecurity requirements extend the same evidence "
    "work to a second regulatory regime."
)

_companies = sa.table(
    "companies",
    sa.column("id", sa.Integer()),
    sa.column("name", sa.String()),
    sa.column("description", sa.Text()),
    sa.column("cv_highlights", sa.JSON()),
)

_cv_profile = sa.table(
    "cv_profile",
    sa.column("id", sa.Integer()),
    sa.column("label", sa.String()),
    sa.column("summary", sa.Text()),
)


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    # Unconditional on the Hermes row - see the module docstring for why the
    # exact-value guard is deliberately not used here.
    bind.execute(
        _companies.update()
        .where(_companies.c.name == _HERMES)
        .values(cv_highlights=_HIGHLIGHTS, description=_DESCRIPTION)
    )

    bind.execute(
        _cv_profile.update()
        .where(_cv_profile.c.summary == _SUMMARY_OLD)
        .values(summary=_SUMMARY_NEW)
    )
    bind.execute(
        _cv_profile.update().where(_cv_profile.c.label == _LABEL_OLD).values(label=_LABEL_NEW)
    )


def downgrade() -> None:
    """Deliberate no-op - reverting would restore the disclosure."""
