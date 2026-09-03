"""Tests for the a7f3c81d9b24 ten-minute-quiz skills migration.

test_migration_drift only proves the EMPTY-table path (a fresh DB upgrades to
head). This migration exists for the opposite case: pruning an already
POPULATED prod ``skills`` table that seed_data can never reach, so the site
stops claiming four things the owner declined to claim on LinkedIn (2026-08-29)
and on the CV (2026-09-03). These run the real upgrade() against sync in-memory
SQLite and assert the semantics that matter — the four gone, the survivors
renumbered contiguously without disturbing category order, owner-added rows
left alone, empty table untouched, idempotent, downgrade a genuine no-op.
"""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "a7f3c81d9b24_cv_skills_ten_minute_quiz.py"
)

_spec = importlib.util.spec_from_file_location("cv_skills_ten_minute_quiz", _MIGRATION_PATH)
assert _spec and _spec.loader
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)

_METADATA = sa.MetaData()
_SKILLS = sa.Table(
    "skills",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String(100), nullable=False),
    sa.Column("category", sa.String(50)),
    sa.Column("proficiency_level", sa.Integer),
    sa.Column("years_of_experience", sa.Float),
    sa.Column("order_index", sa.Integer),
)

# The live table exactly as /api/v1/skills/ served it on 2026-09-03, ids
# shortened. Order matters: the renumber must not reshuffle categories.
_PROD_SKILLS = [
    ("s-py", "Python", "Programming", 1),
    ("s-jsts", "JavaScript/TypeScript", "Programming", 2),
    ("s-sql", "SQL", "Programming", 3),
    ("s-sh", "Bash/PowerShell", "Programming", 4),
    ("s-fastapi", "FastAPI", "Programming", 5),
    ("s-vue", "Vue.js", "Programming", 6),
    ("s-docker", "Docker", "DevOps", 7),
    ("s-k8s", "Kubernetes", "DevOps", 8),
    ("s-gha", "GitHub Actions", "DevOps", 9),
    ("s-appsec", "Application Security", "Security Engineering", 10),
    ("s-tm", "Threat Modeling", "Security Engineering", 11),
    ("s-sdlc", "Secure SDLC", "Security Engineering", 12),
    ("s-sbom", "Software Supply-Chain Security (SBOM)", "Security Engineering", 13),
    ("s-vm", "Vulnerability Management", "Security Engineering", 14),
    ("s-524b", "FDA Premarket Cybersecurity (524B)", "Regulatory & Standards Compliance", 15),
    ("s-81001", "IEC 81001-5-1", "Regulatory & Standards Compliance", 16),
    ("s-62304", "IEC 62304", "Regulatory & Standards Compliance", 17),
    ("s-gamp", "GAMP 5", "Regulatory & Standards Compliance", 18),
    ("s-nis2", "NIS 2", "Regulatory & Standards Compliance", 19),
    ("s-dicom", "DICOM", "Healthcare IT", 20),
    ("s-hl7", "HL7", "Healthcare IT", 21),
]

_DROPPED = {"JavaScript/TypeScript", "SQL", "FastAPI", "Vue.js"}

# Category order as the CV prints it, derived from the first index per category.
_CATEGORY_ORDER = [
    "Programming",
    "DevOps",
    "Security Engineering",
    "Regulatory & Standards Compliance",
    "Healthcare IT",
]


def _rows(skills: list[tuple[str, str, str, int]]) -> list[dict]:
    return [
        {"id": i, "name": n, "category": c, "order_index": o, "proficiency_level": 80}
        for i, n, c, o in skills
    ]


def _run_upgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.upgrade()


def _make_db(skills: list[tuple[str, str, str, int]]) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    if skills:
        with engine.begin() as conn:
            conn.execute(_SKILLS.insert(), _rows(skills))
    return engine


def _names(conn: sa.Connection) -> set[str]:
    return set(conn.execute(sa.select(_SKILLS.c.name)).scalars())


def _by_name(conn: sa.Connection) -> dict[str, int]:
    return dict(conn.execute(sa.select(_SKILLS.c.name, _SKILLS.c.order_index)).all())


class TestSkillsTenMinuteQuizMigration:
    def test_drops_exactly_the_four_declined_claims(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            names = _names(conn)
            assert _DROPPED.isdisjoint(names)
            assert len(names) == 17
            # Programming survives as the honest pair rather than disappearing.
            programming = set(
                conn.execute(
                    sa.select(_SKILLS.c.name).where(_SKILLS.c.category == "Programming")
                ).scalars()
            )
            assert programming == {"Python", "Bash/PowerShell"}

    def test_renumber_is_contiguous_and_unique(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            indexes = sorted(_by_name(conn).values())
            assert indexes == list(range(1, 18)), "survivors must renumber 1..17 with no holes"

    def test_category_order_is_preserved(self):
        # The CV derives section order from the first row per category after
        # ORDER BY order_index. A renumber that reshuffled categories would
        # silently reorder the printed CV, which is the failure this guards.
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            rows = conn.execute(
                sa.select(_SKILLS.c.category, _SKILLS.c.order_index).order_by(_SKILLS.c.order_index)
            ).all()
        seen: list[str] = []
        for category, _ in rows:
            if category not in seen:
                seen.append(category)
        assert seen == _CATEGORY_ORDER

    def test_owner_added_rows_are_left_alone(self):
        # Anything not named in the migration is neither deleted nor renumbered,
        # so a skill the owner adds through /admin between deploys survives.
        extra = [*_PROD_SKILLS, ("s-own", "Kubernetes Hardening", "DevOps", 99)]
        engine = _make_db(extra)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            assert _by_name(conn)["Kubernetes Hardening"] == 99

    def test_empty_skills_table_is_untouched(self):
        engine = _make_db([])
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            assert _names(conn) == set(), "fresh DBs belong to seed_data, not this migration"

    def test_idempotent_rerun(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            first = _by_name(conn)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            assert _by_name(conn) == first

    def test_downgrade_does_not_restore_the_claims(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.begin() as conn:
            ctx = MigrationContext.configure(conn)
            with Operations.context(ctx):
                _migration.downgrade()
        with engine.connect() as conn:
            assert _DROPPED.isdisjoint(_names(conn))
