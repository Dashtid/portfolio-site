"""Tests for the OSS sync service.

Avoids the network entirely — the fetch path is tested at the endpoint
layer with a mocked refresh. Here we cover the pure-function pipeline
(_classify_response + _node_to_row) against the real fixture, plus the
PAT-missing failure mode.
"""

import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.config import settings
from app.models.oss import OssContribution
from app.schemas.oss import OssDashboardResponse
from app.services.bucket_classifier import Bucket
from app.services.oss_sync import OssSyncError, OssSyncService, _node_to_row
from tests.conftest import TestSessionLocal

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "oss_dashboard_response.json"


@pytest.fixture
def parsed_fixture() -> OssDashboardResponse:
    with FIXTURE_PATH.open("r", encoding="utf-8") as fh:
        return OssDashboardResponse.model_validate(json.load(fh))


class TestClassifyResponsePipeline:
    def test_fixture_produces_expected_bucket_distribution(
        self, parsed_fixture: OssDashboardResponse
    ):
        rows = OssSyncService._classify_response(parsed_fixture)

        bucket_counts: dict[str, int] = {}
        for row in rows:
            bucket_counts[row.bucket] = bucket_counts.get(row.bucket, 0) + 1

        # Fixture composition (see oss_dashboard_response.json):
        # - 1 PR -> NOW (DefectDojo Garak parser)
        # - 1 PR -> WAITING (syft empty-SBOM fix)
        # - 1 Issue -> WATCHING (stereoscope cache TTL)
        # - 1 PR + 1 Issue -> DONE (presidio merged, pydicom not-planned)
        # - 1 Issue -> WATCHING (grype false-positive, substantive comment)
        # - 1 PR -> WATCHING (fo-dicom drop, but len(comment)=80? — < threshold,
        #   so it's dropped; only the grype issue survives the heuristic)
        # - 1 PR -> DONE (dependency-track substantive comment, now merged)
        assert bucket_counts[Bucket.NOW.value] == 1
        assert bucket_counts[Bucket.WAITING.value] == 1
        # 1 authored-open issue + 1 substantive-commented open issue.
        # The fo-dicom PR's lone Dashtid comment is "+1, this matches the
        # pattern we landed in pydicom last quarter." (62 chars < 80) so
        # it's dropped, leaving 2 WATCHING rows.
        assert bucket_counts[Bucket.WATCHING.value] == 2
        # 1 merged authored + 1 closed authored issue + 1 commented-merged.
        assert bucket_counts[Bucket.DONE.value] == 3

    def test_every_row_has_node_id_and_bucket(self, parsed_fixture: OssDashboardResponse):
        rows = OssSyncService._classify_response(parsed_fixture)
        assert all(r.github_node_id for r in rows)
        assert all(r.bucket in {b.value for b in Bucket if b != Bucket.LATER} for r in rows)

    def test_pr_rows_have_kind_pr_and_issue_rows_have_kind_issue(
        self, parsed_fixture: OssDashboardResponse
    ):
        rows = OssSyncService._classify_response(parsed_fixture)
        for row in rows:
            if row.url.startswith("https://github.com/") and "/pull/" in row.url:
                assert row.kind == "pr"
            elif "/issues/" in row.url:
                assert row.kind == "issue"

    def test_node_id_dedup(self, parsed_fixture: OssDashboardResponse):
        """Same fixture run twice must not produce duplicates."""
        rows = OssSyncService._classify_response(parsed_fixture)
        node_ids = [r.github_node_id for r in rows]
        assert len(node_ids) == len(set(node_ids))


class TestNodeToRowMapping:
    def test_pr_node_maps_merge_state_to_row(self, parsed_fixture: OssDashboardResponse):
        first_pr = parsed_fixture.authored_open_prs.nodes[0]
        row = _node_to_row(first_pr, bucket=Bucket.NOW)
        assert row.kind == "pr"
        assert row.repo_name_with_owner == "DefectDojo/django-DefectDojo"
        assert row.number == 14878
        assert row.state == "OPEN"
        assert row.bucket == Bucket.NOW.value
        assert row.author_login == "Dashtid"

    def test_issue_node_maps_state_and_no_merge_fields(self, parsed_fixture: OssDashboardResponse):
        issue = parsed_fixture.authored_open_issues.nodes[0]
        row = _node_to_row(issue, bucket=Bucket.WATCHING)
        assert row.kind == "issue"
        assert row.merged_at is None
        assert row.is_draft is False

    def test_pr_with_no_author_lands_null(self, parsed_fixture: OssDashboardResponse):
        """Forced edge case: GitHub returns null author on ghost-user threads."""
        pr = parsed_fixture.authored_open_prs.nodes[0]
        pr.author = None
        row = _node_to_row(pr, bucket=Bucket.NOW)
        assert row.author_login is None


class TestRefreshGuards:
    @pytest.mark.asyncio
    async def test_refresh_raises_when_pat_missing(self, monkeypatch):
        """If the dashboard PAT isn't configured, the service raises
        OssSyncError instead of attempting a token-less call to GitHub."""
        monkeypatch.setattr(settings, "GITHUB_OSS_DASHBOARD_PAT", None)
        service = OssSyncService()
        with pytest.raises(OssSyncError, match="GITHUB_OSS_DASHBOARD_PAT") as exc_info:
            async with service._github_client():
                pass
        # The endpoint discriminates 503 vs 502 on this attribute.
        assert exc_info.value.is_pat_missing is True


