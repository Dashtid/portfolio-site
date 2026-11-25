"""The Python that scheduled workflows run inline, run here against fakes.

A step that runs `python3 - <<'PY'` is read from its workflow file and run in
this process with the network replaced, so each check is tested as CI runs it.
"""

import socket
import ssl
import sys
import time
from pathlib import Path
from typing import Any

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
    with pytest.raises(SystemExit) as stop:
        exec(compile(_heredoc(step), step["name"], "exec"), {"__name__": "__main__"})
    code = stop.value.code
    assert isinstance(code, int)
    return code


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
