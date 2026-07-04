"""
Tests for the admin-only Sentry-panel config endpoint (BACKEND-ADMIN-10).
"""

from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient


class TestSentryPanelEndpoint:
    def test_requires_admin(self, client: TestClient, test_user_in_db: dict[str, Any]):
        """Non-admin tokens get 401/403, never the panel config."""
        response = client.get("/api/v1/admin/sentry-panel", headers=test_user_in_db["headers"])
        assert response.status_code in (401, 403)

    def test_admin_gets_config_when_dsn_set(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """With DSN + URL configured, the panel reports ``enabled=True`` and
        the deep-link URL the admin dashboard should render."""
        with patch("app.api.v1.admin_panel.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = True
            mock_settings.SENTRY_DSN = "https://abc@o12345.ingest.sentry.io/12345"
            mock_settings.SENTRY_ISSUES_URL = (
                "https://test-org.sentry.io/issues/?project=12345&statsPeriod=24h"
            )

            response = client.get("/api/v1/admin/sentry-panel", headers=admin_user_in_db["headers"])

        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is True
        assert body["issues_url"].startswith("https://test-org.sentry.io/")

    def test_admin_gets_disabled_when_dsn_missing(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """No DSN -> ``enabled=False`` even if ERROR_TRACKING_ENABLED is true.

        Keeps the dashboard from rendering a misleading panel when Sentry
        was deliberately turned off in a deploy.
        """
        with patch("app.api.v1.admin_panel.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = True
            mock_settings.SENTRY_DSN = None
            mock_settings.SENTRY_ISSUES_URL = None

            response = client.get("/api/v1/admin/sentry-panel", headers=admin_user_in_db["headers"])

        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is False
        assert body["issues_url"] is None

    def test_admin_gets_disabled_when_error_tracking_off(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """ERROR_TRACKING_ENABLED=False overrides a configured DSN."""
        with patch("app.api.v1.admin_panel.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = False
            mock_settings.SENTRY_DSN = "https://abc@o12345.ingest.sentry.io/12345"
            mock_settings.SENTRY_ISSUES_URL = "https://example.sentry.io/issues/"

            response = client.get("/api/v1/admin/sentry-panel", headers=admin_user_in_db["headers"])

        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is False
        # URL still surfaces (admin could navigate to it manually if they
        # know it), but the dashboard hides the panel when enabled=False.
        assert body["issues_url"] == "https://example.sentry.io/issues/"

    def test_admin_gets_null_url_when_unset(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """DSN configured but no deep-link URL -> enabled=True, url=None.

        Lets the dashboard render an "errors enabled but no deep link
        configured" hint rather than a 404-prone link.
        """
        with patch("app.api.v1.admin_panel.settings") as mock_settings:
            mock_settings.ERROR_TRACKING_ENABLED = True
            mock_settings.SENTRY_DSN = "https://abc@o12345.ingest.sentry.io/12345"
            mock_settings.SENTRY_ISSUES_URL = None

            response = client.get("/api/v1/admin/sentry-panel", headers=admin_user_in_db["headers"])

        assert response.status_code == 200
        body = response.json()
        assert body["enabled"] is True
        assert body["issues_url"] is None

    def test_unauthenticated_rejected(self, client: TestClient):
        """No auth header -> 401/403, never the panel config."""
        response = client.get("/api/v1/admin/sentry-panel")
        assert response.status_code in (401, 403)
