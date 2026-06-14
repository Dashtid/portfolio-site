"""Tests for the admin OSS dashboard HTTP surface.

GET is exercised end-to-end against the test DB. POST is exercised in
two failure modes (PAT missing, GraphQL exception) and one success
mode (mocked refresh returns a fake OssRefreshResult). The actual
GitHub call is never made.
"""

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.models.oss import OssContribution
from app.schemas.oss import OssRefreshResult
from app.services.bucket_classifier import Bucket
from app.services.oss_sync import OssSyncError, oss_sync_service
from tests.conftest import TestSessionLocal


def _make_row(bucket: Bucket, **overrides) -> OssContribution:
    base: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "github_node_id": f"NODE_{uuid.uuid4().hex[:12]}",
        "kind": "pr",
        "repo_name_with_owner": "anchore/syft",
        "number": 42,
        "title": f"fix: thing in {bucket.value}",
        "url": "https://github.com/anchore/syft/pull/42",
        "state": "OPEN",
        "is_draft": False,
        "author_login": "Dashtid",
        "bucket": bucket.value,
        "created_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_activity_at": datetime(2026, 6, 13, tzinfo=UTC),
        "closed_at": None,
        "merged_at": None,
    }
    base.update(overrides)
    return OssContribution(**base)


async def _seed_rows(rows: list[OssContribution]) -> None:
    async with TestSessionLocal() as session:
        session.add_all(rows)
        await session.commit()


class TestGetOssDashboard:
    @pytest.mark.asyncio
    async def test_admin_gets_empty_buckets_when_no_rows(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        response = client.get("/api/v1/admin/oss", headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        body = response.json()
        assert set(body["buckets"].keys()) == {b.value for b in Bucket}
        for value in body["buckets"].values():
            assert value == []
        assert body["lastRefreshAt"] is None
        assert len(body["trackedRepos"]) == 8

    @pytest.mark.asyncio
    async def test_admin_gets_rows_grouped_by_bucket(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        await _seed_rows(
            [
                _make_row(Bucket.NOW, title="Now row"),
                _make_row(Bucket.WAITING, title="Waiting row"),
                _make_row(Bucket.DONE, title="Done row 1"),
                _make_row(Bucket.DONE, title="Done row 2", number=43),
            ]
        )

        response = client.get("/api/v1/admin/oss", headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        body = response.json()
        assert len(body["buckets"][Bucket.NOW.value]) == 1
        assert len(body["buckets"][Bucket.WAITING.value]) == 1
        assert len(body["buckets"][Bucket.DONE.value]) == 2
        # last_refresh_at surfaces the latest synced_at (server-default).
        assert body["lastRefreshAt"] is not None

    def test_non_admin_rejected(self, client: TestClient, test_user_in_db: dict[str, Any]):
        response = client.get("/api/v1/admin/oss", headers=test_user_in_db["headers"])
        assert response.status_code in (401, 403)

    def test_unauthenticated_rejected(self, client: TestClient):
        response = client.get("/api/v1/admin/oss")
        assert response.status_code in (401, 403)


class TestRefreshOssDashboard:
    def test_non_admin_rejected(self, client: TestClient, test_user_in_db: dict[str, Any]):
        response = client.post("/api/v1/admin/oss/refresh", headers=test_user_in_db["headers"])
        assert response.status_code in (401, 403)

    def test_unauthenticated_rejected(self, client: TestClient):
        response = client.post("/api/v1/admin/oss/refresh")
        assert response.status_code in (401, 403)

    def test_returns_503_when_pat_unconfigured(
        self,
        client: TestClient,
        admin_user_in_db: dict[str, Any],
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Operator-actionable failure: missing PAT -> 503, not 500."""
        monkeypatch.setattr(settings, "GITHUB_OSS_DASHBOARD_PAT", None)
        response = client.post("/api/v1/admin/oss/refresh", headers=admin_user_in_db["headers"])
        assert response.status_code == 503
        assert "GITHUB_OSS_DASHBOARD_PAT" in response.json()["detail"]

    def test_returns_502_when_github_fetch_fails(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        async def _boom(session):  # noqa: ARG001
            raise OssSyncError("GitHub GraphQL fetch failed: timeout")

        with patch.object(oss_sync_service, "refresh", side_effect=_boom):
            response = client.post("/api/v1/admin/oss/refresh", headers=admin_user_in_db["headers"])
        assert response.status_code == 502
        assert "OSS dashboard refresh failed" in response.json()["detail"]

    def test_successful_refresh_returns_telemetry(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        fake = OssRefreshResult(
            contributions_count=7,
            rate_limit_cost=8,
            rate_limit_remaining=4992,
            finished_at=datetime(2026, 6, 14, 18, 0, tzinfo=UTC),
        )

        async def _fake_refresh(session):  # noqa: ARG001
            return fake

        with patch.object(oss_sync_service, "refresh", side_effect=_fake_refresh):
            response = client.post("/api/v1/admin/oss/refresh", headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        body = response.json()
        assert body["contributionsCount"] == 7
        assert body["rateLimitCost"] == 8
        assert body["rateLimitRemaining"] == 4992
        assert body["finishedAt"].startswith("2026-06-14T18:00:00")