class TestPatSanitization:
    def test_sanitize_replaces_configured_pat(self, monkeypatch):
        """A leaked PAT in any string gets redacted before logging/return."""
        from app.services.oss_sync import _sanitize_pat

        fake_pat = "ghp_fakefakefakefakefakefakefakefake1234"
        monkeypatch.setattr(settings, "GITHUB_OSS_DASHBOARD_PAT", fake_pat)
        original = f"401 Unauthorized — Authorization: Bearer {fake_pat}"
        sanitized = _sanitize_pat(original)
        assert fake_pat not in sanitized
        assert "***REDACTED***" in sanitized

    def test_sanitize_passthrough_when_no_pat_configured(self, monkeypatch):
        """In tests/dev where the PAT is unset, the helper must not raise."""
        from app.services.oss_sync import _sanitize_pat

        monkeypatch.setattr(settings, "GITHUB_OSS_DASHBOARD_PAT", None)
        assert _sanitize_pat("nothing to redact") == "nothing to redact"


class TestRefreshIntegration:
    """End-to-end refresh: mock GraphQL fetch, real DB swap, real classifier."""

    @pytest.mark.asyncio
    async def test_refresh_replaces_table_and_returns_telemetry(
        self,
        client,
        monkeypatch,
        parsed_fixture: OssDashboardResponse,
    ):
        """Refresh wipes existing rows and inserts the classifier output.

        ``client`` fixture is unused beyond DB table creation but is needed
        to populate the conftest-managed schema; without it the OSS table
        doesn't exist.
        """
        _ = client

        # Seed a row that should be wiped by the refresh.
        stale = OssContribution(
            id="stale-row-id",
            github_node_id="STALE_NODE",
            kind="pr",
            repo_name_with_owner="anchore/syft",
            number=1,
            title="stale",
            url="https://example.com",
            state="OPEN",
            is_draft=False,
            author_login="Dashtid",
            bucket="WAITING",
            created_at=parsed_fixture.authored_open_prs.nodes[0].created_at,
            last_activity_at=parsed_fixture.authored_open_prs.nodes[0].updated_at,
            closed_at=None,
            merged_at=None,
        )
        async with TestSessionLocal() as setup_session:
            setup_session.add(stale)
            await setup_session.commit()

        # Mock the network: bypass _fetch_payload to return the fixture.
        async def fake_fetch(self):
            return parsed_fixture.model_dump(by_alias=True)

        monkeypatch.setattr(OssSyncService, "_fetch_payload", fake_fetch)

        service = OssSyncService()
        async with TestSessionLocal() as session:
            result = await service.refresh(session)

        # Telemetry mirrors the fixture's rateLimit selection.
        assert result.rate_limit_cost == 7
        assert result.rate_limit_remaining == 4993
        assert result.contributions_count > 0

        # Stale row is gone; new rows replaced it.
        async with TestSessionLocal() as verify_session:
            rows = (await verify_session.execute(select(OssContribution))).scalars().all()
            assert len(rows) == result.contributions_count
            assert all(r.id != "stale-row-id" for r in rows)
            # Buckets distributed across all classifier outputs.
            buckets = {r.bucket for r in rows}
            assert "NOW" in buckets
            assert "WAITING" in buckets
            assert "DONE" in buckets

    @pytest.mark.asyncio
    async def test_refresh_preserves_merged_history_outside_window(
        self,
        client,
        monkeypatch,
        parsed_fixture: OssDashboardResponse,
    ):
        """Merged self-authored PRs are permanent public evidence (the
        homepage Open Source strip reads them) — a refresh whose 30-day
        GraphQL window no longer returns them must NOT delete them.
        Non-merged rows and other-author rows are still replaced wholesale.
        """
        _ = client

        old_merged = OssContribution(
            id="old-merged-id",
            github_node_id="OLD_MERGED_NODE",
            kind="pr",
            repo_name_with_owner="anchore/syft",
            number=4791,
            title="fix(cyclonedx): exclude distro group from package name",
            url="https://github.com/anchore/syft/pull/4791",
            state="MERGED",
            is_draft=False,
            author_login="Dashtid",
            bucket="DONE",
            created_at=parsed_fixture.authored_open_prs.nodes[0].created_at,
            last_activity_at=parsed_fixture.authored_open_prs.nodes[0].updated_at,
            closed_at=parsed_fixture.authored_open_prs.nodes[0].created_at,
            merged_at=parsed_fixture.authored_open_prs.nodes[0].created_at,
        )
        other_author_merged = OssContribution(
            id="other-author-id",
            github_node_id="OTHER_AUTHOR_NODE",
            kind="pr",
            repo_name_with_owner="anchore/grype",
            number=9999,
            title="someone else's merged PR",
            url="https://github.com/anchore/grype/pull/9999",
            state="MERGED",
            is_draft=False,
            author_login="someone-else",
            bucket="DONE",
            created_at=parsed_fixture.authored_open_prs.nodes[0].created_at,
            last_activity_at=parsed_fixture.authored_open_prs.nodes[0].updated_at,
            closed_at=parsed_fixture.authored_open_prs.nodes[0].created_at,
            merged_at=parsed_fixture.authored_open_prs.nodes[0].created_at,
        )
        async with TestSessionLocal() as setup_session:
            setup_session.add_all([old_merged, other_author_merged])
            await setup_session.commit()

        async def fake_fetch(self):
            return parsed_fixture.model_dump(by_alias=True)

        monkeypatch.setattr(OssSyncService, "_fetch_payload", fake_fetch)

        service = OssSyncService()
        async with TestSessionLocal() as session:
            result = await service.refresh(session)

        async with TestSessionLocal() as verify_session:
            rows = (await verify_session.execute(select(OssContribution))).scalars().all()
            ids = {r.id for r in rows}
            # Self-authored merged history survives the refresh...
            assert "old-merged-id" in ids
            # ...other-author rows are replaced like everything else...
            assert "other-author-id" not in ids
            # ...and the fresh classification set landed alongside it.
            assert len(rows) == result.contributions_count + 1
