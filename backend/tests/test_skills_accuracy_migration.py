"""Tests for the d4b7a91c3e58 cv-skills-accuracy migration.

test_migration_drift only proves the EMPTY-table path (a fresh DB upgrades to
head). This migration exists for the opposite case: converging an already
POPULATED prod ``skills`` table (plus the CompTIA education row and the
cv_profile focus line) onto the 2026-08-22 accuracy set that seed_data can
never reach. These run the real upgrade() against sync in-memory SQLite and
assert the pruning semantics — unbacked rows deleted, HL7/FHIR renamed, the
FDA row added exactly once, order_index deduplicated deterministically, an
owner-edited focus never trampled, idempotent.
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
    / "d4b7a91c3e58_cv_skills_accuracy.py"
)

_spec = importlib.util.spec_from_file_location("cv_skills_accuracy", _MIGRATION_PATH)
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
_EDUCATION = sa.Table(
    "education",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("institution", sa.String(200)),
    sa.Column("degree", sa.String(200)),
)
_CV_PROFILE = sa.Table(
    "cv_profile",
    _METADATA,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("focus", sa.Text),
)

_FOCUS_OLD = _migration._FOCUS_OLD
_FOCUS_NEW = _migration._FOCUS_NEW

# The live table as the 2026-08-22 prod dump showed it: the four unbacked
# rows present, HL7/FHIR not yet renamed, and order_index 17/18/19 each
# duplicated across the Security/Medical boundary.
_PROD_SKILLS = [
    {"id": "s-py", "name": "Python", "category": "Programming", "order_index": 1},
    {"id": "s-django", "name": "Django", "category": "Frameworks", "order_index": 7},
    {"id": "s-react", "name": "React", "category": "Frameworks", "order_index": 8},
    {"id": "s-azure", "name": "Azure", "category": "Cloud", "order_index": 11},
    {"id": "s-audit", "name": "Security Auditing", "category": "Security", "order_index": 13},
    {"id": "s-iec", "name": "IEC 62304", "category": "Medical", "order_index": 17},
    {"id": "s-sdlc", "name": "Secure SDLC", "category": "Security", "order_index": 17},
    {"id": "s-dicom", "name": "DICOM", "category": "Medical", "order_index": 18},
    {
        "id": "s-sbom",
        "name": "Software Supply-Chain Security (SBOM)",
        "category": "Security",
        "order_index": 18,
    },
    {"id": "s-hl7", "name": "HL7/FHIR", "category": "Medical", "order_index": 19},
    {"id": "s-nis2", "name": "NIS 2", "category": "Security", "order_index": 19},
]


def _run_upgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.upgrade()


def _make_db(skills: list[dict]) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    with engine.begin() as conn:
        if skills:
            conn.execute(_SKILLS.insert(), skills)
        conn.execute(
            _EDUCATION.insert(),
            [
                {
                    "id": "e-kth",
                    "institution": "KTH Royal Institute of Technology",
                    "degree": "Master of Science - MS",
                },
                {"id": "e-comptia", "institution": "CompTIA", "degree": "Security+ Certification"},
            ],
        )
        conn.execute(_CV_PROFILE.insert(), [{"id": 1, "focus": _FOCUS_OLD}])
    return engine


def _names(conn: sa.Connection) -> set[str]:
    return set(conn.execute(sa.select(_SKILLS.c.name)).scalars())


class TestSkillsAccuracyMigration:
    def test_prunes_renames_and_adds_on_populated_table(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            names = _names(conn)
            assert {"Django", "React", "Azure", "Security Auditing", "HL7/FHIR"}.isdisjoint(names)
            assert "HL7" in names
            assert "FDA Premarket Cybersecurity (524B)" in names
            # The rename kept the curated row (same id) rather than recreating it.
            hl7_id = conn.execute(
                sa.select(_SKILLS.c.id).where(_SKILLS.c.name == "HL7")
            ).scalar_one()
            assert hl7_id == "s-hl7"

    def test_renumber_is_deterministic_and_duplicate_free(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            rows = conn.execute(sa.select(_SKILLS.c.name, _SKILLS.c.order_index)).all()
            indexes = [r.order_index for r in rows]
            assert len(indexes) == len(set(indexes)), "order_index must be unique after renumber"
            by_name = dict(rows)
            # Category order on the CV follows the first index per category:
            # every surviving Security row must sort before every Medical row.
            security_max = max(
                by_name[n]
                for n in ("Secure SDLC", "Software Supply-Chain Security (SBOM)", "NIS 2")
            )
            medical_min = min(by_name[n] for n in ("IEC 62304", "DICOM", "HL7"))
            assert security_max < medical_min

    def test_empty_skills_table_gets_no_inserts(self):
        engine = _make_db([])
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            assert _names(conn) == set(), "fresh DBs belong to seed_data, not this migration"

    def test_education_and_focus_updates(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            degrees = dict(conn.execute(sa.select(_EDUCATION.c.id, _EDUCATION.c.degree)).all())
            assert degrees["e-comptia"] == "Security+"
            assert degrees["e-kth"] == "Master of Science - MS"
            focus = conn.execute(sa.select(_CV_PROFILE.c.focus)).scalar_one()
            assert focus == _FOCUS_NEW

    def test_owner_edited_focus_is_never_trampled(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            conn.execute(_CV_PROFILE.update().values(focus="Owner wrote this himself"))
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            focus = conn.execute(sa.select(_CV_PROFILE.c.focus)).scalar_one()
            assert focus == "Owner wrote this himself"

    def test_idempotent_rerun(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            names = list(conn.execute(sa.select(_SKILLS.c.name)).scalars())
            assert names.count("FDA Premarket Cybersecurity (524B)") == 1
            assert len(names) == len(set(names))

    def test_rename_collision_deletes_stale_row(self):
        rows = [
            *_PROD_SKILLS,
            {"id": "s-hl7-new", "name": "HL7", "category": "Medical", "order_index": 30},
        ]
        engine = _make_db(rows)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            names = list(conn.execute(sa.select(_SKILLS.c.name)).scalars())
            assert names.count("HL7") == 1
            assert "HL7/FHIR" not in names

    def test_downgrade_is_noop(self):
        engine = _make_db(_PROD_SKILLS)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.begin() as conn:
            ctx = MigrationContext.configure(conn)
            with Operations.context(ctx):
                _migration.downgrade()
        with engine.connect() as conn:
            assert "FDA Premarket Cybersecurity (524B)" in _names(conn)
