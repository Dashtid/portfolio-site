"""
Tests for analytics API module
"""

import asyncio
import logging
import re
from datetime import date
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api.v1.analytics import _referrer_host, logger, router
from app.config import settings
from app.models.analytics import PageView
from app.utils import visitor_key
from tests.conftest import TestSessionLocal

BEACON = "/api/v1/analytics/track/pageview"


def _stored(*columns: Any) -> list[tuple[Any, ...]]:
    """The given page_views columns of every stored row."""

    async def read() -> list[tuple[Any, ...]]:
        async with TestSessionLocal() as session:
            return [tuple(row) for row in await session.execute(select(*columns))]

    return asyncio.run(read())


class TestAnalyticsModule:
    """Tests for analytics module setup."""

    def test_router_exists(self):
        """Test that router is defined."""
        assert router is not None

    def test_logger_exists(self):
        """Test that logger is defined."""
        assert logger is not None
        assert isinstance(logger, logging.Logger)

    def test_router_has_active_routes(self):
        """Test that router has active analytics routes."""
        # Analytics router should have 3 routes:
        # - POST /analytics/track/pageview
        # - GET /analytics/stats/summary
        # - GET /analytics/stats/visitors
        assert len(router.routes) == 3

        route_paths = [route.path for route in router.routes]
        assert "/analytics/track/pageview" in route_paths
        assert "/analytics/stats/summary" in route_paths
        assert "/analytics/stats/visitors" in route_paths


