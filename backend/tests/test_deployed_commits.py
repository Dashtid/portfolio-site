"""scripts/deployed-commits.py finds where each half of production was last deployed from.

ci-cd.yml's changes job filters the range from that commit to the pushed one,
so a half whose deploy failed, was skipped or never ran is deployed again by
the next push. These tests feed the script recorded API answers and git exit
codes, and one throwaway repository for the real git calls.
"""

import importlib.util
import shutil
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "deployed_commits", ROOT / "scripts" / "deployed-commits.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


deployed_commits = _load_script()

FRONTEND = "https://dashti.se"
BACKEND = "https://api.dashti.se"
URLS = {"frontend": FRONTEND, "backend": BACKEND}
F1, F2, B1, B0, HEAD = ("1" * 40, "2" * 40, "3" * 40, "4" * 40, "5" * 40)

Get = Callable[[str], object]


def _status(state: str, url: str = "") -> dict[str, str]:
    return {"state": state, "environment_url": url}


def _api(*deployments: tuple[int, str, str, list[dict[str, str]]]) -> tuple[Get, list[str]]:
    """A fake API over (id, sha, created_at, statuses) deployments, and the paths asked."""
    listing = [{"id": i, "sha": sha, "created_at": at} for i, sha, at, _ in deployments]
    statuses = {i: s for i, _, _, s in deployments}
    asked: list[str] = []

    def get(path: str) -> object:
        asked.append(path)
        if path.startswith("/deployments?"):
            return listing
        return statuses[int(path.split("/")[2])]

    return get, asked


# Newest first, as the API lists them. A frontend deploy adds an inactive
# status to the frontend deploy before it, and a backend deploy to the backend
# deploy before it.
RECORDS = (
    (5, F2, "2026-11-24T13:04:45Z", [_status("success", FRONTEND), _status("in_progress")]),
    (
        4,
        F1,
        "2026-11-24T03:55:07Z",
        [_status("inactive"), _status("success", FRONTEND + "/"), _status("in_progress")],
    ),
    (3, B1, "2026-11-24T03:53:26Z", [_status("success", BACKEND), _status("in_progress")]),
    (2, B0, "2026-11-15T17:01:29Z", [_status("inactive"), _status("success", BACKEND)]),
)


def test_each_half_takes_the_newest_deploy_that_succeeded_at_its_url() -> None:
    get, asked = _api(*RECORDS)
    assert deployed_commits.deployed_commits("production", URLS, get) == {
        "frontend": F2,
        "backend": B1,
    }
    assert asked[0] == "/deployments?environment=production&per_page=100"
    # Both halves were found by the third record, so the fourth is not read.
    assert asked[1:] == [f"/deployments/{i}/statuses?per_page=100" for i in (5, 4, 3)]


def test_failed_and_running_deploys_do_not_count_and_order_comes_from_created_at() -> None:
    newest = (6, HEAD, "2026-11-25T08:00:00Z", [_status("failure"), _status("in_progress")])
    get, _ = _api(*reversed(RECORDS), newest)
    assert deployed_commits.deployed_commits("production", URLS, get) == {
        "frontend": F2,
        "backend": B1,
    }


def test_a_url_without_a_successful_deploy_is_left_out_and_a_bad_commit_is_unknown() -> None:
    get, _ = _api((7, "not-a-sha", "2026-11-25T08:00:00Z", [_status("success", FRONTEND)]))
    assert deployed_commits.deployed_commits("production", URLS, get) == {"frontend": ""}


