"""The Python that scheduled workflows run inline, run here against fakes.

A step that runs `python3 - <<'PY'` is read from its workflow file and run in
this process with the network replaced, so each check is tested as CI runs it.
"""

import datetime
import json
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Self

import pytest
import yaml

WORKFLOWS = Path(__file__).resolve().parents[2] / ".github" / "workflows"
DAY = 86400
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _steps(workflow: str) -> list[dict[str, Any]]:
    jobs = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))["jobs"]
    return [step for job in jobs.values() for step in job["steps"]]


def _step(workflow: str, name: str) -> dict[str, Any]:
    [step] = [step for step in _steps(workflow) if step.get("name") == name]
    return step


def _heredoc(step: dict[str, Any]) -> str:
    """The Python of a step whose whole run is `python3 - [args] <<'PY'` ... `PY`."""
    head, _, rest = step["run"].partition("<<'PY'\n")
    body, end, tail = rest.partition("\nPY\n")
    assert head.startswith("python3 - "), step["name"]
    assert end, step["name"]
    assert not tail.strip(), step["name"]
    return body


def _run(step: dict[str, Any], argv: list[str], monkeypatch: pytest.MonkeyPatch) -> int:
    """Run a step's Python with `argv` and return its exit code."""
    monkeypatch.setattr(sys, "argv", ["-", *argv])
    try:
        exec(compile(_heredoc(step), step["name"], "exec"), {"__name__": "__main__"})
    except SystemExit as stop:
        assert isinstance(stop.code, int)
        return stop.code
    return 0


def _errors(out: str) -> list[str]:
    return [line for line in out.splitlines() if line.startswith("::error::")]


TLS = ("security-txt-expiry.yml", "Check the TLS certificates")
HOSTS = ["dashti.se", "www.dashti.se", "api.dashti.se"]
VERCEL = "check the Vercel project's Domains settings"
FLY = "check `fly certs show api.dashti.se`"


def _cert_time(seconds: float) -> str:
    """A date as getpeercert() gives it, e.g. 'Jan  8 23:45:38 2027 GMT'."""
    t = time.gmtime(seconds)
    clock = f"{t.tm_hour:02d}:{t.tm_min:02d}:{t.tm_sec:02d}"
    return f"{MONTHS[t.tm_mon - 1]} {t.tm_mday:2d} {clock} {t.tm_year} GMT"


def _cert(days_left: float, lifetime: float = 90) -> dict[str, str]:
    not_after = time.time() + days_left * DAY
    return {"notBefore": _cert_time(not_after - lifetime * DAY), "notAfter": _cert_time(not_after)}


class _Peer:
    """A connected socket; after the handshake it holds the peer's certificate."""

    def __init__(self, cert: dict[str, str] | None = None) -> None:
        self.cert = cert

    def __enter__(self) -> "_Peer":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def getpeercert(self) -> dict[str, str] | None:
        return self.cert


class _Network:
    """socket.create_connection and ssl.create_default_context, answered per host."""

    def __init__(self, answers: dict[str, dict[str, str] | Exception]) -> None:
        self.answers = answers
        self.calls: list[tuple[str, object]] = []

    def create_connection(self, address: tuple[str, int], timeout: float) -> _Peer:
        self.calls.append(("connect", (address, timeout)))
        return _Peer()

    def create_default_context(self, *args: object, **kwargs: object) -> "_Network":
        self.calls.append(("context", (args, kwargs)))
        return self

    def wrap_socket(self, sock: _Peer, server_hostname: str) -> _Peer:
        self.calls.append(("handshake", server_hostname))
        answer = self.answers[server_hostname]
        if isinstance(answer, Exception):
            raise answer
        return _Peer(answer)


