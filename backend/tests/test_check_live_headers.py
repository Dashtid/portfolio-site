"""scripts/check-live-headers.py holds production's headers to frontend/vercel.json.

The deploy jobs run it after every frontend deploy. These tests feed it
recorded answers, and a local HTTP server for the request itself.
"""

import importlib.util
import json
import threading
import urllib.error
from collections.abc import Callable, Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "check_live_headers", ROOT / "scripts" / "check-live-headers.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


check_live_headers = _load_script()

CSP = "default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'"
RULE = [
    ("X-Frame-Options", "DENY"),
    ("Strict-Transport-Security", "max-age=31536000; includeSubDomains; preload"),
    ("Content-Security-Policy", CSP),
]
URLS = ["https://site.test/", "https://site.test/page"]
# Headers Vercel adds itself; the check ignores what vercel.json does not set.
VENDOR = [("server", "Vercel"), ("x-vercel-id", "arn1::abc"), ("cache-control", "no-cache")]

Answer = tuple[int, list[tuple[str, str]]] | BaseException


def _vercel_json(tmp_path: Path, rule: list[tuple[str, str]]) -> Path:
    path = tmp_path / "vercel.json"
    config = {
        "headers": [
            {"source": "/assets/(.*)", "headers": [{"key": "Cache-Control", "value": "immutable"}]},
            {"source": "/(.*)", "headers": [{"key": k, "value": v} for k, v in rule]},
        ]
    }
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _fetch(*answers: Answer) -> tuple[Callable[[str], Any], list[str]]:
    """A fetch that gives `answers` in turn (raising the exceptions), and the URLs asked."""
    pending = list(answers)
    asked: list[str] = []

    def fetch(url: str) -> Any:
        asked.append(url)
        answer = pending.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    return fetch, asked


def _run(
    tmp_path: Path, *answers: Answer, urls: list[str] | None = None
) -> tuple[int, list[float]]:
    fetch, _ = _fetch(*answers)
    sleeps: list[float] = []
    code = check_live_headers.check(
        _vercel_json(tmp_path, RULE), URLS if urls is None else urls, fetch, sleeps.append
    )
    return code, sleeps


def test_matching_headers_pass_whatever_the_name_case(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    lowercase = [(name.lower(), value) for name, value in RULE]
    code, sleeps = _run(tmp_path, (200, RULE + VENDOR), (200, lowercase + VENDOR))
    assert (code, sleeps) == (0, [])
    assert capsys.readouterr().out.count("[+]") == 2


def _with(name: str, value: str | None) -> list[tuple[str, str]]:
    """RULE with one header's value replaced, or the header dropped for None."""
    headers = [(k, v) for k, v in RULE if k != name]
    return headers if value is None else [*headers, (name, value)]


@pytest.mark.parametrize(
    ("served", "problem"),
    [
        # Vercel's own default HSTS, without includeSubDomains and preload.
        (_with("Strict-Transport-Security", "max-age=63072000"), "Strict-Transport-Security is"),
        (
            _with(
                "Content-Security-Policy",
                CSP.replace("style-src 'self'", "style-src 'self' 'unsafe-inline'"),
            ),
            "Content-Security-Policy is",
        ),
        (
            _with("Content-Security-Policy", CSP.replace("; frame-ancestors 'none'", "")),
            "Content-Security-Policy is",
        ),
        (_with("X-Frame-Options", None), "X-Frame-Options is missing"),
        ([*RULE, ("x-frame-options", "SAMEORIGIN")], "X-Frame-Options is sent 2 times"),
    ],
)
def test_a_weakened_missing_or_repeated_header_fails(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], served: list[tuple[str, str]], problem: str
) -> None:
    code, _ = _run(tmp_path, (200, served), urls=URLS[:1])
    assert code == 1
    assert f"[-] {URLS[0]}: {problem}" in capsys.readouterr().out


