"""page_views and oauth_states: drop four columns, rewrite session_id and referrer

Rows first, then columns. The rewrites read page_views in id order, 1000
rows at a time, and write each page of changes back as one executemany
UPDATE that matches rows by id:

- session_id: a value that starts with "anon_" becomes "legacy_" and 16
  random hex characters (secrets.token_hex(8)), one new value for each
  distinct old value, so rows that shared a session_id still share one.
- referrer: a bare host (a value with no ":", "/", "?", "#", "@",
  whitespace or control character) is lowercased and loses a trailing dot.
  Any other value becomes what _referrer_host gives for it: the lowercased
  host of the URL, without port, user information or trailing dot. Either
  way the result is NULL when it is empty, names dashti.se or www.dashti.se,
  or is an IPv4 or IPv6 address, and NULL when the value does not parse or
  has no host. Only rows whose value changes are updated.

Then page_views.ip_address, page_views.user_agent, page_views.city and
oauth_states.client_ip are dropped, each only while its table has it, inside
batch_alter_table: SQLite copies the table, Postgres runs ALTER TABLE ...
DROP COLUMN.

_CONTROL_CHARS, _OWN_HOSTS, _is_ip_address and _referrer_host are copies of
the names in app/api/v1/analytics.py; tests/test_drop_client_columns_migration.py
compares this _referrer_host with the app's. On a re-run no session_id starts
with "anon_", a bare host stays as it is, and no column is left to drop.

Downgrade adds the four columns back, nullable and empty, each only while
its table lacks it. The rewritten session_id and referrer values stay.

Revision ID: 0c6c75e2c56f
Revises: 0151154c7be1
Create Date: 2026-11-27

"""

import ipaddress
import re
import secrets
from collections.abc import Iterator, Sequence
from urllib.parse import urlsplit

import sqlalchemy as sa

from alembic import op  # type: ignore[attr-defined]

# revision identifiers, used by Alembic.
revision: str = "0c6c75e2c56f"
down_revision: str | Sequence[str] | None = "0151154c7be1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# table -> the columns this revision drops, with the types downgrade adds back.
_DROPPED_COLUMNS: dict[str, tuple[tuple[str, sa.types.TypeEngine], ...]] = {
    "page_views": (
        ("user_agent", sa.Text()),
        ("ip_address", sa.String(length=64)),
        ("city", sa.String(length=100)),
    ),
    "oauth_states": (("client_ip", sa.String(length=45)),),
}

# Rows read per SELECT, and so the most rows one executemany UPDATE carries.
_BATCH_SIZE = 1000

_OLD_SESSION_PREFIX = "anon_"
_NEW_SESSION_PREFIX = "legacy_"

_page_views = sa.table(
    "page_views",
    sa.column("id", sa.String()),
    sa.column("session_id", sa.String()),
    sa.column("referrer", sa.String()),
)

# C0 control characters (U+0000-U+001F) plus DEL.
_CONTROL_CHARS = dict.fromkeys(list(range(0x20)) + [0x7F])

# Referrers from these hosts are stored as NULL: a page of this site.
_OWN_HOSTS = frozenset({"dashti.se", "www.dashti.se"})

# A value without any of these characters is a bare host.
_NOT_IN_A_BARE_HOST = re.compile(r"[\s\x00-\x1f\x7f:/?#@]")


def _is_ip_address(host: str) -> bool:
    """True when host is an IPv4 or IPv6 address (brackets already removed)."""
    try:
        ipaddress.ip_address(host)
    except ValueError:
        return False
    return True


def _referrer_host(referrer: str | None) -> str | None:
    """The lowercased host of a referrer URL, or None.

    Path, query, fragment, port and user:password@ are dropped, and so is a
    trailing dot. None when the referrer is absent or empty, does not parse
    (urlsplit raises ValueError, as on an unclosed IPv6 bracket), has no
    host, names dashti.se or www.dashti.se, or has an IPv4 or IPv6 address
    as its host.
    """
    if not referrer:
        return None
    try:
        host = urlsplit(referrer.translate(_CONTROL_CHARS)).hostname
    except ValueError:
        return None
    host = (host or "").rstrip(".")
    if not host or host in _OWN_HOSTS or _is_ip_address(host):
        return None
    return host[:500]


