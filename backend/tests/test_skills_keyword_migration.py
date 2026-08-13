"""
Tests for the b5d21e04c7a9 skills keyword-sync data migration.

test_migration_drift only proves the EMPTY-table path (fresh DB upgrades to
head); this migration exists for the opposite case — converging an already
POPULATED prod table that seed_skills() can never reach. These tests run the
real upgrade() against a sync in-memory SQLite DB carrying a prod-like old
set and assert the convergence semantics: OUT terms deleted, the rename
preserves curated values, IN terms inserted, unrelated curated rows
untouched, and the whole thing idempotent.
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
    / "b5d21e04c7a9_skills_keyword_sync.py"
)

_spec = importlib.util.spec_from_file_location("skills_keyword_sync", _MIGRATION_PATH)
assert _spec and _spec.loader
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)

_METADATA = sa.MetaData()
_SKILLS = sa.Table(
    "skills",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String(100), nullable=False, unique=True),
    sa.Column("category", sa.String(50)),
    sa.Column("proficiency_level", sa.Integer),
    sa.Column("years_of_experience", sa.Float),
    sa.Column("order_index", sa.Integer),
)

# The shape prod actually had (2026-08-13 live check): old names, old ratings.
_OLD_PROD_ROWS = [
    {
        "id": "row-python",
        "name": "Python",
        "category": "Programming",
        "proficiency_level": 95,
        "years_of_experience": 5.0,
        "order_index": 1,
    },
    {
        "id": "row-k8s",
        "name": "Kubernetes",
        "category": "DevOps",
        "proficiency_level": 70,
        "years_of_experience": 2.0,
        "order_index": 10,
    },
    {
        "id": "row-vuln",
        "name": "Vulnerability Assessment",
        "category": "Security",
        "proficiency_level": 90,
        "years_of_experience": 4.0,
        "order_index": 14,
    },
    {
        "id": "row-iso",
        "name": "ISO 27001",
        "category": "Security",
        "proficiency_level": 85,
        "years_of_experience": 3.0,
        "order_index": 15,
    },
    {
        "id": "row-owasp",
        "name": "OWASP",
        "category": "Security",
        "proficiency_level": 85,
        "years_of_experience": 3.0,
        "order_index": 16,
    },
    {
        "id": "row-62304",
        "name": "IEC 62304",
        "category": "Medical",
        "proficiency_level": 85,
        "years_of_experience": 4.0,
        "order_index": 17,
    },
]

_IN_KEYWORDS = {
    "NIS 2",
    "GAMP 5",
    "IEC 62304",
    "IEC 81001-5-1",
    "Threat Modeling",
    "Application Security",
    "Software Supply-Chain Security (SBOM)",
    "Secure SDLC",
    "Vulnerability Management",
    "Kubernetes",
}


def _run_upgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.upgrade()


def _make_db(rows: list[dict]) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    if rows:
        with engine.begin() as conn:
            conn.execute(_SKILLS.insert(), rows)
    return engine


class TestSkillsKeywordMigration:
    def test_empty_table_is_left_to_the_seed(self):
        """Fresh DB: inserting here would trip _already_seeded and suppress
        the rest of the seed, so the migration must not touch an empty table."""
        engine = _make_db([])
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            count = conn.execute(sa.select(sa.func.count()).select_from(_SKILLS)).scalar_one()
        assert count == 0

    def test_populated_table_converges_to_the_decided_set(self):
        engine = _make_db(_OLD_PROD_ROWS)
        with engine.begin() as conn:
            _run_upgrade(conn)

        with engine.connect() as conn:
            rows = {r.name: r for r in conn.execute(sa.select(_SKILLS)).all()}

        # OUT terms gone; every IN keyword present.
        assert "ISO 27001" not in rows
        assert "OWASP" not in rows
        assert "Vulnerability Assessment" not in rows
        assert set(rows) >= _IN_KEYWORDS

        # The rename PRESERVED the curated row (same id, same rating) rather
        # than recreating it — owner-entered values must survive.
        assert rows["Vulnerability Management"].id == "row-vuln"
        assert rows["Vulnerability Management"].proficiency_level == 90

        # Unrelated curated rows untouched.
        assert rows["Python"].proficiency_level == 95
        assert rows["Kubernetes"].id == "row-k8s"

    def test_idempotent_on_rerun(self):
        engine = _make_db(_OLD_PROD_ROWS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            first = sorted((r.name, r.id) for r in conn.execute(sa.select(_SKILLS)).all())
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            second = sorted((r.name, r.id) for r in conn.execute(sa.select(_SKILLS)).all())
        assert first == second

    def test_rename_collision_deletes_the_old_row(self):
        """If the owner already created 'Vulnerability Management' by hand,
        renaming would violate the unique name constraint — the old row is
        deleted instead and the owner's row wins."""
        rows = _OLD_PROD_ROWS + [
            {
                "id": "row-vm-manual",
                "name": "Vulnerability Management",
                "category": "Security",
                "proficiency_level": 80,
                "years_of_experience": 3.0,
                "order_index": 20,
            },
        ]
        engine = _make_db(rows)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            got = {r.name: r for r in conn.execute(sa.select(_SKILLS)).all()}
        assert "Vulnerability Assessment" not in got
        assert got["Vulnerability Management"].id == "row-vm-manual"
        assert got["Vulnerability Management"].proficiency_level == 80