def test_unsafe_inline_in_script_src_fails_even_when_vercel_json_has_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    weak = CSP.replace("script-src 'self'", "script-src 'self' 'UNSAFE-INLINE'")
    rule = _with("Content-Security-Policy", weak)
    fetch, _ = _fetch((200, rule))
    code = check_live_headers.check(_vercel_json(tmp_path, rule), URLS[:1], fetch, lambda _: None)
    assert code == 1
    assert "script-src allows 'unsafe-inline'" in capsys.readouterr().out


def test_script_src_attr_is_not_script_src() -> None:
    policy = "script-src 'self'; script-src-attr 'unsafe-inline'"
    assert check_live_headers.compare([], [("Content-Security-Policy", policy)]) == []


@pytest.mark.parametrize("status", [308, 404])
def test_only_a_200_counts(tmp_path: Path, status: int) -> None:
    # A redirect carries Vercel's default headers, not vercel.json's.
    code, sleeps = _run(tmp_path, (status, RULE), urls=URLS[:1])
    assert (code, sleeps) == (1, [])


def test_network_errors_and_server_errors_are_retried(tmp_path: Path) -> None:
    code, sleeps = _run(
        tmp_path,
        urllib.error.URLError("connection reset"),
        (503, []),
        (200, RULE),
        urls=URLS[:1],
    )
    assert (code, sleeps) == (0, [10, 10])


def test_three_failed_attempts_fail_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, sleeps = _run(tmp_path, TimeoutError(), TimeoutError(), TimeoutError(), urls=URLS[:1])
    assert (code, sleeps) == (1, [10, 10])
    assert "no answer after 3 attempts (TimeoutError" in capsys.readouterr().out
    code, _ = _run(tmp_path, (502, []), (502, []), (502, []), urls=URLS[:1])
    assert code == 1


def test_vercel_json_switches_off_each_feature_the_colophon_names() -> None:
    # The live check holds production to vercel.json, so a weaker value in
    # vercel.json itself would pass it; the colophon cites this one.
    colophon = (ROOT / "frontend" / "src" / "views" / "ColophonView.vue").read_text(
        encoding="utf-8"
    )
    assert (
        "camera, microphone, geolocation, payment, USB and the motion sensors all switched off"
        " for the page and anything it embeds"
    ) in colophon
    served = dict(check_live_headers.expected_headers(ROOT / "frontend" / "vercel.json"))
    # An empty allowlist, (), turns a feature off in every frame.
    assert served["Permissions-Policy"] == (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), "
        "magnetometer=(), gyroscope=(), accelerometer=()"
    )


def test_expected_headers_come_from_the_catch_all_rule(tmp_path: Path) -> None:
    assert check_live_headers.expected_headers(_vercel_json(tmp_path, RULE)) == RULE
    real = dict(check_live_headers.expected_headers(ROOT / "frontend" / "vercel.json"))
    assert {"Content-Security-Policy", "Strict-Transport-Security"} <= real.keys()
    empty = tmp_path / "empty.json"
    empty.write_text('{"headers": []}', encoding="utf-8")
    with pytest.raises(SystemExit):
        check_live_headers.expected_headers(empty)


class _Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        if self.path == "/moved":
            self.send_response(308)
            self.send_header("Location", "/page")
        else:
            self.send_response(200)
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("X-Frame-Options", "SAMEORIGIN")
        self.end_headers()

    def log_message(self, format: str, *args: Any) -> None:
        """Keep the request log out of the test output."""


@pytest.fixture
def server() -> Iterator[str]:
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}"
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_fetch_sends_head_keeps_repeats_and_follows_no_redirect(server: str) -> None:
    # The handler answers HEAD only, so a 200 also proves the method.
    status, headers = check_live_headers.fetch_headers(f"{server}/page")
    assert status == 200
    assert [value for name, value in headers if name == "X-Frame-Options"] == ["DENY", "SAMEORIGIN"]
    status, headers = check_live_headers.fetch_headers(f"{server}/moved")
    assert status == 308
    assert ("Location", "/page") in headers


def test_usage_without_urls() -> None:
    assert check_live_headers.main(["check-live-headers.py", "frontend/vercel.json"]) == 2
