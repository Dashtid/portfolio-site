"""Tests for the c9a4e7b21f83 summary-trim migration.

The owner's 2026-08-23 review rejected exactly one sentence of the
bullet-pack summary — the "Background: five years ..." tail — and
approved the rest. The migration removes that tail from a summary that
still matches the post-pack text verbatim, and touches nothing else.
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
    / "c9a4e7b21f83_trim_summary_background_line.py"
)

_spec = importlib.util.spec_from_file_location("cv_summary_trim", _MIGRATION_PATH)
assert _spec and _spec.loader
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)

_METADATA = sa.MetaData()
_CV_PROFILE = sa.Table(
    "cv_profile",
    _METADATA,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("summary", sa.Text),
)


def _run_upgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.upgrade()


def _make_db(summary: str | None) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    if summary is not None:
        with engine.begin() as conn:
            conn.execute(_CV_PROFILE.insert(), [{"id": 1, "summary": summary}])
    return engine


def _summary(engine: sa.engine.Engine) -> str:
    with engine.connect() as conn:
        return conn.execute(sa.select(_CV_PROFILE.c.summary)).scalar_one()


class TestCvSummaryTrimMigration:
    def test_trims_the_background_tail(self):
        engine = _make_db(_migration._SUMMARY_WITH_TAIL)
        with engine.begin() as conn:
            _run_upgrade(conn)
        assert _summary(engine) == _migration._SUMMARY_TRIMMED
        assert "Background: five years" not in _summary(engine)

    def test_trimmed_is_the_pack_summary_minus_only_the_tail(self):
        """Everything before the rejected sentence survives verbatim."""
        assert _migration._SUMMARY_WITH_TAIL.startswith(_migration._SUMMARY_TRIMMED)
        tail = _migration._SUMMARY_WITH_TAIL[len(_migration._SUMMARY_TRIMMED) :]
        assert tail == (
            " Background: five years across medical imaging and healthcare IT, "
            "in a formal security role since 2024."
        )

    def test_owner_edited_summary_wins(self):
        engine = _make_db("Owner wrote this himself.")
        with engine.begin() as conn:
            _run_upgrade(conn)
        assert _summary(engine) == "Owner wrote this himself."

    def test_idempotent_rerun(self):
        engine = _make_db(_migration._SUMMARY_WITH_TAIL)
        for _ in range(2):
            with engine.begin() as conn:
                _run_upgrade(conn)
        assert _summary(engine) == _migration._SUMMARY_TRIMMED

    def test_empty_table_noop(self):
        engine = _make_db(None)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            count = conn.execute(sa.select(sa.func.count()).select_from(_CV_PROFILE)).scalar_one()
        assert count == 0
