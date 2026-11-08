"""Tests for the 0151154c7be1 text migration.

The migration rewrites companies.description and projects.description on
named rows, fills education.location where it is NULL or empty, and rewrites
documents.title and documents.description. Every update is guarded on the
column's exact current value. These run the real upgrade() against sync
in-memory SQLite: each guarded column moves to its new value, updated_at moves
with the companies and projects rows that change, edited values and other rows
are left alone, a re-run and an empty database change nothing, and downgrade
is a no-op.
"""

import importlib.util
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

_BACKEND = Path(__file__).resolve().parents[1]
_MIGRATION_PATH = (
    _BACKEND
    / "alembic"
    / "versions"
    / "0151154c7be1_companies_projects_education_documents_text.py"
)

_spec = importlib.util.spec_from_file_location("text_rows_migration", _MIGRATION_PATH)
assert _spec and _spec.loader
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)

_METADATA = sa.MetaData()
_COMPANIES = sa.Table(
    "companies",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("description", sa.Text),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)
_PROJECTS = sa.Table(
    "projects",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String(255), nullable=False),
    sa.Column("description", sa.Text),
    sa.Column("updated_at", sa.DateTime(timezone=True)),
)
_EDUCATION = sa.Table(
    "education",
    _METADATA,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("institution", sa.String(200), nullable=False),
    sa.Column("location", sa.String(200)),
)
_DOCUMENTS = sa.Table(
    "documents",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("title", sa.String, nullable=False),
    sa.Column("description", sa.Text),
)

_STAMP = datetime(2026, 7, 20, 19, 55, 27)
_HERMES = "Hermes Medical Solutions"
_PHILIPS = "Philips Healthcare"
_KTH = "KTH Royal Institute of Technology"
_LUND = "Lund University"


def _old(mapping: dict[str, tuple[str, str]], key: str) -> str:
    return mapping[key][0]


def _new(mapping: dict[str, tuple[str, str]], key: str) -> str:
    return mapping[key][1]


def _deployed_rows() -> dict[sa.Table, list[dict]]:
    """Rows holding the values the guards expect, plus one row per table that no guard names."""
    companies = _migration._COMPANY_DESCRIPTIONS
    projects = _migration._PROJECT_DESCRIPTIONS
    titles = _migration._DOCUMENT_TITLES
    descriptions = _migration._DOCUMENT_DESCRIPTIONS
    return {
        _COMPANIES: [
            {
                "id": "c-hermes",
                "name": _HERMES,
                "description": _old(companies, _HERMES),
                "updated_at": _STAMP,
            },
            {
                "id": "c-philips",
                "name": _PHILIPS,
                "description": _old(companies, _PHILIPS),
                "updated_at": _STAMP,
            },
            {
                "id": "c-other",
                "name": "Karolinska University Hospital",
                "description": "Unrelated description.",
                "updated_at": _STAMP,
            },
        ],
        _PROJECTS: [
            {
                "id": "p-subvectors",
                "name": "subvectors",
                "description": _old(projects, "subvectors"),
                "updated_at": None,
            },
            {
                "id": "p-site",
                "name": "Portfolio Site",
                "description": _old(projects, "Portfolio Site"),
                "updated_at": None,
            },
            {
                "id": "p-other",
                "name": "subcheck",
                "description": "Unrelated description.",
                "updated_at": None,
            },
        ],
        _EDUCATION: [
            {"id": 1, "institution": _LUND, "location": ""},
            {"id": 2, "institution": _KTH, "location": None},
            {"id": 3, "institution": "CompTIA", "location": None},
        ],
        _DOCUMENTS: [
            {"id": "d-msc", "title": titles[0][0], "description": descriptions[0][0]},
            {"id": "d-bsc", "title": titles[1][0], "description": descriptions[1][0]},
        ],
    }


def _make_db(rows: dict[sa.Table, list[dict]] | None = None) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    if rows:
        with engine.begin() as conn:
            for table, values in rows.items():
                if values:
                    conn.execute(table.insert(), values)
    return engine


def _run(engine: sa.engine.Engine, step: str = "upgrade") -> None:
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            getattr(_migration, step)()


def _snapshot(engine: sa.engine.Engine) -> dict[str, list[tuple]]:
    with engine.connect() as conn:
        return {
            table.name: [tuple(row) for row in conn.execute(sa.select(table).order_by(table.c.id))]
            for table in (_COMPANIES, _PROJECTS, _EDUCATION, _DOCUMENTS)
        }


def _column(engine: sa.engine.Engine, table: sa.Table, column: str) -> dict:
    with engine.connect() as conn:
        return dict(conn.execute(sa.select(table.c.id, table.c[column])).all())