def _check_tls(
    monkeypatch: pytest.MonkeyPatch, answers: dict[str, dict[str, str] | Exception]
) -> tuple[int, _Network]:
    network = _Network(answers)
    monkeypatch.setattr(socket, "create_connection", network.create_connection)
    monkeypatch.setattr(ssl, "create_default_context", network.create_default_context)
    return _run(_step(*TLS), [], monkeypatch), network


def test_the_tls_check_runs_even_when_the_security_txt_check_failed() -> None:
    names = [step.get("name") for step in _steps(TLS[0])]
    assert names.index(TLS[1]) > names.index("Check both live copies")
    assert _step(*TLS)["if"] == "${{ !cancelled() }}"


def test_each_host_gets_a_verified_handshake_under_its_own_name(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, network = _check_tls(monkeypatch, {host: _cert(60) for host in HOSTS})
    out = capsys.readouterr().out
    assert code == 0
    assert _errors(out) == []
    # One default context, which verifies the chain and the host name.
    assert network.calls[0] == ("context", ((), {}))
    assert [call for call in network.calls if call[0] != "context"] == [
        call for host in HOSTS for call in (("connect", ((host, 443), 15)), ("handshake", host))
    ]
    for host in HOSTS:
        assert f"\n{host}: valid until " in f"\n{out}"


@pytest.mark.parametrize(
    ("days_left", "lifetime", "fails"),
    [(23, 90, False), (22, 90, True), (17, 64, False), (15, 64, True)],
)
def test_a_certificate_fails_with_under_a_quarter_of_its_lifetime_left(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    days_left: float,
    lifetime: float,
    fails: bool,
) -> None:
    answers: dict[str, dict[str, str] | Exception] = {host: _cert(60) for host in HOSTS}
    answers["api.dashti.se"] = _cert(days_left, lifetime)
    code, _ = _check_tls(monkeypatch, answers)
    errors = _errors(capsys.readouterr().out)
    assert code == int(fails)
    if fails:
        [error] = errors
        assert error.startswith("::error::api.dashti.se: ")
        assert f"under a quarter of its {lifetime}-day lifetime" in error
        assert error.endswith(FLY)
    else:
        assert errors == []


@pytest.mark.parametrize(
    "failure",
    [
        ssl.SSLCertVerificationError(1, "certificate has expired"),
        TimeoutError("timed out"),
        OSError("Name or service not known"),
    ],
)
def test_a_failed_connection_is_reported_and_the_other_hosts_still_checked(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], failure: Exception
) -> None:
    answers: dict[str, dict[str, str] | Exception] = {host: _cert(60) for host in HOSTS}
    answers["www.dashti.se"] = failure
    code, network = _check_tls(monkeypatch, answers)
    out = capsys.readouterr().out
    assert code == 1
    assert _errors(out) == [f"::error::www.dashti.se: {failure} - {VERCEL}"]
    assert [call[1] for call in network.calls if call[0] == "handshake"] == HOSTS
    assert "\ndashti.se: valid until " in f"\n{out}"
    assert "\napi.dashti.se: valid until " in out


FILTER = ("image-scan.yml", "Keep the High and Critical matches")
GATE = ("image-scan.yml", "Fail while a High or Critical match has a fix")


def _sarif(*levels: str) -> dict[str, Any]:
    """A grype-shaped SARIF report with one result per level, in order."""
    results = [
        {"ruleId": f"CVE-2026-{n}-pkg", "level": level, "message": {"text": f"match {n}"}}
        for n, level in enumerate(levels, 1)
    ]
    rules = [{"id": result["ruleId"]} for result in results]
    return {
        "version": "2.1.0",
        "runs": [{"tool": {"driver": {"name": "grype", "rules": rules}}, "results": results}],
    }


def _filter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, report: dict[str, Any]
) -> dict[str, Any]:
    source, target = tmp_path / "grype.sarif", tmp_path / "high.sarif"
    source.write_text(json.dumps(report), encoding="utf-8")
    assert _run(_step(*FILTER), [str(source), str(target)], monkeypatch) == 0
    kept: dict[str, Any] = json.loads(target.read_text(encoding="utf-8"))
    return kept