class TestTrackPageviewEndpoint:
    """Tests for POST /analytics/track/pageview endpoint.

    The beacon answers 204 with no body, so the tests read the stored rows.
    """

    def test_track_pageview_success(self, client: TestClient):
        """A page view is stored and answered with 204 and no body."""
        response = client.post(
            BEACON, json={"page_path": "/projects", "referrer": "https://google.com"}
        )
        assert response.status_code == 204
        assert response.content == b""
        assert _stored(PageView.page_path, PageView.referrer) == [("/projects", "google.com")]

    def test_page_title_and_visitor_id_are_ignored(self, client: TestClient):
        """Older frontend bundles still send both fields; the beacon is stored all the same."""
        response = client.post(
            BEACON,
            json={
                "page_path": "/about",
                "page_title": "about",
                "visitor_id": "session_1700000000000_0123456789ab",
            },
        )
        assert response.status_code == 204
        [(session_id,)] = _stored(PageView.session_id)
        assert re.fullmatch(r"v_[0-9a-f]{16}", session_id)

    def test_track_pageview_strips_control_characters(self, client: TestClient):
        """A JSON-escaped NUL in any stored string field must not reach the DB.

        Postgres text columns cannot store U+0000: asyncpg raised DataError
        and this UNAUTHENTICATED endpoint returned 500 on live prod for
        page_path, referrer and visitor_id (verified 2026-08-04). Same class
        as the length-overflow guard below, missed by it. CR/LF are stripped
        with the rest of C0 so an attacker cannot forge log lines either.
        """
        nul = chr(0)
        response = client.post(
            BEACON,
            json={"page_path": f"/proj{nul}ects", "referrer": f"https://ex{nul}.com/{nul}a"},
            headers={"User-Agent": f"Mozilla{nul}/5.0"},
        )
        assert response.status_code == 204
        assert _stored(PageView.page_path, PageView.referrer) == [("/projects", "ex.com")]

    def test_track_pageview_strips_crlf_log_injection(self, client: TestClient):
        """CR/LF in a beacon value must not survive into stored data."""
        response = client.post(
            BEACON, json={"page_path": "/a" + chr(13) + chr(10) + "FAKE LOG LINE"}
        )
        assert response.status_code == 204
        assert _stored(PageView.page_path) == [("/aFAKE LOG LINE",)]

    def test_track_pageview_all_control_chars_yields_usable_row(self, client: TestClient):
        """A path of nothing but control chars scrubs to empty -> falls back
        to "/" rather than storing an empty string or 500-ing."""
        response = client.post(BEACON, json={"page_path": chr(0) + chr(1) + chr(31)})
        assert response.status_code == 204
        assert _stored(PageView.page_path) == [("/",)]

    def test_track_pageview_truncates_long_values_to_column_width(self, client: TestClient):
        """Long UTM-style paths/referrers (501-2048 chars) are accepted and
        the path is stored truncated to its String(500) column instead of
        500-ing at INSERT (Postgres 22001) or dropping the beacon with a 422.
        The referrer is stored as its host, and the long User-Agent header
        is not stored at all.
        """
        long_path = "/campaign?" + "utm_content=" + "x" * 900
        long_ref = "https://example.com/?ref=" + "y" * 900
        response = client.post(
            BEACON,
            json={"page_path": long_path, "referrer": long_ref},
            headers={"User-Agent": "A" * 2000},
        )
        assert response.status_code == 204
        assert _stored(PageView.page_path, PageView.referrer) == [(long_path[:500], "example.com")]

    def test_track_pageview_rejects_over_2048(self, client: TestClient):
        """Beyond the generous 2048 cap the beacon is rejected outright —
        nothing legitimate is that long."""
        response = client.post(BEACON, json={"page_path": "/x" + "z" * 2100})
        assert response.status_code == 422
        assert _stored(PageView.page_path) == []

    def test_track_pageview_without_referrer(self, client: TestClient):
        """Test tracking a page view without referrer."""
        response = client.post(BEACON, json={"page_path": "/about"})
        assert response.status_code == 204
        assert _stored(PageView.page_path, PageView.referrer) == [("/about", None)]

    def test_track_pageview_home_page(self, client: TestClient):
        """Test tracking home page view."""
        response = client.post(BEACON, json={"page_path": "/"})
        assert response.status_code == 204
        assert _stored(PageView.page_path) == [("/",)]

    def test_track_pageview_with_query_params(self, client: TestClient):
        """Test tracking page view with query parameters."""
        response = client.post(BEACON, json={"page_path": "/projects?filter=featured"})
        assert response.status_code == 204
        assert _stored(PageView.page_path) == [("/projects?filter=featured",)]

    def test_track_pageview_missing_page_path(self, client: TestClient):
        """Test tracking page view without page_path fails."""
        response = client.post(BEACON, json={})
        assert response.status_code == 422  # Validation error

    def test_track_pageview_empty_page_path(self, client: TestClient):
        """An empty page_path is stored as "/"."""
        response = client.post(BEACON, json={"page_path": ""})
        assert response.status_code == 204
        assert _stored(PageView.page_path) == [("/",)]

    def test_forwarded_for_from_an_untrusted_peer_leaves_the_key_alone(self, client: TestClient):
        """X-Forwarded-For counts only from a trusted proxy (app/core/ip_utils.py).

        TestClient's peer is not an address, so the header is ignored and
        both rows get the key of the same address and User-Agent.
        """
        assert client.post(BEACON, json={"page_path": "/a"}).status_code == 204
        response = client.post(
            BEACON, json={"page_path": "/b"}, headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
        )
        assert response.status_code == 204

        keys = dict(_stored(PageView.page_path, PageView.session_id))
        assert keys["/a"] == keys["/b"]

    def test_track_pageview_stores_no_address_digest_or_user_agent(self, client: TestClient):
        """ip_address, user_agent and city stay NULL on every new row."""
        response = client.post(
            BEACON,
            json={"page_path": "/a"},
            headers={"User-Agent": "Mozilla/5.0 probe", "X-Forwarded-For": "203.0.113.9"},
        )
        assert response.status_code == 204

        assert _stored(PageView.ip_address, PageView.user_agent, PageView.city) == [
            (None, None, None)
        ]

    def test_track_multiple_pageviews(self, client: TestClient):
        """Test tracking multiple page views creates separate records."""
        paths = ["/", "/about", "/projects", "/contact"]
        for path in paths:
            assert client.post(BEACON, json={"page_path": path}).status_code == 204

        rows = _stored(PageView.id, PageView.page_path)
        assert sorted(path for _, path in rows) == sorted(paths)
        # All IDs should be unique
        assert len({row_id for row_id, _ in rows}) == len(paths)