def _completed(code: int, stdout: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess([], code, stdout=stdout, stderr="")


def _fake_git(
    head: str, ancestors: Iterable[tuple[str, str]], known: Iterable[str]
) -> Callable[..., subprocess.CompletedProcess[str]]:
    """git rev-parse HEAD and merge-base --is-ancestor over a made-up history."""
    pairs, commits = set(ancestors), set(known) | {head}

    def git(*args: str) -> subprocess.CompletedProcess[str]:
        if args == ("rev-parse", "HEAD"):
            return _completed(0, f"{head}\n")
        assert args[:2] == ("merge-base", "--is-ancestor")
        older, newer = args[2:]
        if older not in commits or newer not in commits:
            return _completed(128)
        return _completed(0 if (older, newer) in pairs else 1)

    return git


@pytest.mark.parametrize(
    ("deployed", "expected"),
    [
        (HEAD, HEAD),  # production runs the pushed commit
        (B1, B1),  # behind: filter from the deployed commit
        (F2, HEAD),  # ahead (an older run re-run): nothing to catch up
        (F1, F1),  # another line of history: the tree diff decides
        (B0, ""),  # git does not know the commit: unknown
    ],
)
def test_filter_base(deployed: str, expected: str) -> None:
    git = _fake_git(HEAD, ancestors=[(B1, HEAD), (HEAD, F2)], known=[B1, F2, F1])
    assert deployed_commits.filter_base(deployed, HEAD, git) == expected


def _commit(repo: Path, message: str) -> str:
    # A throwaway repository: an identity of its own and no signing.
    subprocess.run(
        ["git", "-c", "user.name=test", "-c", "user.email=test", "-c", "commit.gpgsign=false"]
        + ["commit", "--allow-empty", "-q", "-m", message],
        cwd=repo,
        check=True,
    )
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, check=True, capture_output=True, text=True
    )
    return out.stdout.strip()


@pytest.mark.skipif(shutil.which("git") is None, reason="needs git, as the changes job has")
def test_filter_base_reads_git_history(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    first = _commit(tmp_path, "first")
    _commit(tmp_path, "second")
    tip = _commit(tmp_path, "tip")
    subprocess.run(["git", "checkout", "-q", "-b", "side", first], cwd=tmp_path, check=True)
    side = _commit(tmp_path, "side")
    monkeypatch.chdir(tmp_path)
    assert deployed_commits.filter_base(first, tip) == first
    assert deployed_commits.filter_base(tip, first) == first
    assert deployed_commits.filter_base(side, tip) == side
    assert deployed_commits.filter_base("0" * 40, tip) == ""


def _main(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, get: Get, git: Any = None) -> list[str]:
    output = tmp_path / "github_output"
    output.write_text("earlier=1\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    git = git or _fake_git(HEAD, ancestors=[(F2, HEAD), (B1, HEAD)], known=[F2, B1])
    argv = ["deployed-commits.py", "production", f"frontend={FRONTEND}", f"backend={BACKEND}"]
    assert deployed_commits.main(argv, get=get, git=git) == 0
    return output.read_text(encoding="utf-8").splitlines()


def test_main_appends_one_output_line_per_half(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    get, _ = _api(*RECORDS)
    assert _main(tmp_path, monkeypatch, get) == ["earlier=1", f"frontend={F2}", f"backend={B1}"]
    assert capsys.readouterr().out.count("[+]") == 2


def test_main_prints_the_pushed_commit_when_production_is_ahead(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    get, _ = _api(*RECORDS)
    git = _fake_git(HEAD, ancestors=[(HEAD, F2), (B1, HEAD)], known=[F2, B1])
    lines = _main(tmp_path, monkeypatch, get, git)
    assert lines[1:] == [f"frontend={HEAD}", f"backend={B1}"]


def test_any_lookup_failure_leaves_both_halves_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def down(path: str) -> object:
        raise OSError("connection refused")

    assert _main(tmp_path, monkeypatch, down)[1:] == ["frontend=", "backend="]
    out = capsys.readouterr().out
    assert "::warning::Could not read the production deployments: connection refused" in out
    get, _ = _api(*RECORDS)
    no_git = _fake_git("", ancestors=[], known=[])
    assert _main(tmp_path, monkeypatch, get, no_git)[1:] == ["frontend=", "backend="]


def test_usage_needs_an_environment_and_name_url_pairs() -> None:
    assert deployed_commits.main(["deployed-commits.py", "production"]) == 2
    assert deployed_commits.main(["deployed-commits.py", "production", "frontend"]) == 2