def test_only_high_and_critical_matches_go_to_code_scanning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    report = _sarif("error", "warning", "note", "error")
    kept = _filter(tmp_path, monkeypatch, report)
    [run] = kept["runs"]
    # grype's SARIF level is "error" for High and Critical, "warning" for Medium.
    assert [result["ruleId"] for result in run["results"]] == ["CVE-2026-1-pkg", "CVE-2026-4-pkg"]
    assert run["tool"] == report["runs"][0]["tool"]
    assert kept["version"] == report["version"]


def test_the_gate_fails_on_each_kept_match_and_passes_without_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    high = tmp_path / "high.sarif"
    high.write_text(json.dumps(_sarif("error", "error")), encoding="utf-8")
    assert _run(_step(*GATE), [str(high)], monkeypatch) == 1
    errors = _errors(capsys.readouterr().out)
    assert [error.split(" - ")[0] for error in errors] == [
        "::error::CVE-2026-1-pkg: match 1",
        "::error::CVE-2026-2-pkg: match 2",
    ]
    assert all("FROM lines of backend/Dockerfile" in error for error in errors)

    high.write_text(json.dumps(_sarif()), encoding="utf-8")
    assert _run(_step(*GATE), [str(high)], monkeypatch) == 0
    assert _errors(capsys.readouterr().out) == []


def test_medium_and_low_matches_alone_leave_the_gate_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _filter(tmp_path, monkeypatch, _sarif("warning", "note"))
    assert _run(_step(*GATE), [str(tmp_path / "high.sarif")], monkeypatch) == 0
    assert _errors(capsys.readouterr().out) == []


COMMIT = ("security-txt-expiry.yml", "Check that production serves main's frontend")
SHORT = "b5f4fe6"
FULL = SHORT + "0" * 33
HEAD = "c" * 40
REBAKE = "run rebake-frontend.yml, which deploys main's frontend"


def _page(*commits: str) -> bytes:
    """The home page with one footer build stamp per commit, as the build renders it."""
    stamps = "".join(
        '<p class="build-stamp"> Build <a href="https://github.com/Dashtid/portfolio-site/'
        f'commit/{commit}" target="_blank" rel="noopener noreferrer">{commit}</a></p>'
        for commit in commits
    )
    return f"<html><body><footer>{stamps}</footer></body></html>".encode()


class _Response:
    def __init__(self, body: bytes) -> None:
        self.body = body

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def read(self) -> bytes:
        return self.body


class _Site:
    """urllib.request.build_opener, answering every request with one page or error."""

    def __init__(self, answer: bytes | Exception) -> None:
        self.answer = answer
        self.handlers: tuple[Any, ...] = ()
        self.requests: list[tuple[str, float]] = []

    def build_opener(self, *handlers: Any) -> "_Site":
        self.handlers = handlers
        return self

    def open(self, request: urllib.request.Request, timeout: float) -> _Response:
        self.requests.append((request.full_url, timeout))
        if isinstance(self.answer, Exception):
            raise self.answer
        return _Response(self.answer)


class _Git:
    """subprocess.run for the step's git commands, answered from its settings."""

    def __init__(self, resolves: bool = True, diff: int = 0) -> None:
        self.resolves, self.diff = resolves, diff
        self.calls: list[list[str]] = []

    def run(self, args: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str]:
        assert args[0] == "git"
        command = list(args[1:])
        self.calls.append(command)
        if command[:3] == ["rev-parse", "--verify", "--quiet"]:
            found = f"{FULL}\n" if self.resolves else ""
            return subprocess.CompletedProcess(args, 0 if self.resolves else 1, found, "")
        if command == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(args, 0, f"{HEAD}\n", "")
        assert command[0] == "diff", command
        stderr = "fatal: bad object" if self.diff > 1 else ""
        return subprocess.CompletedProcess(args, self.diff, "", stderr)