class TestDailyVisitorKey:
    """A row's session_id is the daily visitor key of its address and User-Agent.

    Every TestClient request has the address "unknown" (its peer is not an
    address), so the requests here differ by User-Agent only.
    """

    @staticmethod
    def _track(client: TestClient, path: str, user_agent: str, **body: Any) -> None:
        response = client.post(
            BEACON, json={"page_path": path, **body}, headers={"User-Agent": user_agent}
        )
        assert response.status_code == 204

    def test_one_user_agent_gets_one_key_for_the_day(self, client: TestClient):
        self._track(client, "/a", "agent-one")
        self._track(client, "/b", "agent-one")

        keys = dict(_stored(PageView.page_path, PageView.session_id))
        assert keys["/a"] == keys["/b"]
        assert re.fullmatch(r"v_[0-9a-f]{16}", keys["/a"])

    def test_another_user_agent_gets_another_key(self, client: TestClient):
        self._track(client, "/a", "agent-one")
        self._track(client, "/b", "agent-two")

        keys = dict(_stored(PageView.page_path, PageView.session_id))
        assert keys["/a"] != keys["/b"]

    def test_a_new_salt_gives_another_key(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        self._track(client, "/a", "agent-one")
        # A salt dated in the past is replaced by the next beacon.
        monkeypatch.setattr(visitor_key, "_salt_day", date(2000, 1, 1))
        self._track(client, "/b", "agent-one")

        keys = dict(_stored(PageView.page_path, PageView.session_id))
        assert keys["/a"] != keys["/b"]

    def test_visitor_id_in_the_body_is_ignored(self, client: TestClient):
        self._track(client, "/a", "agent-one", visitor_id="client-chosen-1")
        self._track(client, "/b", "agent-one", visitor_id="client-chosen-2")

        keys = dict(_stored(PageView.page_path, PageView.session_id))
        assert keys["/a"] == keys["/b"]
        assert re.fullmatch(r"v_[0-9a-f]{16}", keys["/a"])


class TestReferrerHost:
    """A page view's referrer is stored as the lowercased host of the URL."""

    @pytest.mark.parametrize(
        ("referrer", "host"),
        [
            ("https://www.Google.com/search?q=private#results", "www.google.com"),
            ("https://www.linkedin.com:443/in/someone?trk=feed", "www.linkedin.com"),
            ("https://user:password@mail.example.org/inbox/123", "mail.example.org"),
            ("https://example.com./path", "example.com"),
            ("android-app://com.google.android.gm/", "com.google.android.gm"),
            ("https://ex" + chr(0) + "ample.com/" + chr(10), "example.com"),
            ("https://api.dashti.se/x", "api.dashti.se"),
            ("https://1.example.com/x", "1.example.com"),
        ],
    )
    def test_the_host_is_kept(self, referrer: str, host: str):
        assert _referrer_host(referrer) == host

    @pytest.mark.parametrize(
        "referrer",
        [
            None,
            "",
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
        ],
    )
    def test_no_host_is_stored_for_these(self, referrer: str | None):
        assert _referrer_host(referrer) is None

    def test_the_beacon_stores_the_host_or_null(self, client: TestClient):
        for path, referrer in [
            ("/a", "https://www.linkedin.com/in/someone?trk=feed"),
            ("/b", "https://dashti.se/colophon"),
            ("/c", "http://192.168.1.10:8080/intranet"),
        ]:
            response = client.post(BEACON, json={"page_path": path, "referrer": referrer})
            assert response.status_code == 204

        assert sorted(_stored(PageView.page_path, PageView.referrer)) == [
            ("/a", "www.linkedin.com"),
            ("/b", None),
            ("/c", None),
        ]


class TestDeclinedPageViews:
    """Sec-GPC: 1 or DNT: 1 gets 204 and records nothing; any other value is counted."""

    @pytest.fixture
    def lookup(self, monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
        """The country lookup, answering "SE", with the back-fill on the test database."""
        mock = AsyncMock(return_value="SE")
        monkeypatch.setattr("app.api.v1.analytics.get_country_code", mock)
        monkeypatch.setattr("app.api.v1.analytics.AsyncSessionLocal", TestSessionLocal)
        return mock

    @pytest.mark.parametrize("header", ["Sec-GPC", "DNT"])
    def test_a_1_stores_nothing_and_looks_nothing_up(
        self, client: TestClient, lookup: AsyncMock, header: str
    ):
        response = client.post(BEACON, json={"page_path": "/a"}, headers={header: "1"})

        assert response.status_code == 204
        assert response.content == b""
        assert _stored(PageView.page_path) == []
        lookup.assert_not_awaited()

    @pytest.mark.parametrize(
        ("header", "value"), [("Sec-GPC", "0"), ("DNT", "0"), ("Sec-GPC", "true"), ("DNT", "")]
    )
    def test_any_other_value_is_counted(
        self, client: TestClient, lookup: AsyncMock, header: str, value: str
    ):
        response = client.post(BEACON, json={"page_path": "/a"}, headers={header: value})

        assert response.status_code == 204
        assert _stored(PageView.page_path, PageView.country) == [("/a", "SE")]
        lookup.assert_awaited_once()

    def test_declined_beacons_still_use_up_the_public_tier(self, client: TestClient):
        limit = int(settings.RATE_LIMIT_PUBLIC.split("/")[0])
        declined = {"Sec-GPC": "1"}

        for i in range(limit):
            response = client.post(BEACON, json={"page_path": "/"}, headers=declined)
            assert response.status_code == 204, f"request {i + 1}: {response.status_code}"

        assert client.post(BEACON, json={"page_path": "/"}, headers=declined).status_code == 429


class TestAnalyticsSummaryEndpoint:
    """Tests for GET /analytics/stats/summary endpoint."""

    def test_summary_requires_authentication(self, client: TestClient):
        """Test that summary endpoint requires authentication."""
        response = client.get("/api/v1/analytics/stats/summary")
        assert response.status_code == 401

    def test_summary_requires_admin(self, client: TestClient, test_user_in_db: dict[str, Any]):
        """Test that summary endpoint requires admin privileges."""
        response = client.get(
            "/api/v1/analytics/stats/summary",
            headers=test_user_in_db["headers"],
        )
        assert response.status_code == 403

    def test_summary_success_with_admin(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test analytics summary with admin authentication."""
        response = client.get(
            "/api/v1/analytics/stats/summary",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_views" in data
        assert "unique_visitors" in data
        assert "top_pages" in data
        assert "daily_views" in data
        assert "period_days" in data
        assert "outbound_clicks" in data

    def test_summary_excludes_event_rows_and_aggregates_outbound(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """D3-M-01: synthetic /event/ rows stay OUT of page metrics and are
        surfaced separately as aggregated outbound_clicks."""
        for path in ["/", "/experience/hermes"]:
            client.post("/api/v1/analytics/track/pageview", json={"page_path": path})
        for path in [
            "/event/outbound/linkedin/hero",
            "/event/outbound/linkedin/hero",
            "/event/outbound/github/footer",
        ]:
            client.post("/api/v1/analytics/track/pageview", json={"page_path": path})

        data = client.get(
            "/api/v1/analytics/stats/summary",
            headers=admin_user_in_db["headers"],
        ).json()

        # Page-view metrics count the 2 real views only, never the 3 events.
        assert data["total_views"] == 2
        page_paths = {p["path"] for p in data["top_pages"]}
        assert page_paths == {"/", "/experience/hermes"}
        assert not any(p.startswith("/event/") for p in page_paths)
        assert sum(d["views"] for d in data["daily_views"]) == 2

        # Outbound clicks aggregated with the '/event/outbound/' prefix stripped.
        clicks = {c["destination"]: c["count"] for c in data["outbound_clicks"]}
        assert clicks == {"linkedin/hero": 2, "github/footer": 1}

    def test_summary_excludes_admin_navigations(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """The owner's own CMS traffic is not visitor traffic.

        router.afterEach fired on /admin routes too, so every navigation inside
        the admin SPA was POSTed to the PUBLIC track endpoint and landed in the
        same table this summary reports on. The frontend no longer sends them,
        but rows already in the table must not skew history either -- hence the
        read-time '/admin%' filter this test pins.
        """
        # Two User-Agents, so the two browsers get two daily visitor keys.
        for path in ["/", "/experience/hermes"]:
            client.post(BEACON, json={"page_path": path}, headers={"User-Agent": "visitor-agent"})
        for path in ["/admin", "/admin/companies", "/admin/cv"]:
            client.post(BEACON, json={"page_path": path}, headers={"User-Agent": "admin-agent"})

        data = client.get(
            "/api/v1/analytics/stats/summary",
            headers=admin_user_in_db["headers"],
        ).json()

        assert data["total_views"] == 2
        page_paths = {p["path"] for p in data["top_pages"]}
        assert page_paths == {"/", "/experience/hermes"}
        assert not any(p.startswith("/admin") for p in page_paths)
        assert sum(d["views"] for d in data["daily_views"]) == 2
        # A key with admin paths only has no real page view, so it is not a visitor.
        assert len({key for (key,) in _stored(PageView.session_id)}) == 2
        assert data["unique_visitors"] == 1

    def test_summary_default_period(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test analytics summary uses 30-day default period."""
        response = client.get(
            "/api/v1/analytics/stats/summary",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 30

    def test_summary_custom_period(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test analytics summary with custom period."""
        response = client.get(
            "/api/v1/analytics/stats/summary?days=7",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7

    def test_summary_period_too_small(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test analytics summary rejects period less than 1 day."""
        response = client.get(
            "/api/v1/analytics/stats/summary?days=0",
            headers=admin_user_in_db["headers"],
        )
        # FastAPI returns 422 for Query parameter validation errors
        assert response.status_code == 422

    def test_summary_period_too_large(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test analytics summary rejects period more than 365 days."""
        response = client.get(
            "/api/v1/analytics/stats/summary?days=400",
            headers=admin_user_in_db["headers"],
        )
        # FastAPI returns 422 for Query parameter validation errors
        assert response.status_code == 422

    def test_summary_with_tracked_pageviews(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test analytics summary includes tracked pageviews."""
        # Track some pageviews first
        client.post("/api/v1/analytics/track/pageview", json={"page_path": "/home"})
        client.post("/api/v1/analytics/track/pageview", json={"page_path": "/home"})
        client.post("/api/v1/analytics/track/pageview", json={"page_path": "/about"})

        response = client.get(
            "/api/v1/analytics/stats/summary",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_views"] >= 3

    def test_summary_top_pages_ordered(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test that top pages are ordered by view count."""
        # Track pageviews with different frequencies
        for _ in range(5):
            client.post("/api/v1/analytics/track/pageview", json={"page_path": "/popular"})
        for _ in range(2):
            client.post("/api/v1/analytics/track/pageview", json={"page_path": "/less-popular"})

        response = client.get(
            "/api/v1/analytics/stats/summary",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        if len(data["top_pages"]) >= 2:
            # Most popular page should be first
            assert data["top_pages"][0]["views"] >= data["top_pages"][1]["views"]


class TestVisitorStatsEndpoint:
    """Tests for GET /analytics/stats/visitors endpoint."""

    def test_visitors_requires_authentication(self, client: TestClient):
        """Test that visitors endpoint requires authentication."""
        response = client.get("/api/v1/analytics/stats/visitors")
        assert response.status_code == 401

    def test_visitors_requires_admin(self, client: TestClient, test_user_in_db: dict[str, Any]):
        """Test that visitors endpoint requires admin privileges."""
        response = client.get(
            "/api/v1/analytics/stats/visitors",
            headers=test_user_in_db["headers"],
        )
        assert response.status_code == 403

    def test_visitors_success_with_admin(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test visitor stats with admin authentication."""
        response = client.get(
            "/api/v1/analytics/stats/visitors",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_sessions" in data
        assert "top_countries" in data
        assert "period_days" in data

    def test_visitors_default_period(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test visitor stats uses 7-day default period."""
        response = client.get(
            "/api/v1/analytics/stats/visitors",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 7

    def test_visitors_custom_period(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test visitor stats with custom period."""
        response = client.get(
            "/api/v1/analytics/stats/visitors?days=14",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["period_days"] == 14

    def test_visitors_period_validation(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test visitor stats validates period range."""
        # Too small - FastAPI returns 422 for Query parameter validation errors
        response = client.get(
            "/api/v1/analytics/stats/visitors?days=0",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 422

        # Too large
        response = client.get(
            "/api/v1/analytics/stats/visitors?days=500",
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 422