class TestTextRowsMigration:
    def test_each_guarded_column_moves_to_its_new_value(self):
        engine = _make_db(_deployed_rows())
        _run(engine)

        companies = _migration._COMPANY_DESCRIPTIONS
        projects = _migration._PROJECT_DESCRIPTIONS
        titles = _migration._DOCUMENT_TITLES
        descriptions = _migration._DOCUMENT_DESCRIPTIONS
        assert _column(engine, _COMPANIES, "description") == {
            "c-hermes": _new(companies, _HERMES),
            "c-philips": _new(companies, _PHILIPS),
            "c-other": "Unrelated description.",
        }
        assert _column(engine, _PROJECTS, "description") == {
            "p-subvectors": _new(projects, "subvectors"),
            "p-site": _new(projects, "Portfolio Site"),
            "p-other": "Unrelated description.",
        }
        assert _column(engine, _EDUCATION, "location") == {
            1: "Lund, Sweden",
            2: "Stockholm, Sweden",
            3: None,
        }
        assert _column(engine, _DOCUMENTS, "title") == {
            "d-msc": titles[0][1],
            "d-bsc": titles[1][1],
        }
        assert _column(engine, _DOCUMENTS, "description") == {
            "d-msc": descriptions[0][1],
            "d-bsc": descriptions[1][1],
        }

    def test_updated_at_moves_only_on_changed_companies_and_projects_rows(self):
        engine = _make_db(_deployed_rows())
        _run(engine)

        companies = _column(engine, _COMPANIES, "updated_at")
        assert companies["c-hermes"] > _STAMP
        assert companies["c-philips"] > _STAMP
        assert companies["c-other"] == _STAMP

        projects = _column(engine, _PROJECTS, "updated_at")
        assert projects["p-subvectors"] is not None
        assert projects["p-site"] is not None
        assert projects["p-other"] is None

    def test_a_value_edited_in_admin_is_left_alone(self):
        rows = _deployed_rows()
        rows[_COMPANIES][0]["description"] = "Edited in /admin."
        rows[_PROJECTS][1]["description"] = "Edited in /admin."
        rows[_EDUCATION][1]["location"] = "Solna, Sweden"
        rows[_DOCUMENTS][0]["title"] = "Edited title"
        rows[_DOCUMENTS][1]["description"] = "Edited description."
        engine = _make_db(rows)
        _run(engine)

        assert _column(engine, _COMPANIES, "description")["c-hermes"] == "Edited in /admin."
        assert _column(engine, _COMPANIES, "updated_at")["c-hermes"] == _STAMP
        assert _column(engine, _PROJECTS, "description")["p-site"] == "Edited in /admin."
        assert _column(engine, _PROJECTS, "updated_at")["p-site"] is None
        assert _column(engine, _EDUCATION, "location")[2] == "Solna, Sweden"
        assert _column(engine, _DOCUMENTS, "title")["d-msc"] == "Edited title"
        assert _column(engine, _DOCUMENTS, "description")["d-bsc"] == "Edited description."
        # The other column of each edited document row still moves on its own guard.
        msc_description = _migration._DOCUMENT_DESCRIPTIONS[0][1]
        bsc_title = _migration._DOCUMENT_TITLES[1][1]
        assert _column(engine, _DOCUMENTS, "description")["d-msc"] == msc_description
        assert _column(engine, _DOCUMENTS, "title")["d-bsc"] == bsc_title

    def test_a_guarded_value_on_another_name_is_left_alone(self):
        rows = _deployed_rows()
        rows[_COMPANIES][2]["description"] = _old(_migration._COMPANY_DESCRIPTIONS, _HERMES)
        rows[_PROJECTS][2]["description"] = _old(_migration._PROJECT_DESCRIPTIONS, "subvectors")
        engine = _make_db(rows)
        _run(engine)

        assert _column(engine, _COMPANIES, "description")["c-other"] == _old(
            _migration._COMPANY_DESCRIPTIONS, _HERMES
        )
        assert _column(engine, _PROJECTS, "description")["p-other"] == _old(
            _migration._PROJECT_DESCRIPTIONS, "subvectors"
        )

    def test_rerun_changes_nothing(self):
        engine = _make_db(_deployed_rows())
        _run(engine)
        first = _snapshot(engine)
        _run(engine)
        assert _snapshot(engine) == first

    def test_empty_tables_stay_empty(self):
        engine = _make_db()
        _run(engine)
        assert _snapshot(engine) == {
            "companies": [],
            "projects": [],
            "education": [],
            "documents": [],
        }

    def test_downgrade_is_a_no_op(self):
        engine = _make_db(_deployed_rows())
        _run(engine)
        upgraded = _snapshot(engine)
        _run(engine, "downgrade")
        assert _snapshot(engine) == upgraded

    def test_new_companies_projects_and_education_values_are_the_seed_values(self):
        """A seeded database and an upgraded one end up with the same text."""
        seed = (_BACKEND / "app" / "seed_data.py").read_text(encoding="utf-8")
        for mapping in (_migration._COMPANY_DESCRIPTIONS, _migration._PROJECT_DESCRIPTIONS):
            for _old_value, new_value in mapping.values():
                assert f'"description": "{new_value}"' in seed
        for location in _migration._EDUCATION_LOCATIONS.values():
            assert f'"location": "{location}"' in seed

    def test_revision_follows_the_single_previous_head(self):
        assert _migration.revision == "0151154c7be1"
        assert _migration.down_revision == "b41f7ac2e905"
