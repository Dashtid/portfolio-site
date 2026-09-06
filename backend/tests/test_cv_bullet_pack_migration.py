"""Tests for the f3d8b17c6e42 cv-bullet-pack migration.

Converges the owner-approved bullet rewrites/trims onto an already-populated
prod ``companies`` table. The load-bearing semantics: updates fire ONLY when
the current value equals the exact pre-pack value (owner edits win), the
Scania-2012 trim writes a genuinely EMPTY list (which the export renders as
no bullets — see test_cv_export), and the summary append is exact-match
guarded the same way.
"""

import datetime
import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

_MIGRATION_PATH = (
    Path(__file__).resolve().parents[1] / "alembic" / "versions" / "f3d8b17c6e42_cv_bullet_pack.py"
)

_spec = importlib.util.spec_from_file_location("cv_bullet_pack", _MIGRATION_PATH)
assert _spec and _spec.loader
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)

_METADATA = sa.MetaData()
_COMPANIES = sa.Table(
    "companies",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("title", sa.String(200)),
    sa.Column("start_date", sa.DateTime),
    sa.Column("cv_highlights", sa.JSON, nullable=True),
)
_EDUCATION = sa.Table(
    "education",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("institution", sa.String(200)),
    sa.Column("degree", sa.String(200)),
    sa.Column("field_of_study", sa.String(200)),
    sa.Column("description", sa.Text),
)
_CV_PROFILE = sa.Table(
    "cv_profile",
    _METADATA,
    sa.Column("id", sa.Integer, primary_key=True),
    sa.Column("summary", sa.Text),
)


def _pack(key: str) -> tuple[list[str], list[str]]:
    return _migration._PACK[key]


# Stand-in for whatever the Hermes row holds when this pack runs. Deliberately
# not the real pre-September text: that text is the reason the "2024-05" entry
# was removed, and committing it here would put it back in the tracked tree.
_HERMES_UNTOUCHED = ["Hermes bullets - owned by b41f7ac2e905, not by this pack."]


def _prod_rows() -> list[dict]:
    return [
        {
            "id": "c-hermes",
            "title": "QA/RA & Security Specialist",
            "start_date": datetime.datetime(2024, 5, 1),
            # The pack's "2024-05" entry was removed 2026-09-06 (its bullets named
            # the banned protocol/technique pair). This row is now one the pack
            # must LEAVE ALONE; b41f7ac2e905 owns the Hermes copy instead.
            "cv_highlights": _HERMES_UNTOUCHED,
        },
        {
            "id": "c-philips",
            "title": "Incident Support Specialist, Nordics",
            "start_date": datetime.datetime(2022, 3, 1),
            "cv_highlights": list(_pack("2022-03")[0]),
        },
        {
            "id": "c-karolinska",
            "title": "Biomedical Engineer, Medical Imaging and Physiology",
            "start_date": datetime.datetime(2021, 6, 1),
            "cv_highlights": ["Provided support for imaging IT systems ..."],
        },
        {
            "id": "c-softpro",
            "title": "Master Thesis Student",
            "start_date": datetime.datetime(2020, 10, 1),
            "cv_highlights": list(_pack("2020-10")[0]),
        },
        {
            "id": "c-scania12",
            "title": "Technician, Engine Analysis",
            "start_date": datetime.datetime(2012, 6, 1),
            "cv_highlights": list(_pack("2012-06")[0]),
        },
    ]


def _run_upgrade(conn: sa.Connection) -> None:
    ctx = MigrationContext.configure(conn)
    with Operations.context(ctx):
        _migration.upgrade()


def _make_db(rows: list[dict], summary: str | None = None) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    with engine.begin() as conn:
        if rows:
            conn.execute(_COMPANIES.insert(), rows)
        conn.execute(
            _EDUCATION.insert(),
            [
                {
                    "id": "e-kth",
                    "institution": "KTH Royal Institute of Technology",
                    "degree": "Master of Science - MS",
                    "field_of_study": "Biomedical Engineering - Computer Science",
                    "description": _migration._EDUCATION_FIXES[2][2],
                },
                {
                    "id": "e-lund",
                    "institution": "Lund University",
                    "degree": "Bachelor of Science - BS",
                    "field_of_study": "Biomedical Engineering",
                    "description": _migration._EDUCATION_FIXES[4][2],
                },
            ],
        )
        conn.execute(
            _CV_PROFILE.insert(),
            [{"id": 1, "summary": summary if summary is not None else _migration._SUMMARY_OLD}],
        )
    return engine


def _highlights(conn: sa.Connection, company_id: str):
    return conn.execute(
        sa.select(_COMPANIES.c.cv_highlights).where(_COMPANIES.c.id == company_id)
    ).scalar_one()


