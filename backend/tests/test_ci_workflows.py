"""The CI workflows keep the guards their deploy and backup jobs rely on.

Each workflow under .github/workflows is parsed with PyYAML. The tests pin
the settings that decide which branch deploys, which job holds which token
scope, and what a deploy job checks before and after it ships.
"""

from pathlib import Path
from typing import Any

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