def _check_commit(
    monkeypatch: pytest.MonkeyPatch, answer: bytes | Exception, git: _Git
) -> tuple[int, _Site]:
    site = _Site(answer)
    monkeypatch.setattr(urllib.request, "build_opener", site.build_opener)
    monkeypatch.setattr(subprocess, "run", git.run)
    return _run(_step(*COMMIT), [], monkeypatch), site


def test_the_commit_check_runs_weekly_on_full_history_with_read_access() -> None:
    workflow = yaml.safe_load((WORKFLOWS / COMMIT[0]).read_text(encoding="utf-8"))
    assert "schedule" in workflow.get("on", workflow.get(True))
    job = workflow["jobs"]["frontend-commit"]
    assert job["permissions"] == {"contents": "read"}
    [checkout] = [step for step in job["steps"] if "uses" in step]
    assert checkout["uses"].startswith("actions/checkout@")
    assert checkout["with"] == {"fetch-depth": 0, "persist-credentials": False}
    assert "secrets." not in yaml.safe_dump(job)


def test_the_commit_check_passes_when_main_has_the_served_frontend(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    git = _Git()
    code, site = _check_commit(monkeypatch, _page(SHORT), git)
    out = capsys.readouterr().out
    assert (code, _errors(out)) == (0, [])
    assert site.requests == [("https://dashti.se/", 15)]
    # A redirect is reported as an error instead of being followed.
    [handler] = site.handlers
    assert handler().redirect_request(None, None, 308, "Moved", {}, "https://x.test/") is None
    assert git.calls == [
        ["rev-parse", "--verify", "--quiet", f"{SHORT}^{{commit}}"],
        ["rev-parse", "HEAD"],
        ["diff", "--quiet", FULL, HEAD, "--", "frontend"],
    ]
    assert f"serves {SHORT}; frontend/ is the same on main at ccccccc" in out


@pytest.mark.parametrize(
    ("answer", "git", "problem"),
    [
        (_page(SHORT), _Git(diff=1), f"serves {SHORT}, and frontend/ differs from it on main"),
        (_page(SHORT), _Git(resolves=False), "a commit this repository's history does not resolve"),
        (_page(SHORT), _Git(diff=128), f"git diff {SHORT} ccccccc failed: fatal: bad object"),
        (_page(), _Git(), "expected one footer build stamp, found []"),
        (_page(SHORT, "1234567"), _Git(), "expected one footer build stamp, found ['1234567',"),
        (urllib.error.URLError("timed out"), _Git(), "https://dashti.se/: <urlopen error"),
    ],
)
def test_the_commit_check_fails_when_main_has_moved_on_or_the_stamp_is_unusable(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    answer: bytes | Exception,
    git: _Git,
    problem: str,
) -> None:
    code, _ = _check_commit(monkeypatch, answer, git)
    [error] = _errors(capsys.readouterr().out)
    assert code == 1
    assert problem in error
    assert error.endswith(f" - {REBAKE}")


DATE = ("security-txt-expiry.yml", "Warn when the colophon's verification date passes 90 days")
COLOPHON = WORKFLOWS.parents[1] / "frontend" / "src" / "views" / "ColophonView.vue"
MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)
TODAY = datetime.date(2026, 11, 30)
RECHECK = "re-check the page's claims against the live site and the repository"


class _Clock(datetime.datetime):
    """datetime.datetime with now() at 06:00 UTC on TODAY, the schedule's hour."""

    @classmethod
    def now(cls, tz: datetime.tzinfo | None = None) -> Self:
        return cls(TODAY.year, TODAY.month, TODAY.day, 6, tzinfo=datetime.UTC)


def _days_before_today(days: int) -> str:
    """A date `days` before TODAY, written the way the colophon writes VERIFIED_ON."""
    day = TODAY - datetime.timedelta(days=days)
    return f"{day.day} {MONTH_NAMES[day.month - 1]} {day.year}"