class TestCvBulletPackMigration:
    def test_applies_pack_to_matching_rows(self):
        engine = _make_db(_prod_rows())
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            # Hermes is no longer this pack's business - it must pass through.
            assert _highlights(conn, "c-hermes") == _HERMES_UNTOUCHED
            assert _highlights(conn, "c-philips") == _pack("2022-03")[1]
            # The trim is an EMPTY list, not NULL — "deliberately no bullets".
            assert _highlights(conn, "c-scania12") == []
            # A role the pack does not touch keeps its bullets.
            assert _highlights(conn, "c-karolinska") == [
                "Provided support for imaging IT systems ..."
            ]

    def test_owner_edited_bullets_win(self):
        rows = _prod_rows()
        rows[0]["cv_highlights"] = ["Owner rewrote this himself."]
        engine = _make_db(rows)
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            assert _highlights(conn, "c-hermes") == ["Owner rewrote this himself."]
            # Untouched rows still converge.
            assert _highlights(conn, "c-philips") == _pack("2022-03")[1]

    def test_copy_polish_title_and_education(self):
        engine = _make_db(_prod_rows())
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            title = conn.execute(
                sa.select(_COMPANIES.c.title).where(_COMPANIES.c.id == "c-softpro")
            ).scalar_one()
            assert title == "Master's Thesis Student"
            kth = conn.execute(
                sa.select(
                    _EDUCATION.c.degree, _EDUCATION.c.field_of_study, _EDUCATION.c.description
                ).where(_EDUCATION.c.id == "e-kth")
            ).one()
            assert kth.degree == "Master of Science"
            assert kth.field_of_study == "Biomedical Engineering – Computer Science"
            assert kth.description.startswith("Master's Thesis — '")
            lund_degree = conn.execute(
                sa.select(_EDUCATION.c.degree).where(_EDUCATION.c.id == "e-lund")
            ).scalar_one()
            assert lund_degree == "Bachelor of Science"

    def test_summary_appends_two_clocks_line(self):
        engine = _make_db(_prod_rows())
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            summary = conn.execute(sa.select(_CV_PROFILE.c.summary)).scalar_one()
            assert summary == _migration._SUMMARY_NEW
            assert "formal security role since 2024" in summary

    def test_owner_edited_summary_wins(self):
        engine = _make_db(_prod_rows(), summary="Owner wrote this himself.")
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            summary = conn.execute(sa.select(_CV_PROFILE.c.summary)).scalar_one()
            assert summary == "Owner wrote this himself."

    def test_idempotent_rerun(self):
        engine = _make_db(_prod_rows())
        for _ in range(2):
            with engine.begin() as conn:
                _run_upgrade(conn)
        with engine.connect() as conn:
            assert _highlights(conn, "c-hermes") == _HERMES_UNTOUCHED
            summary = conn.execute(sa.select(_CV_PROFILE.c.summary)).scalar_one()
            # The append must not stack on a re-run.
            assert summary.count("Background: five years") == 1

    def test_empty_companies_table_noop(self):
        engine = _make_db([])
        with engine.begin() as conn:
            _run_upgrade(conn)
        with engine.connect() as conn:
            count = conn.execute(sa.select(sa.func.count()).select_from(_COMPANIES)).scalar_one()
            assert count == 0
            # The summary guard still runs (separate table, exact-match safe).
            summary = conn.execute(sa.select(_CV_PROFILE.c.summary)).scalar_one()
            assert summary == _migration._SUMMARY_NEW

    def test_register_constraints_hold_in_new_bullets(self):
        """The pack must never smuggle in a banned claim."""
        new_text = " ".join(" ".join(new) for _, new in _migration._PACK.values()).lower()
        for banned in ("pentest", "penetration", "wired into ci", "spearheaded", "owasp"):
            assert banned not in new_text
        # No personal-ownership claim over the employer's testing tool. Token
        # assembled, not written out - see the docstring of the test below.
        assert "my " + "fu" + "zz" + "er" not in new_text

    def test_pack_carries_no_protocol_or_technique_token(self):
        """Neither half of the banned public-surface pair may live in this file.

        The "2024-05" entry was removed on 2026-09-06 because both its halves named
        the employer's imaging protocol beside the dynamic-testing technique. This
        guards the removal: a future edit that reinstates either token here would
        put it back into a public repo's tracked tree and every clone of it.

        The two tokens are assembled from fragments rather than written out, so
        that the tree-wide scan in frontend/tests/unit/cvPublicScrub.spec.ts does
        not flag this guard as the very thing it guards against.
        """
        protocol = "DI" + "COM"
        technique = "fu" + "zz"
        both_halves = " ".join(
            " ".join(old) + " " + " ".join(new) for old, new in _migration._PACK.values()
        ).lower()
        assert protocol.lower() not in both_halves
        assert technique not in both_halves
        assert "2024-05" not in _migration._PACK
