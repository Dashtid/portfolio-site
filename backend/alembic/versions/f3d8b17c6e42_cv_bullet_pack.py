"""cv bullet pack — rewrite CV bullets, the summary and education strings

Data-only. Every update is guarded on the EXACT current value (list or
string), so a re-run, or a value edited in /admin/cv after this was written,
is never trampled:

- companies.cv_highlights, keyed by start month (YYYY-MM) in _PACK: a row is
  rewritten only when its current list equals the old list exactly. Rows with
  no start_date, or with a start month not in _PACK, are skipped. The 2012-06
  replacement is an EMPTY list, which the export renders as no bullets
  instead of falling back to the site's lists.
- companies.title: "Master Thesis Student" -> "Master's Thesis Student".
- education: the KTH and Lund degree, field_of_study and description strings
  in _EDUCATION_FIXES (suffixes dropped, dash styles changed).
- cv_profile.summary: _SUMMARY_OLD -> _SUMMARY_NEW (see the comment there).

_PACK has no "2024-05" entry. It was removed after this revision had been
applied: c9e2f7a4b681 now carries that role's bullets, and deployed rows are
rewritten by b41f7ac2e905.

An empty companies table skips the bullet loop; the other updates still run,
each with its exact-value guard. Downgrade is a deliberate no-op.

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
    # No "2024-05" entry - see the module docstring.
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
# Two edits in one: "Experienced extending" becomes "Experienced in
# extending", and a closing "Background: ..." sentence is appended
# (c9a4e7b21f83 takes that sentence out again).
_SUMMARY_NEW = (
    "Biomedical Engineer focused on product cybersecurity for regulated medical "
    "software. Experienced in extending STRIDE-based threat models into concrete, "
    "product-specific security requirements and supporting vulnerability evaluation "
    "using SBOM-driven SCA. Comfortable translating FDA premarket cybersecurity "
    "guidance (Section 524B) and IEC 81001-5-1 expectations into structured security "
    "evidence and SDLC improvements. Background: five years across medical imaging "
    "and healthcare IT, in a formal security role since 2024."
)

# Copy fixes, all exact-match guarded like everything above: the "Master
# Thesis Student" title gains its possessive, the degree strings drop their
# " - MS"/" - BS" suffixes, the KTH field's spaced hyphen becomes an en dash,
# and the thesis prefixes use an em dash instead of a spaced hyphen.
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