def _colophon(tmp_path: Path, *literals: str) -> Path:
    """A ColophonView.vue with one VERIFIED_ON line per literal."""
    page = tmp_path / "ColophonView.vue"
    lines = "".join(f"const VERIFIED_ON = '{literal}'\n" for literal in literals)
    page.write_text(f'<script setup lang="ts">\n{lines}</script>\n', encoding="utf-8")
    return page


def _check_date(monkeypatch: pytest.MonkeyPatch, page: Path) -> int:
    monkeypatch.setattr(datetime, "datetime", _Clock)
    return _run(_step(*DATE), [str(page)], monkeypatch)


def test_the_date_check_reads_the_colophon_whatever_the_commit_check_found() -> None:
    workflow = yaml.safe_load((WORKFLOWS / DATE[0]).read_text(encoding="utf-8"))
    names = [step.get("name") for step in workflow["jobs"]["frontend-commit"]["steps"]]
    assert names.index(DATE[1]) > names.index(COMMIT[1])
    step = _step(*DATE)
    assert step["if"] == "${{ !cancelled() }}"
    # The job's checkout is the step's working directory.
    head = step["run"].partition(" <<'PY'\n")[0]
    assert head == "python3 - frontend/src/views/ColophonView.vue"
    assert COLOPHON.is_file()


def test_the_date_check_reads_the_literal_the_page_carries(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Under the fixed clock, so the page's date growing old fails the weekly
    # run and ColophonView.spec, not this test.
    code = _check_date(monkeypatch, COLOPHON)
    out = capsys.readouterr().out
    assert (code, _errors(out)) == (0, [])
    assert f"{COLOPHON}: VERIFIED_ON 20" in out


@pytest.mark.parametrize(("days", "fails"), [(0, False), (90, False), (91, True), (400, True)])
def test_the_date_check_fails_once_the_date_is_more_than_90_days_old(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    days: int,
    fails: bool,
) -> None:
    page = _colophon(tmp_path, _days_before_today(days))
    code = _check_date(monkeypatch, page)
    out = capsys.readouterr().out
    verified = TODAY - datetime.timedelta(days=days)
    assert f"{page}: VERIFIED_ON {verified.isoformat()}, {days} days ago" in out
    errors = _errors(out)
    assert code == int(fails)
    if fails:
        [error] = errors
        assert error.startswith(f"::error::{page}: VERIFIED_ON is {days} days old")
        assert f"more than 90 - {RECHECK}" in error
    else:
        assert errors == []


@pytest.mark.parametrize(
    ("literals", "problem"),
    [
        ((), "expected one VERIFIED_ON literal, found 0"),
        (("1 May 2026", "2 May 2026"), "expected one VERIFIED_ON literal, found 2"),
        (("4 Sept 2026",), "VERIFIED_ON '4 Sept 2026' is not 'D Month YYYY'"),
        (("4 september 2026",), "VERIFIED_ON '4 september 2026' is not 'D Month YYYY'"),
        (("2026-11-30",), "VERIFIED_ON '2026-11-30' is not 'D Month YYYY'"),
        (("31 April 2026",), "VERIFIED_ON '31 April 2026' names no such day"),
    ],
)
def test_the_date_check_fails_on_a_literal_it_cannot_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    literals: tuple[str, ...],
    problem: str,
) -> None:
    page = _colophon(tmp_path, *literals)
    code = _check_date(monkeypatch, page)
    out = capsys.readouterr().out
    assert code == 1
    assert _errors(out) == [f"::error::{page}: {problem}"]


def test_the_date_check_fails_when_the_page_is_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "ColophonView.vue"
    code = _check_date(monkeypatch, missing)
    [error] = _errors(capsys.readouterr().out)
    assert code == 1
    assert error.startswith(f"::error::{missing}: ")
