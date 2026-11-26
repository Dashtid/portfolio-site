"""
No SQL statement names a column that the code no longer writes.

page_views.ip_address, user_agent and city stay in the schema, unwritten. A
migration that drops them can run while this code still serves (Fly runs the
release command before the new machines start), so no statement this code
emits may name them, neither a write nor a read. Each test records every
statement the test engine runs while the code paths that use the table
execute, checks that each kind of statement was seen, and looks for the
column names in all of them.
"""

import asyncio
import contextlib
import re
from collections.abc import Iterator
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from tests.conftest import TestSessionLocal, run_one_cleanup_pass, test_engine

BEACON = "/api/v1/analytics/track/pageview"
PAGE_VIEW_COLUMNS = re.compile(r"\b(?:ip_address|user_agent|city)\b", re.IGNORECASE)


@contextlib.contextmanager
def _statements() -> Iterator[list[str]]:
    """Every SQL statement the test engine runs inside the block."""
    seen: list[str] = []

    def record(_conn: Any, _cursor: Any, statement: str, *_rest: Any) -> None:
        seen.append(statement)

    event.listen(test_engine.sync_engine, "before_cursor_execute", record)
    try:
        yield seen
    finally:
        event.remove(test_engine.sync_engine, "before_cursor_execute", record)


def _starting(statements: list[str], prefix: str) -> list[str]:
    """The statements that start with `prefix`, compared with whitespace collapsed."""
    return [s for s in statements if " ".join(s.split()).upper().startswith(prefix)]


def test_page_view_statements_name_no_unwritten_column(
    client: TestClient, admin_user_in_db: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The beacon, its country update, both stats endpoints and a cleanup pass."""
    monkeypatch.setattr("app.api.v1.analytics.get_country_code", AsyncMock(return_value="SE"))
    monkeypatch.setattr("app.api.v1.analytics.AsyncSessionLocal", TestSessionLocal)

    with _statements() as statements:
        response = client.post(
            BEACON,
            json={"page_path": "/a", "referrer": "https://example.com/"},
            headers={"User-Agent": "probe-agent/1.0"},
        )
        assert response.status_code == 200
        for stats in ("summary", "visitors"):
            response = client.get(
                f"/api/v1/analytics/stats/{stats}", headers=admin_user_in_db["headers"]
            )
            assert response.status_code == 200
        asyncio.run(run_one_cleanup_pass())

    assert _starting(statements, "INSERT INTO PAGE_VIEWS")
    assert _starting(statements, "UPDATE PAGE_VIEWS SET COUNTRY")
    assert _starting(statements, "DELETE FROM PAGE_VIEWS")
    assert [s for s in _starting(statements, "SELECT") if "page_views" in s]
    assert [s for s in statements if PAGE_VIEW_COLUMNS.search(s)] == []
