"""The CI workflows keep the guards their deploy and backup jobs rely on.

Each workflow under .github/workflows is parsed with PyYAML. The tests pin
the settings that decide which branch deploys, which job holds which token
scope, and what a deploy job checks before and after it ships.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"


def _load(name: str) -> dict[Any, Any]:
    workflow = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    assert isinstance(workflow, dict), name
    return workflow


def _triggers(workflow: dict[Any, Any]) -> dict[str, Any]:
    # YAML 1.1 reads the bare key `on` as the boolean True.
    triggers = workflow.get("on", workflow.get(True))
    assert isinstance(triggers, dict)
    return triggers


def _condition(job: dict[str, Any]) -> str:
    """A job's `if:` with its line breaks and indentation folded to single spaces."""
    return " ".join(str(job["if"]).split())


def test_the_pipeline_runs_for_main_only() -> None:
    triggers = _triggers(_load("ci-cd.yml"))
    assert {event: triggers[event]["branches"] for event in triggers} == {
        "push": ["main"],
        "pull_request": ["main"],
        "merge_group": ["main"],
    }


def test_deploys_and_push_e2e_runs_accept_main_only() -> None:
    jobs = _load("ci-cd.yml")["jobs"]
    for name in ("e2e-tests", "deploy-frontend", "deploy-backend"):
        condition = _condition(jobs[name])
        assert "github.ref == 'refs/heads/main'" in condition, name
        assert condition.count("github.ref") == 1, name


def test_the_rebake_deploys_from_main_only() -> None:
    rebake = _load("rebake-frontend.yml")["jobs"]["rebake"]
    assert _condition(rebake) == "github.ref == 'refs/heads/main'"


def test_only_the_backup_keepalive_job_holds_actions_write() -> None:
    # actions: write can delete the backup artifacts, so it stays out of the
    # jobs that hold the Fly tokens and the database password.
    backup = _load("db-backup.yml")
    assert backup["permissions"] == {"contents": "read"}
    holders = [
        name
        for name, job in backup["jobs"].items()
        if (job.get("permissions") or {}).get("actions") == "write"
    ]
    assert holders == ["keepalive"]
    keepalive = backup["jobs"]["keepalive"]
    assert keepalive["permissions"] == {"actions": "write"}
    [step] = keepalive["steps"]
    assert "uses" not in step
    assert "db-backup.yml/enable" in step["run"]
    assert "secrets." not in yaml.safe_dump(keepalive)
    # No `needs` either way: a failed enable call must not stop the dumps.
    assert all("needs" not in job for job in backup["jobs"].values())


def _uses(job: dict[str, Any], action: str) -> list[dict[str, Any]]:
    """The steps of `job` that run `action` (owner/repo), at any pinned ref."""
    return [step for step in job["steps"] if str(step.get("uses", "")).startswith(f"{action}@")]


@pytest.mark.parametrize(
    ("workflow", "job"), [("ci-cd.yml", "deploy-frontend"), ("rebake-frontend.yml", "rebake")]
)
def test_vercel_deploy_jobs_restore_no_npm_cache(workflow: str, job: str) -> None:
    # The npm cache is written by the jobs that run the frontend's test and
    # build tooling; the deploy jobs hold VERCEL_TOKEN and must not unpack it.
    [setup_node] = _uses(_load(workflow)["jobs"][job], "actions/setup-node")
    settings = setup_node["with"]
    assert "cache" not in settings
    assert "cache-dependency-path" not in settings
    assert settings["package-manager-cache"] is False


def test_no_checkout_leaves_the_job_token_on_disk() -> None:
    # No later step pushes or fetches with the job token, so a persisted copy
    # would only serve dependency code that reads it.
    checkouts = {
        f"{path.name}:{name}": step
        for path in sorted(WORKFLOWS.glob("*.yml"))
        for name, job in _load(path.name)["jobs"].items()
        for step in _uses(job, "actions/checkout")
    }
    assert len(checkouts) >= 13
    kept = [
        where
        for where, step in checkouts.items()
        if step.get("with", {}).get("persist-credentials") is not False
    ]
    assert kept == []


@pytest.mark.parametrize("name", ["deploy-frontend", "deploy-backend"])
def test_deploys_wait_for_the_security_scan_and_the_dependency_review(name: str) -> None:
    job = _load("ci-cd.yml")["jobs"][name]
    assert {"security-scan", "dependency-review"} <= set(job["needs"])
    condition = _condition(job)
    # Without !cancelled() a skipped dependency-review would skip the deploy.
    assert condition.startswith("!cancelled() && ")
    assert "needs.security-scan.result == 'success'" in condition
    assert (
        "(needs.dependency-review.result == 'success'"
        " || needs.dependency-review.result == 'skipped')"
    ) in condition


def test_dependency_review_also_checks_the_range_a_push_adds() -> None:
    review = _load("ci-cd.yml")["jobs"]["dependency-review"]
    assert _condition(review) == (
        "github.event_name == 'pull_request' || (github.event_name == 'push' && "
        "!github.event.forced && "
        "github.event.before != '0000000000000000000000000000000000000000')"
    )
    [step] = _uses(review, "actions/dependency-review-action")
    assert step["with"]["base-ref"] == (
        "${{ github.event_name == 'push' && github.event.before || '' }}"
    )
    assert step["with"]["head-ref"] == "${{ github.event_name == 'push' && github.sha || '' }}"


def test_the_changes_job_needs_no_fetch_after_checkout() -> None:
    # With full history the filter finds the pushed range's base locally; a
    # depth-1 clone would make it fetch, and without credentials.
    [checkout] = _uses(_load("ci-cd.yml")["jobs"]["changes"], "actions/checkout")
    assert checkout["with"] == {"fetch-depth": 0, "persist-credentials": False}