def _rewritten_referrer(referrer: str) -> str | None:
    """The referrer value this revision stores in place of `referrer`."""
    if _NOT_IN_A_BARE_HOST.search(referrer):
        return _referrer_host(referrer)
    host = referrer.lower().rstrip(".")
    if not host or host in _OWN_HOSTS or _is_ip_address(host):
        return None
    return host[:500]


def _pages(
    bind: sa.engine.Connection, column: sa.ColumnClause, condition: sa.ColumnElement
) -> Iterator[list[tuple[str, str]]]:
    """(id, column) of the page_views rows that meet `condition`, in id order, a page at a time."""
    last_id: str | None = None
    while True:
        query = sa.select(_page_views.c.id, column).where(condition)
        if last_id is not None:
            query = query.where(_page_views.c.id > last_id)
        rows = bind.execute(query.order_by(_page_views.c.id).limit(_BATCH_SIZE)).all()
        if not rows:
            return
        yield [(row_id, value) for row_id, value in rows]
        last_id = rows[-1][0]


def _update_by_id(
    bind: sa.engine.Connection, column: str, changes: list[tuple[str, str | None]]
) -> None:
    """Set page_views.<column> on each (id, value) row of `changes` with one executemany."""
    if not changes:
        return
    bind.execute(
        _page_views.update()
        .where(_page_views.c.id == sa.bindparam("row_id"))
        .values({column: sa.bindparam("new_value")}),
        [{"row_id": row_id, "new_value": value} for row_id, value in changes],
    )


def _rewrite_session_ids(bind: sa.engine.Connection) -> None:
    """Give every row of one "anon_" session_id the same new "legacy_" value."""
    new_ids: dict[str, str] = {}
    anon = _page_views.c.session_id.like("anon\\_%", escape="\\")
    for page in _pages(bind, _page_views.c.session_id, anon):
        changes: list[tuple[str, str | None]] = []
        for row_id, old in page:
            # SQLite's LIKE ignores the case of ASCII letters; startswith does not.
            if not old.startswith(_OLD_SESSION_PREFIX):
                continue
            if old not in new_ids:
                new_ids[old] = _NEW_SESSION_PREFIX + secrets.token_hex(8)
            changes.append((row_id, new_ids[old]))
        _update_by_id(bind, "session_id", changes)


def _rewrite_referrers(bind: sa.engine.Connection) -> None:
    """Store _rewritten_referrer of each non-NULL referrer, on the rows where it differs."""
    has_referrer = _page_views.c.referrer.is_not(None)
    for page in _pages(bind, _page_views.c.referrer, has_referrer):
        changes = [
            (row_id, new) for row_id, old in page if (new := _rewritten_referrer(old)) != old
        ]
        _update_by_id(bind, "referrer", changes)


def _drop_present(bind: sa.engine.Connection, table: str, names: Sequence[str]) -> None:
    """Drop the columns of `names` that `table` has, in one batch_alter_table."""
    present = {col["name"] for col in sa.inspect(bind).get_columns(table)}
    drops = [name for name in names if name in present]
    if not drops:
        return
    with op.batch_alter_table(table) as batch:
        for name in drops:
            batch.drop_column(name)


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("page_views"):
        _rewrite_session_ids(bind)
        _rewrite_referrers(bind)
    for table, columns in _DROPPED_COLUMNS.items():
        if inspector.has_table(table):
            _drop_present(bind, table, [name for name, _type in columns])


def downgrade() -> None:
    """Downgrade schema.

    Adds each dropped column back, nullable and empty, while its table lacks
    it. The session_id and referrer values the upgrade rewrote are not
    restored.
    """
    inspector = sa.inspect(op.get_bind())
    for table, columns in _DROPPED_COLUMNS.items():
        if not inspector.has_table(table):
            continue
        present = {col["name"] for col in inspector.get_columns(table)}
        for name, type_ in columns:
            if name not in present:
                op.add_column(table, sa.Column(name, type_, nullable=True))
