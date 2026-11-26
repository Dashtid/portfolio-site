"""Tests for the 0c6c75e2c56f migration.

The migration gives every page_views.session_id that starts with "anon_" a
"legacy_" value, reduces every non-NULL page_views.referrer to a host or NULL,
then drops page_views.ip_address, user_agent and city and
oauth_states.client_ip. These run the real upgrade() and downgrade() against
sync in-memory SQLite tables shaped as the previous head leaves them, and the
Alembic chain on a SQLite file from the previous head to this revision, down
one step and up again. The migration's copy of _referrer_host is compared with
the app's on the same URLs.
"""

import importlib.util
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import event

from alembic import command  # type: ignore[attr-defined]
from app.api.v1.analytics import _referrer_host

_BACKEND = Path(__file__).resolve().parents[1]
_MIGRATION_PATH = (
    _BACKEND
    / "alembic"
    / "versions"
    / "0c6c75e2c56f_page_views_oauth_states_drop_client_columns.py"
)

_spec = importlib.util.spec_from_file_location("drop_client_columns_migration", _MIGRATION_PATH)
assert _spec and _spec.loader
_migration = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_migration)

_LEGACY_ID = re.compile(r"legacy_[0-9a-f]{16}")
_STAMP = datetime(2026, 6, 1, 12, 0, 0)

# The columns of page_views and oauth_states after the revision.
_PAGE_VIEW_COLUMNS_KEPT = {"id", "page_path", "referrer", "country", "session_id", "created_at"}
_OAUTH_STATE_COLUMNS_KEPT = {"state", "expires_at", "created_at"}

# page_views and oauth_states with the columns, defaults and indexes the
# previous head leaves.
_METADATA = sa.MetaData()
_PAGE_VIEWS = sa.Table(
    "page_views",
    _METADATA,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("page_path", sa.String(500), nullable=False),
    sa.Column("referrer", sa.String(500)),
    sa.Column("user_agent", sa.Text),
    sa.Column("ip_address", sa.String(64)),
    sa.Column("country", sa.String(2)),
    sa.Column("city", sa.String(100)),
    sa.Column("session_id", sa.String(255), nullable=False),
    sa.Column(
        "created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)")
    ),
    sa.Index("ix_page_views_created_at", "created_at"),
    sa.Index("ix_page_views_created_country", "created_at", "country"),
    sa.Index("ix_page_views_created_path", "created_at", "page_path"),
    sa.Index("ix_page_views_session_id", "session_id"),
)
_OAUTH_STATES = sa.Table(
    "oauth_states",
    _METADATA,
    sa.Column("state", sa.String(64), primary_key=True),
    sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        server_default=sa.text("(CURRENT_TIMESTAMP)"),
        nullable=False,
    ),
    sa.Column("client_ip", sa.String(45)),
    sa.Index("ix_oauth_states_expires_at", "expires_at"),
)

# A stored referrer and the value the migration leaves in its place.
_REFERRERS: list[tuple[str | None, str | None]] = [
    ("https://www.Google.com/search?q=private#results", "www.google.com"),
    ("https://user:password@mail.example.org/inbox/123", "mail.example.org"),
    ("android-app://com.google.android.gm/", "com.google.android.gm"),
    ("https://example.com./path", "example.com"),
    ("github.com", "github.com"),
    ("Example.ORG", "example.org"),
    ("news.example.net.", "news.example.net"),
    ("https://dashti.se/colophon?q=1", None),
    ("https://WWW.Dashti.SE./writing", None),
    ("dashti.se", None),
    ("WWW.DASHTI.SE", None),
    ("203.0.113.7", None),
    ("https://192.168.1.10:8080/intranet", None),
    ("https://[2001:db8::1]:8443/x", None),
    ("2001:db8::1", None),
    ("http://[::1/unclosed", None),
    ("not a url", None),
    ("/relative/path", None),
    ("localhost:3000", None),
    ("", None),
    (None, None),
]

