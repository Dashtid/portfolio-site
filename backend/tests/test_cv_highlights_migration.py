"""Tests for the c9e2f7a4b681 cv_highlights / photo migration.

test_migration_drift only proves the EMPTY-table path (a fresh DB upgrades to
head). This migration exists for the opposite case: backfilling curated CV
bullets into an already POPULATED prod `companies` table that seed_data can
never reach. These run the real upgrade() against sync in-memory SQLite and
assert the backfill semantics — matched by start month, unknown roles left
NULL so the export falls back, owner edits never overwritten, idempotent.
"""

import datetime
import importlib.util
import json
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "alembic"
    / "versions"
    / "c9e2f7a4b681_cv_highlights_and_photo.py"
)

_spec = importlib.util.spec_from_file_location("cv_highlights_and_photo", _MIGRATION_PATH)
assert _spec and _spec.loader
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)

_METADATA = sa.MetaData()
_COMPANIES = sa.Table(
    "companies",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String(200), nullable=False),
    sa.Column("start_date", sa.DateTime),
)
_CV_PROFILE = sa.Table(
    "cv_profile",
    _METADATA,
    sa.Column("id", sa.Integer, primary_key=True),
)

# Names as PROD has them — deliberately different from cv/resume.json
# ("Philips Healthcare" vs "Philips") to prove the match is on start month.
_PROD_ROWS = [
    {
        "id": "c-hermes",
        "name": "Hermes Medical Solutions",
        "start_date": datetime.datetime(2024, 5, 1),
    },
    {"id": "c-philips", "name": "Philips Healthcare", "start_date": datetime.datetime(2022, 3, 1)},
    {"id": "c-fdf", "name": "Finnish Defence Forces", "start_date": datetime.datetime(2014, 1, 1)},
    {"id": "c-scania12", "name": "Scania Group", "start_date": datetime.datetime(2012, 6, 1)},
]


def _run_upgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.upgrade()


def _run_downgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.downgrade()


def _make_db(rows: list[dict]) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    with engine.begin() as conn:
        if rows:
            conn.execute(_COMPANIES.insert(), rows)
        conn.execute(_CV_PROFILE.insert(), [{"id": 1}])
    return engine


def _highlights(engine: sa.engine.Engine) -> dict[str, list[str] | None]:
    with engine.connect() as conn:
        rows = conn.execute(sa.text("SELECT name, cv_highlights FROM companies")).fetchall()
    out: dict[str, list[str] | None] = {}
    for name, raw in rows:
        # SQLite hands JSON back as text; Postgres would give the list directly.
        out[name] = json.loads(raw) if isinstance(raw, str) else raw
    return out


def _columns(engine: sa.engine.Engine, table: str) -> set[str]:
    with engine.connect() as conn:
        return {row[1] for row in conn.execute(sa.text(f"PRAGMA table_info({table})")).fetchall()}


class TestCvHighlightsBackfill:
    def test_backfills_curated_bullets_by_start_month(self):
        engine = _make_db(_PROD_ROWS)
        with engine.connect() as conn:
            _run_upgrade(conn)
            conn.commit()

        got = _highlights(engine)
        # Counts match the owner's real CV exactly (cv/resume.json). Hermes went
        # 3 -> 8 on 2026-09-06 with the approved September copy.
        hermes = got["Hermes Medical Solutions"]
        assert len(hermes) == 8
        assert len(got["Philips Healthcare"]) == 2
        assert len(got["Finnish Defence Forces"]) == 3
        assert len(got["Scania Group"]) == 1
        # The authorship claim leads - it was the August audit's defect #1 and it
        # must never slip back down the list.
        assert hermes[0].startswith("Author product cybersecurity documentation")
        assert any("STRIDE" in bullet for bullet in hermes)

    def test_unknown_role_left_null_so_export_falls_back(self):
        """A role added after this migration must not be blanked."""
        engine = _make_db(
            [
                *_PROD_ROWS,
                {
                    "id": "c-new",
                    "name": "Future Employer",
                    "start_date": datetime.datetime(2027, 1, 1),
                },
            ]
        )
        with engine.connect() as conn:
            _run_upgrade(conn)
            conn.commit()

        assert _highlights(engine)["Future Employer"] is None

    def test_never_overwrites_an_existing_curated_list(self):
        engine = _make_db(_PROD_ROWS)
        with engine.connect() as conn:
            _run_upgrade(conn)
            conn.commit()
        with engine.begin() as conn:
            conn.execute(
                sa.text("UPDATE companies SET cv_highlights = :v WHERE name = :n"),
                {"v": json.dumps(["Owner's own edit"]), "n": "Hermes Medical Solutions"},
            )
        with engine.connect() as conn:
            _run_upgrade(conn)  # idempotent re-run
            conn.commit()

        assert _highlights(engine)["Hermes Medical Solutions"] == ["Owner's own edit"]

    def test_empty_table_is_a_noop(self):
        """A fresh DB belongs to seed_data, not to this migration."""
        engine = _make_db([])
        with engine.connect() as conn:
            _run_upgrade(conn)
            conn.commit()

        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT COUNT(*) FROM companies")).scalar() == 0
        assert "cv_highlights" in _columns(engine, "companies")

    def test_adds_photo_column_and_downgrade_reverses_both(self):
        engine = _make_db(_PROD_ROWS)
        with engine.connect() as conn:
            _run_upgrade(conn)
            conn.commit()
        assert "photo" in _columns(engine, "cv_profile")
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT photo FROM cv_profile")).scalar() == ""

        with engine.connect() as conn:
            _run_downgrade(conn)
            conn.commit()
        assert "photo" not in _columns(engine, "cv_profile")
        assert "cv_highlights" not in _columns(engine, "companies")
