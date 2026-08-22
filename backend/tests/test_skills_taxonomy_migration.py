"""Tests for the e7c9d24a5b13 cv-skills-taxonomy migration.

Converges an already-populated prod ``skills`` table onto the 2026-08-22
regrouping (Frameworks merged into Programming, "Security" -> "Security
Engineering" minus NIS 2, "Medical" split into "Regulatory & Standards Compliance" and
"Healthcare IT"). Runs the real upgrade() against sync in-memory SQLite.
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
    / "e7c9d24a5b13_cv_skills_taxonomy.py"
)

_spec = importlib.util.spec_from_file_location("cv_skills_taxonomy", _MIGRATION_PATH)
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
    sa.Column("order_index", sa.Integer),
)

# The table as d4b7a91c3e58 left it in prod: old category names, NIS 2 under
# Security, the standards under Medical — plus one owner-added row the
# migration does not know.
_PROD_SKILLS = [
    {"id": "s-py", "name": "Python", "category": "Programming", "order_index": 1},
    {"id": "s-fastapi", "name": "FastAPI", "category": "Frameworks", "order_index": 5},
    {"id": "s-nis2", "name": "NIS 2", "category": "Security", "order_index": 15},
    {
        "id": "s-fda",
        "name": "FDA Premarket Cybersecurity (524B)",
        "category": "Medical",
        "order_index": 19,
    },
    {"id": "s-dicom", "name": "DICOM", "category": "Medical", "order_index": 20},
    {"id": "s-custom", "name": "Owner Added This", "category": "Custom", "order_index": 99},
]


def _run_upgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.upgrade()


def _make_db(skills: list[dict]) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    if skills:
        with engine.begin() as conn:
            conn.execute(_SKILLS.insert(), skills)
    return engine


class TestSkillsTaxonomyMigration:
    def test_regroups_known_rows(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            rows = {
                r.name: (r.category, r.order_index)
                for r in conn.execute(
                    sa.select(_SKILLS.c.name, _SKILLS.c.category, _SKILLS.c.order_index)
                )
            }
            assert rows["FastAPI"] == ("Programming", 5)
            assert rows["NIS 2"] == ("Regulatory & Standards Compliance", 19)
            assert rows["FDA Premarket Cybersecurity (524B)"] == (
                "Regulatory & Standards Compliance",
                15,
            )
            assert rows["DICOM"] == ("Healthcare IT", 20)

    def test_unknown_rows_untouched(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            row = conn.execute(
                sa.select(_SKILLS.c.category, _SKILLS.c.order_index).where(
                    _SKILLS.c.name == "Owner Added This"
                )
            ).one()
            assert tuple(row) == ("Custom", 99)

    def test_empty_table_noop(self):
        engine = _make_db([])
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            count = conn.execute(sa.select(sa.func.count()).select_from(_SKILLS)).scalar_one()
            assert count == 0

    def test_idempotent_and_matches_seed_taxonomy(self):
        engine = _make_db(_PROD_SKILLS)
        for _ in range(2):
            with engine.begin() as conn:
                _run_upgrade(conn)
        # The migration's map IS the seed's canonical set — categories used
        # here must be exactly the five the CV renders.
        categories = {cat for cat, _ in _migration._TAXONOMY.values()}
        assert categories == {
            "Programming",
            "DevOps",
            "Security Engineering",
            "Regulatory & Standards Compliance",
            "Healthcare IT",
        }
        indexes = [idx for _, idx in _migration._TAXONOMY.values()]
        assert sorted(indexes) == list(range(1, 22))
