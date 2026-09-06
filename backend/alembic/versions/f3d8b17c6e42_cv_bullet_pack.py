"""cv bullet pack — the owner-approved round-2 rewrites and trims

Approved by the owner 2026-08-22 ("apply it") from the round-2 audit, which
checked every proposal against the career-plan defensible-claims register:

- Hermes #1: filler "actionable" dropped (redundant beside "traceable");
  simple present replaces the participle opener.
- Hermes #2: leading verb aligned to the same voice; the register-exact
  content (manual, artifact-level SBOM/SCA, no CI claim) is untouched.
- Hermes #3: three ideas untangled, ~15 words shorter, every claim kept
  (advocated — not gated; dynamic testing introduced — no ownership claim).

[!] 2026-09-06: the Hermes ("2024-05") entry was REMOVED from _PACK below, and
this docstring's description of it is retained only as history. Both halves of
that tuple named the employer's imaging protocol beside the dynamic-testing
technique — the banned public-surface pair — on rows that render publicly next
to the employer's name. The approved September copy is now seeded directly by
c9e2f7a4b681, and deployed databases are corrected by a later forward migration;
this entry had nothing left to do and could only carry the strings forward.
- Philips: pair merged into one bullet and "Spearheaded" removed — a cliché
  AND an overclaim for L1 support. "IIG" (unexplained acronym) dropped;
  under-claiming scope is the safe direction. Support work stays support
  work, per the register.
- SoftPro: "Drove digital transformation" (the CV's worst cliché) replaced
  with what actually happened; "inventory system" matches the site's own
  description of Medusa.
- FDF: the two command bullets collapse into one (both honest numbers
  survive); officer training keeps its own line, de-filled.
- Scania 2012: trimmed to title + dates — an EMPTY list, which the export
  now honours as "deliberately no bullets" instead of falling back to the
  site's lists. Bullet count 13 -> 10, weight shifted toward the security
  role (support-era bullets no longer outnumber security-era 10:3).
- Summary gains the two-clocks line, pre-empting the "only two years of
  security?" ambush with the register's own framing — and "Experienced
  extending" becomes "Experienced in extending" (final-sweep proofread).
- Final-sweep copy polish: "Master's Thesis Student" (possessive), degree
  strings drop their redundant " - MS"/" - BS" suffixes, and the document's
  three competing dash styles converge (en dash inside the KTH field, em
  dash before thesis titles, matching the header and Certificates line).

Every update is guarded on the EXACT current value (list or string), so an
owner edit made after this was written is never trampled. Empty companies
table -> no-op. Downgrade is a deliberate no-op.

Revision ID: f3d8b17c6e42
Revises: e7c9d24a5b13
Create Date: 2026-08-22

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "f3d8b17c6e42"
down_revision: str | Sequence[str] | None = "e7c9d24a5b13"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# start month (YYYY-MM) -> (exact current bullets, replacement bullets).
_PACK: dict[str, tuple[list[str], list[str]]] = {
    # "2024-05" (Hermes) removed 2026-09-06 - see the note in the module docstring.
    "2022-03": (
        [
            "Spearheaded Level 1 support for image processing systems in healthcare IT "
            "across Nordics, UK&I, and IIG.",
            "Collaborated with installation teams to resolve support cases and improve "
            "system integrations.",
        ],
        [
            "Provided Level 1 support for medical image processing systems across the "
            "Nordics and UK & Ireland, handling the full incident lifecycle and "
            "collaborating with installation teams on system integrations.",
        ],
    ),
    "2020-10": (
        [
            "Drove digital transformation by integrating Medusa with the workflow for "
            "maintenance of radiology equipment, enhancing QA processes.",
        ],
        [
            "Integrated the Medusa inventory system into the radiology equipment "
            "maintenance workflow (master's thesis), improving QA processes.",
        ],
    ),
    "2014-01": (
        [
            "Day-to-day command of 150 soldiers.",
            "Field operation command of 30 soldiers.",
            "In-depth officer training in stress resilience and organizational skills.",
        ],
        [
            "Day-to-day command of 150 soldiers; field-operation command of 30.",
            "Completed officer training in stress resilience and organizational leadership.",
        ],
    ),
    "2012-06": (
        [
            "Supported a team of engineers and technicians, acquiring foundational "
            "troubleshooting skills.",
        ],
        [],
    ),
}

_SUMMARY_OLD = (
    "Biomedical Engineer focused on product cybersecurity for regulated medical "
    "software. Experienced extending STRIDE-based threat models into concrete, "
    "product-specific security requirements and supporting vulnerability evaluation "
    "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
    "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
    "evidence and SDLC improvements."
)
# Two edits in one: the final-sweep proofread's "Experienced IN extending"
# (standard collocation), and the two-clocks tail.
_SUMMARY_NEW = (
    "Biomedical Engineer focused on product cybersecurity for regulated medical "
    "software. Experienced in extending STRIDE-based threat models into concrete, "
    "product-specific security requirements and supporting vulnerability evaluation "
    "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
    "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
    "evidence and SDLC improvements. Background: five years across medical imaging "
    "and healthcare IT, in a formal security role since 2024."
)

# Final-sweep copy polish, all exact-match guarded like everything above:
# the SoftPro title gains its possessive, the degree strings drop their
# redundant " - MS"/" - BS" suffixes, the KTH field's spaced hyphen becomes
# an en dash, and the thesis prefixes use the document's em dash instead of
# a spaced hyphen (the sweep found three dash styles doing one job).
_TITLE_FIX = ("Master Thesis Student", "Master's Thesis Student")

# Each entry reads: institution, column name, exact old value, new value.
_EDUCATION_FIXES: tuple[tuple[str, str, str, str], ...] = (
    ("KTH Royal Institute of Technology", "degree", "Master of Science - MS", "Master of Science"),
    (
        "KTH Royal Institute of Technology",
        "field_of_study",
        "Biomedical Engineering - Computer Science",
        "Biomedical Engineering – Computer Science",
    ),
    (
        "KTH Royal Institute of Technology",
        "description",
        "Master's Thesis - 'Improving Quality Assurance of Radiology Equipment Using "
        "Process Modelling and Multi-actor System Analysis'",
        "Master's Thesis — 'Improving Quality Assurance of Radiology Equipment Using "
        "Process Modelling and Multi-actor System Analysis'",
    ),
    ("Lund University", "degree", "Bachelor of Science - BS", "Bachelor of Science"),
    (
        "Lund University",
        "description",
        "Bachelor's Thesis - 'Development of a User-friendly Method of Processing Data "
        "from Ergonomics Measurements Utilizing Inclinometers'",
        "Bachelor's Thesis — 'Development of a User-friendly Method of Processing Data "
        "from Ergonomics Measurements Utilizing Inclinometers'",
    ),
)

_companies = sa.table(
    "companies",
    sa.column("id", sa.String()),
    sa.column("title", sa.String()),
    sa.column("start_date", sa.DateTime()),
    sa.column("cv_highlights", sa.JSON()),
)

_education = sa.table(
    "education",
    sa.column("institution", sa.String()),
    sa.column("degree", sa.String()),
    sa.column("field_of_study", sa.String()),
    sa.column("description", sa.Text()),
)

_cv_profile = sa.table(
    "cv_profile",
    sa.column("id", sa.Integer()),
    sa.column("summary", sa.Text()),
)


def upgrade() -> None:
    """Upgrade schema (data-only)."""
    bind = op.get_bind()

    rows = bind.execute(
        sa.select(_companies.c.id, _companies.c.start_date, _companies.c.cv_highlights)
    ).fetchall()
    # Empty table = a fresh database; nothing to converge.
    if rows:
        for row in rows:
            if row.start_date is None:
                continue
            key = f"{row.start_date.year:04d}-{row.start_date.month:02d}"
            pack = _PACK.get(key)
            if pack is None:
                continue
            old, new = pack
            if row.cv_highlights != old:
                # Owner edited this role since the pack was written — theirs wins.
                continue
            bind.execute(
                _companies.update().where(_companies.c.id == row.id).values(cv_highlights=new)
            )

    bind.execute(
        _companies.update().where(_companies.c.title == _TITLE_FIX[0]).values(title=_TITLE_FIX[1])
    )

    for institution, column, old_value, new_value in _EDUCATION_FIXES:
        bind.execute(
            _education.update()
            .where(_education.c.institution == institution)
            .where(getattr(_education.c, column) == old_value)
            .values(**{column: new_value})
        )

    bind.execute(
        _cv_profile.update()
        .where(_cv_profile.c.summary == _SUMMARY_OLD)
        .values(summary=_SUMMARY_NEW)
    )


def downgrade() -> None:
    """Deliberate no-op — the pack is a content decision, not schema."""
