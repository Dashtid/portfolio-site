"""
Tests for analytics API module
"""

import logging
from typing import Any

from fastapi.testclient import TestClient

from app.api.v1.analytics import logger, router


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
    """Tests for POST /analytics/track/pageview endpoint."""

    def test_track_pageview_success(self, client: TestClient):
        """Test tracking a page view successfully."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": "/projects", "referrer": "https://google.com"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_path"] == "/projects"
        assert data["referrer"] == "https://google.com"
        assert "id" in data
        assert "timestamp" in data

    def test_track_pageview_truncates_long_values_to_column_width(self, client: TestClient):
        """Long UTM-style paths/referrers (501-2048 chars) are accepted and
        stored truncated to the String(500) columns instead of 500-ing at
        INSERT (Postgres 22001) or dropping the beacon with a 422. The UA
        header is capped at 512 before the unbounded Text column.
        """
        long_path = "/campaign?" + "utm_content=" + "x" * 900
        long_ref = "https://example.com/?ref=" + "y" * 900
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": long_path, "referrer": long_ref},
            headers={"User-Agent": "A" * 2000},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_path"] == long_path[:500]
        assert data["referrer"] == long_ref[:500]

    def test_track_pageview_rejects_over_2048(self, client: TestClient):
        """Beyond the generous 2048 cap the beacon is rejected outright —
        nothing legitimate is that long."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": "/x" + "z" * 2100},
        )
        assert response.status_code == 422

    def test_track_pageview_without_referrer(self, client: TestClient):
        """Test tracking a page view without referrer."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": "/about"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_path"] == "/about"
        assert data["referrer"] is None

    def test_track_pageview_home_page(self, client: TestClient):
        """Test tracking home page view."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": "/"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_path"] == "/"

    def test_track_pageview_with_query_params(self, client: TestClient):
        """Test tracking page view with query parameters."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": "/projects?filter=featured"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page_path"] == "/projects?filter=featured"

    def test_track_pageview_missing_page_path(self, client: TestClient):
        """Test tracking page view without page_path fails."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={},
        )
        assert response.status_code == 422  # Validation error

    def test_track_pageview_empty_page_path(self, client: TestClient):
        """Test tracking page view with empty page_path."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": ""},
        )
        # Implementation may allow empty string or reject it
        # Either behavior is acceptable
        assert response.status_code in [200, 422]

    def test_track_pageview_captures_x_forwarded_for(self, client: TestClient):
        """Test that X-Forwarded-For header is captured for IP."""
        response = client.post(
            "/api/v1/analytics/track/pageview",
            json={"page_path": "/test"},
            headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"},
        )
        assert response.status_code == 200
        # Note: IP is stored in DB but not returned in response

    def test_track_multiple_pageviews(self, client: TestClient):
        """Test tracking multiple page views creates separate records."""
        paths = ["/", "/about", "/projects", "/contact"]
        ids = []
        for path in paths:
            response = client.post(
                "/api/v1/analytics/track/pageview",
                json={"page_path": path},
            )
            assert response.status_code == 200
            ids.append(response.json()["id"])

        # All IDs should be unique
        assert len(ids) == len(set(ids))


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