# Values with a scheme, a path, a port, whitespace or a control character:
# the migration hands each of them to its copy of _referrer_host.
_URLS = [
    "https://www.Google.com/search?q=private#results",
    "https://www.linkedin.com:443/in/someone?trk=feed",
    "https://user:password@mail.example.org/inbox/123",
    "https://example.com./path",
    "android-app://com.google.android.gm/",
    "https://ex" + chr(0) + "ample.com/" + chr(10),
    "https://api.dashti.se/x",
    "https://1.example.com/x",
    "not a url",
    "/relative/path",
    "https:///no-host",
    "http://./",
    "http://[::1/unclosed",
    "https://[not-an-address]/",
    "https://dashti.se",
    "https://dashti.se/colophon?q=1",
    "https://WWW.Dashti.SE./writing",
    "https://192.168.1.10:8080/intranet",
    "http://203.0.113.7./",
    "https://[2001:db8::1]:8443/x",
    "http://[::ffff:192.0.2.1]/",
    "http://[fe80::1%25eth0]/",
    "javascript:alert(1)",
    "localhost:3000",
    "2001:db8::1",
]


def _page_view(
    row_id: str, session_id: str = "v_0000000000000000", referrer: str | None = None
) -> dict[str, Any]:
    """A page_views row with every column of the previous head filled in."""
    return {
        "id": row_id,
        "page_path": f"/{row_id}",
        "referrer": referrer,
        "user_agent": "Mozilla/5.0 probe",
        "ip_address": "0123456789abcdef",
        "country": "SE",
        "city": "Stockholm",
        "session_id": session_id,
        "created_at": _STAMP,
    }


def _oauth_state(state: str) -> dict[str, Any]:
    return {"state": state, "expires_at": _STAMP, "client_ip": "203.0.113.1"}


def _make_db(
    page_views: list[dict[str, Any]] | None = None,
    oauth_states: list[dict[str, Any]] | None = None,
) -> sa.engine.Engine:
    engine = sa.create_engine("sqlite://")
    _METADATA.create_all(engine)
    with engine.begin() as conn:
        if page_views:
            conn.execute(_PAGE_VIEWS.insert(), page_views)
        if oauth_states:
            conn.execute(_OAUTH_STATES.insert(), oauth_states)
    return engine


def _run(engine: sa.engine.Engine, step: str = "upgrade") -> None:
    with engine.begin() as conn:
        ctx = MigrationContext.configure(conn)
        with Operations.context(ctx):
            getattr(_migration, step)()


def _column(engine: sa.engine.Engine, column: str) -> dict[str, Any]:
    """page_views id -> the value of one column."""
    with engine.connect() as conn:
        return dict(conn.execute(sa.select(_PAGE_VIEWS.c.id, _PAGE_VIEWS.c[column])).all())


def _columns(engine: sa.engine.Engine, table: str) -> set[str]:
    return {col["name"] for col in sa.inspect(engine).get_columns(table)}


def _indexes(engine: sa.engine.Engine, table: str) -> set[str | None]:
    return {index["name"] for index in sa.inspect(engine).get_indexes(table)}


def _snapshot(engine: sa.engine.Engine) -> list[tuple[Any, ...]]:
    with engine.connect() as conn:
        return [tuple(row) for row in conn.execute(sa.text("SELECT * FROM page_views ORDER BY id"))]


class TestSessionIds:
    def test_rows_that_shared_an_anon_id_share_one_legacy_id(self):
        engine = _make_db(
            [
                _page_view("a1", "anon_0123456789abcdef"),
                _page_view("a2", "anon_0123456789abcdef"),
                _page_view("a3", "anon_fedcba9876543210"),
            ]
        )
        _run(engine)

        ids = _column(engine, "session_id")
        assert ids["a1"] == ids["a2"]
        assert ids["a3"] != ids["a1"]
        assert all(_LEGACY_ID.fullmatch(value) for value in ids.values())

    def test_other_session_ids_are_left_alone(self):
        """Only a value that starts with "anon_", in that case, is rewritten."""
        others = [
            "session_1700000000000_0123456789ab",
            "v_0123456789abcdef",
            "anonymous",
            "ANON_0123456789abcdef",
            "xanon_0123",
            "anon",
        ]
        engine = _make_db([_page_view(f"o{i}", value) for i, value in enumerate(others)])
        _run(engine)

        assert _column(engine, "session_id") == {f"o{i}": value for i, value in enumerate(others)}


