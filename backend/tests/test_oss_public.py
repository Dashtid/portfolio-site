"""Tests for the public OSS contributions endpoint (D3-FEAT-01).

The public surface must expose ONLY merged, non-draft PRs and only the
fields already visible on the upstream PR page — no auth, no author
logins, no workflow buckets, no in-flight items.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.models.oss import OssContribution
from app.services.bucket_classifier import Bucket
from tests.conftest import TestSessionLocal


def _make_row(**overrides) -> OssContribution:
    base: dict[str, Any] = {
        "id": str(uuid.uuid4()),
        "github_node_id": f"NODE_{uuid.uuid4().hex[:12]}",
        "kind": "pr",
        "repo_name_with_owner": "anchore/syft",
        "number": 4963,
        "title": "fix(dpkg): extract License field for opkg/ipkg entries",
        "url": "https://github.com/anchore/syft/pull/4963",
        "state": "MERGED",
        "is_draft": False,
        "author_login": "Dashtid",
        "bucket": Bucket.DONE.value,
        "created_at": datetime(2026, 6, 1, tzinfo=UTC),
        "last_activity_at": datetime(2026, 6, 15, tzinfo=UTC),
        "closed_at": datetime(2026, 6, 15, tzinfo=UTC),
        "merged_at": datetime(2026, 6, 15, tzinfo=UTC),
    }
    base.update(overrides)
    return OssContribution(**base)


async def _seed_rows(rows: list[OssContribution]) -> None:
    async with TestSessionLocal() as session:
        session.add_all(rows)
        await session.commit()


class TestPublicOssContributions:
    def test_empty_table_returns_empty_list_without_auth(self, client: TestClient):
        response = client.get("/api/v1/oss/contributions")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_returns_merged_prs_newest_first(self, client: TestClient):
        await _seed_rows(
            [
                _make_row(
                    number=4791,
                    merged_at=datetime(2026, 4, 18, tzinfo=UTC),
                    title="fix(cyclonedx): exclude distro group",
                ),
                _make_row(number=4963, merged_at=datetime(2026, 6, 15, tzinfo=UTC)),
            ]
        )

        response = client.get("/api/v1/oss/contributions")
        assert response.status_code == 200
        body = response.json()
        assert [row["number"] for row in body] == [4963, 4791]
        assert body[0]["repoNameWithOwner"] == "anchore/syft"
        assert body[0]["url"].startswith("https://github.com/")
        assert body[0]["mergedAt"].startswith("2026-06-15")

    @pytest.mark.asyncio
    async def test_excludes_everything_not_merged(self, client: TestClient):
        await _seed_rows(
            [
                _make_row(number=1, state="OPEN", merged_at=None, closed_at=None),
                _make_row(number=2, state="CLOSED", merged_at=None),
                _make_row(number=3, kind="issue", state="CLOSED"),
                _make_row(number=4, is_draft=True),
                _make_row(number=5),  # the only public row
            ]
        )

        response = client.get("/api/v1/oss/contributions")
        assert response.status_code == 200
        body = response.json()
        assert [row["number"] for row in body] == [5]

    @pytest.mark.asyncio
    async def test_excludes_other_authors_merged_prs(self, client: TestClient):
        """The commented-* syncs persist OTHER people's merged PRs that
        Dashtid reviewed — those must never surface as his contributions."""
        await _seed_rows(
            [
                _make_row(number=10, author_login="someone-else"),
                _make_row(number=11, author_login=None),
                _make_row(number=12),  # Dashtid's own
            ]
        )

        response = client.get("/api/v1/oss/contributions")
        assert response.status_code == 200
        assert [row["number"] for row in response.json()] == [12]

    @pytest.mark.asyncio
    async def test_dto_carries_no_person_or_workflow_fields(self, client: TestClient):
        await _seed_rows([_make_row()])

        response = client.get("/api/v1/oss/contributions")
        body = response.json()
        assert len(body) == 1
        assert set(body[0].keys()) == {"repoNameWithOwner", "number", "title", "url", "mergedAt"}
