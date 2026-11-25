"""
Tests for OriginCheckMiddleware: a state-changing request that carries an
auth cookie must come from an allowed origin.

SameSite=Lax already keeps the cookies off cross-site requests; these cover
the same-site case (another *.dashti.se host), where a bodyless POST, a form
POST or a multipart upload needs no CORS preflight.
"""

from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from app.middleware.performance import metrics

FOREIGN = "https://attacker.dashti.se"
SITE = "https://dashti.se"


def _reset(client: TestClient, headers: dict[str, str]):
    return client.post("/api/v1/metrics/reset", headers=headers)


class TestCookieAuthenticatedWrites:
    def test_foreign_origin_is_refused_before_the_handler_runs(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        client.cookies.set("access_token", admin_user_in_db["access_token"])
        metrics.incr("origin_check.marker")
        marker = metrics.counters["origin_check.marker"]

        response = _reset(client, {"Origin": FOREIGN})

        assert response.status_code == 403
        assert response.json() == {"detail": "Cross-origin request refused"}
        # A reset that ran would have cleared the counter.
        assert metrics.counters["origin_check.marker"] == marker

    def test_the_site_origin_is_allowed(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        client.cookies.set("access_token", admin_user_in_db["access_token"])

        assert _reset(client, {"Origin": SITE}).status_code == 200

    def test_a_null_origin_is_refused(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        client.cookies.set("access_token", admin_user_in_db["access_token"])

        assert _reset(client, {"Origin": "null"}).status_code == 403

    def test_without_origin_a_same_site_fetch_is_refused(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        client.cookies.set("access_token", admin_user_in_db["access_token"])

        assert _reset(client, {"Sec-Fetch-Site": "same-site"}).status_code == 403
        assert _reset(client, {"Sec-Fetch-Site": "cross-site"}).status_code == 403

    def test_a_client_sending_neither_header_is_allowed(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """No browser sends an unsafe request without Origin and Sec-Fetch-Site."""
        client.cookies.set("access_token", admin_user_in_db["access_token"])

        assert _reset(client, {}).status_code == 200

    def test_a_same_origin_fetch_is_allowed(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """A script on the API's own origin; page code cannot set Sec-Fetch-Site."""
        client.cookies.set("access_token", admin_user_in_db["access_token"])

        headers = {"Origin": "https://api.dashti.se", "Sec-Fetch-Site": "same-origin"}

        assert _reset(client, headers).status_code == 200

    def test_bearer_only_requests_are_not_checked(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        headers = {**admin_user_in_db["headers"], "Origin": FOREIGN}

        assert _reset(client, headers).status_code == 200

    def test_reads_are_not_checked(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        client.cookies.set("access_token", admin_user_in_db["access_token"])

        assert client.get("/api/v1/metrics/", headers={"Origin": FOREIGN}).status_code == 200

    def test_a_preflight_from_the_site_still_passes(self, client: TestClient):
        response = client.options(
            "/api/v1/metrics/reset",
            headers={"Origin": SITE, "Access-Control-Request-Method": "POST"},
        )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == SITE


class TestRefreshCookieRoutes:
    def test_foreign_logout_keeps_the_session(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        client.cookies.set("refresh_token", admin_user_in_db["refresh_token"])

        refused = client.post("/api/v1/auth/logout", headers={"Origin": FOREIGN})

        assert refused.status_code == 403
        assert "set-cookie" not in refused.headers
        client.cookies.clear()
        refreshed = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": admin_user_in_db["refresh_token"]}
        )
        assert refreshed.status_code == 200

    def test_foreign_refresh_is_refused_without_rotating(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        client.cookies.set("refresh_token", admin_user_in_db["refresh_token"])

        refused = client.post("/api/v1/auth/refresh", headers={"Origin": FOREIGN})

        assert refused.status_code == 403
        assert "set-cookie" not in refused.headers
        assert client.post("/api/v1/auth/refresh", headers={"Origin": SITE}).status_code == 200


class TestUpload:
    def _upload(self, client: TestClient, origin: str):
        return client.post(
            "/api/v1/documents/upload",
            files={"file": ("paper.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")},
            headers={"Origin": origin},
        )

    def test_foreign_upload_writes_nothing(
        self, client: TestClient, admin_user_in_db: dict[str, Any], tmp_path: Path, monkeypatch
    ):
        monkeypatch.setattr("app.api.v1.documents._UPLOAD_DIR", tmp_path)
        client.cookies.set("access_token", admin_user_in_db["access_token"])

        assert self._upload(client, FOREIGN).status_code == 403
        assert list(tmp_path.iterdir()) == []

        # Control: the same upload from the site is stored.
        assert self._upload(client, SITE).status_code == 200
        assert len(list(tmp_path.iterdir())) == 1
