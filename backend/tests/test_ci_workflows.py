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