class TestReferrers:
    def test_each_referrer_becomes_its_host_or_null(self):
        rows = [_page_view(f"r{i:02d}", referrer=old) for i, (old, _new) in enumerate(_REFERRERS)]
        engine = _make_db(rows)
        _run(engine)

        assert _column(engine, "referrer") == {
            f"r{i:02d}": new for i, (_old, new) in enumerate(_REFERRERS)
        }

    @pytest.mark.parametrize("url", _URLS)
    def test_the_copy_of_referrer_host_gives_what_the_app_stores(self, url: str):
        assert _migration._referrer_host(url) == _referrer_host(url)
        assert _migration._rewritten_referrer(url) == _referrer_host(url)

    @pytest.mark.parametrize("host", ["github.com", "www.linkedin.com", "com.google.android.gm"])
    def test_a_host_the_app_stores_is_kept(self, host: str):
        assert _referrer_host(f"https://{host}/x") == host
        assert _migration._rewritten_referrer(host) == host


class TestUpdates:
    def test_updates_match_rows_by_id_and_carry_one_page_each(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        """With pages of two rows, an anon_ id seen on two pages still gets one new value."""
        monkeypatch.setattr(_migration, "_BATCH_SIZE", 2)
        engine = _make_db(
            [
                _page_view("p1", "anon_0123456789abcdef", "https://example.com/a"),
                _page_view("p2", "v_0000000000000001", "github.com"),
                _page_view("p3", "anon_fedcba9876543210", "https://example.com/b"),
                _page_view("p4", "v_0000000000000002", None),
                _page_view("p5", "anon_0123456789abcdef", "https://dashti.se/"),
            ]
        )
        updates: list[tuple[str, int]] = []

        def record(
            _conn: Any,
            _cursor: Any,
            statement: str,
            parameters: Any,
            _context: Any,
            executemany: bool,
        ) -> None:
            if statement.lstrip().upper().startswith("UPDATE"):
                updates.append((" ".join(statement.split()), len(parameters) if executemany else 1))

        event.listen(engine, "before_cursor_execute", record)
        try:
            _run(engine)
        finally:
            event.remove(engine, "before_cursor_execute", record)

        assert {statement for statement, _rows in updates} == {
            "UPDATE page_views SET session_id=? WHERE page_views.id = ?",
            "UPDATE page_views SET referrer=? WHERE page_views.id = ?",
        }
        assert max(rows for _statement, rows in updates) == 2
        # Three anon_ rows; three referrers that change (github.com stays, p4 has none).
        assert sum(rows for statement, rows in updates if "session_id" in statement) == 3
        assert sum(rows for statement, rows in updates if "referrer" in statement) == 3
        ids = _column(engine, "session_id")
        assert ids["p1"] == ids["p5"]
        assert ids["p3"] != ids["p1"]


class TestColumns:
    def test_the_columns_go_and_every_row_keeps_its_other_values(self):
        engine = _make_db(
            [_page_view("a1", "v_0000000000000001"), _page_view("a2", "v_0000000000000002")],
            [_oauth_state("s1")],
        )
        _run(engine)

        assert _columns(engine, "page_views") == _PAGE_VIEW_COLUMNS_KEPT
        assert _columns(engine, "oauth_states") == _OAUTH_STATE_COLUMNS_KEPT
        assert _indexes(engine, "page_views") == {index.name for index in _PAGE_VIEWS.indexes}
        assert _indexes(engine, "oauth_states") == {index.name for index in _OAUTH_STATES.indexes}
        with engine.connect() as conn:
            rows = conn.execute(
                sa.text("SELECT id, page_path, country, session_id FROM page_views ORDER BY id")
            ).all()
            states = conn.execute(sa.text("SELECT state FROM oauth_states")).all()
        assert [tuple(row) for row in rows] == [
            ("a1", "/a1", "SE", "v_0000000000000001"),
            ("a2", "/a2", "SE", "v_0000000000000002"),
        ]
        assert [tuple(row) for row in states] == [("s1",)]

    def test_empty_tables_lose_the_columns(self):
        engine = _make_db()
        _run(engine)

        assert _columns(engine, "page_views") == _PAGE_VIEW_COLUMNS_KEPT
        assert _columns(engine, "oauth_states") == _OAUTH_STATE_COLUMNS_KEPT

    def test_a_rerun_changes_nothing(self):
        rows = [_page_view(f"r{i:02d}", referrer=old) for i, (old, _new) in enumerate(_REFERRERS)]
        rows.append(_page_view("a1", "anon_0123456789abcdef"))
        engine = _make_db(rows, [_oauth_state("s1")])
        _run(engine)
        first = _snapshot(engine)
        _run(engine)

        assert _snapshot(engine) == first

    def test_downgrade_adds_the_columns_back_empty_and_upgrade_runs_again(self):
        engine = _make_db(
            [_page_view("a1", "anon_0123456789abcdef", "https://example.com/x")],
            [_oauth_state("s1")],
        )
        _run(engine)
        _run(engine, "downgrade")

        assert _columns(engine, "page_views") == _PAGE_VIEW_COLUMNS_KEPT | {
            "user_agent",
            "ip_address",
            "city",
        }
        assert _columns(engine, "oauth_states") == _OAUTH_STATE_COLUMNS_KEPT | {"client_ip"}
        with engine.connect() as conn:
            row = conn.execute(
                sa.text("SELECT user_agent, ip_address, city, session_id, referrer FROM page_views")
            ).one()
            client_ip = conn.execute(sa.text("SELECT client_ip FROM oauth_states")).scalar_one()
        assert row[:3] == (None, None, None)
        assert _LEGACY_ID.fullmatch(row[3])
        assert row[4] == "example.com"
        assert client_ip is None

        _run(engine)
        assert _columns(engine, "page_views") == _PAGE_VIEW_COLUMNS_KEPT
        assert _columns(engine, "oauth_states") == _OAUTH_STATE_COLUMNS_KEPT


class TestChain:
    @staticmethod
    def _config() -> Config:
        # No ini file: env.py then skips logging.config.fileConfig, which would
        # disable the app's loggers for every test that runs after this one.
        config = Config()
        config.set_main_option("script_location", str(_BACKEND / "alembic"))
        return config

    def test_revision_follows_the_single_previous_head(self):
        assert _migration.revision == "0c6c75e2c56f"
        assert _migration.down_revision == "0151154c7be1"

    def test_the_chain_upgrades_rows_from_the_previous_head_and_back(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        db_path = tmp_path / "chain.db"
        monkeypatch.setenv("ALEMBIC_DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
        config = self._config()
        command.upgrade(config, "0151154c7be1")

        engine = sa.create_engine(f"sqlite:///{db_path}")
        try:
            # The tables the other tests build have the previous head's columns and indexes.
            for table in (_PAGE_VIEWS, _OAUTH_STATES):
                assert _columns(engine, table.name) == set(table.columns.keys())
                assert _indexes(engine, table.name) == {index.name for index in table.indexes}
            with engine.begin() as conn:
                conn.execute(
                    _PAGE_VIEWS.insert(),
                    [
                        _page_view("a1", "anon_0123456789abcdef", "https://www.Google.com/?q=1"),
                        _page_view("a2", "anon_0123456789abcdef", "github.com"),
                        _page_view("a3", "v_0000000000000001", "https://dashti.se/"),
                    ],
                )
                conn.execute(_OAUTH_STATES.insert(), [_oauth_state("s1")])

            command.upgrade(config, "0c6c75e2c56f")
            assert _columns(engine, "page_views") == _PAGE_VIEW_COLUMNS_KEPT
            assert _columns(engine, "oauth_states") == _OAUTH_STATE_COLUMNS_KEPT
            assert _indexes(engine, "page_views") == {index.name for index in _PAGE_VIEWS.indexes}
            ids = _column(engine, "session_id")
            assert ids["a1"] == ids["a2"]
            assert _LEGACY_ID.fullmatch(ids["a1"])
            assert ids["a3"] == "v_0000000000000001"
            assert _column(engine, "referrer") == {
                "a1": "www.google.com",
                "a2": "github.com",
                "a3": None,
            }

            command.downgrade(config, "0151154c7be1")
            assert {"user_agent", "ip_address", "city"} <= _columns(engine, "page_views")
            assert "client_ip" in _columns(engine, "oauth_states")

            command.upgrade(config, "0c6c75e2c56f")
            assert _columns(engine, "page_views") == _PAGE_VIEW_COLUMNS_KEPT
            assert _column(engine, "session_id") == ids
        finally:
            engine.dispose()
