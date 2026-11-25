"""Compare the headers production serves with the ones frontend/vercel.json sets.

vercel.json sets the site's security headers on its "/(.*)" rule, and unit
tests pin the file's values. Only production shows what Vercel actually
serves: a platform or project setting, or a deploy that did not take effect,
can serve other headers while every test passes. The frontend deploy in
ci-cd.yml and rebake-frontend.yml run this check after `vercel deploy --prod`.
It fails unless every URL answers 200 and carries each header of that rule
exactly once, with exactly the configured value, and unless the served CSP's
script-src is free of 'unsafe-inline'.

Point it at pages that answer 200. A redirect (www.dashti.se, a trailing
slash) carries Vercel's own default headers instead of the rule's, so a
redirecting URL fails every deploy.

Standard library only, so the deploy jobs run it with the runner's Python.

Usage, from the repository root:
    python3 scripts/check-live-headers.py frontend/vercel.json URL [URL ...]
"""

from __future__ import annotations

import http.client
import json
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Sequence
from pathlib import Path

RULE_SOURCE = "/(.*)"
ATTEMPTS = 3
RETRY_SECONDS = 10
TIMEOUT_SECONDS = 15

Headers = list[tuple[str, str]]
Fetch = Callable[[str], tuple[int, Headers]]


def expected_headers(vercel_json: Path) -> Headers:
    """The (name, value) pairs of vercel.json's "/(.*)" headers rule."""
    config = json.loads(vercel_json.read_text(encoding="utf-8"))
    for rule in config.get("headers", []):
        if rule.get("source") == RULE_SOURCE and rule.get("headers"):
            return [(entry["key"], entry["value"]) for entry in rule["headers"]]
    raise SystemExit(f"[-] {vercel_json} has no headers for the source {RULE_SOURCE!r}")


def _script_src_allows_inline(policy: str) -> bool:
    for directive in policy.split(";"):
        tokens = directive.lower().split()
        if tokens[:1] == ["script-src"] and "'unsafe-inline'" in tokens[1:]:
            return True
    return False


def compare(expected: Headers, served: Headers) -> list[str]:
    """What is wrong with one response's headers; an empty list when they match.

    Names compare case-insensitively and values exactly, after trimming the
    whitespace HTTP allows around a value. Headers vercel.json does not set
    are not compared: Vercel adds its own (server, cache, request id).
    """
    problems = []
    for name, value in expected:
        values = [v.strip() for key, v in served if key.lower() == name.lower()]
        if not values:
            problems.append(f"{name} is missing")
        elif len(values) > 1:
            problems.append(f"{name} is sent {len(values)} times")
        elif values[0] != value:
            problems.append(f"{name} is {values[0]!r}, but vercel.json sets {value!r}")
    for key, policy in served:
        if key.lower() == "content-security-policy" and _script_src_allows_inline(policy):
            problems.append("the served CSP's script-src allows 'unsafe-inline'")
    return problems


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args: object, **kwargs: object) -> None:
        return None  # a 3xx then comes back as an HTTPError, not followed


def fetch_headers(url: str) -> tuple[int, Headers]:
    """Status and every header, repeats included, of a HEAD request to `url`."""
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(
        url, method="HEAD", headers={"User-Agent": "check-live-headers"}
    )
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            return response.status, list(response.headers.items())
    except urllib.error.HTTPError as error:
        return error.code, list(error.headers.items())


def _fetch_with_retries(
    url: str, fetch: Fetch, sleep: Callable[[float], None]
) -> tuple[int, Headers] | str:
    """The first answer below 500, else the last answer; a message if none came."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            status, served = fetch(url)
        except (OSError, http.client.HTTPException) as exc:
            if attempt == ATTEMPTS:
                return f"{type(exc).__name__}: {exc}"
            reason = type(exc).__name__
        else:
            if status < 500 or attempt == ATTEMPTS:
                return status, served
            reason = f"HTTP {status}"
        print(
            f"[!] {url}: {reason} (attempt {attempt} of {ATTEMPTS}); retrying in {RETRY_SECONDS}s"
        )
        sleep(RETRY_SECONDS)
    raise AssertionError("unreachable: the last attempt returns")


def check(
    vercel_json: Path,
    urls: Sequence[str],
    fetch: Fetch = fetch_headers,
    sleep: Callable[[float], None] = time.sleep,
) -> int:
    """Check every URL against vercel.json; 0 when all match, 1 otherwise."""
    expected = expected_headers(vercel_json)
    failed = False
    for url in urls:
        result = _fetch_with_retries(url, fetch, sleep)
        if isinstance(result, str):
            print(f"[-] {url}: no answer after {ATTEMPTS} attempts ({result})")
            failed = True
            continue
        status, served = result
        if status != 200:
            print(f"[-] {url}: HTTP {status}; only a 200 carries the headers vercel.json sets")
            failed = True
            continue
        problems = compare(expected, served)
        for problem in problems:
            print(f"[-] {url}: {problem}")
        if problems:
            failed = True
        else:
            print(f"[+] {url}: all {len(expected)} headers match vercel.json")
    return 1 if failed else 0


def main(argv: Sequence[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    return check(Path(argv[1]), argv[2:])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
