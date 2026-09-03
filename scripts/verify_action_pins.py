#!/usr/bin/env python3
"""Verify that every SHA-pinned GitHub Action matches its version comment.

Actions are pinned by commit SHA so a hijacked tag cannot silently change what
runs in CI. The trailing `# vX.Y.Z` comment is the only human-readable part of
that pin -- it is what a reviewer actually reads. If the comment drifts from
the SHA, the audit trail is worse than useless: it asserts something false with
the authority of a pin.

That is not hypothetical here. `scorecard.yml` shipped from its very first
commit pinning upload-artifact's v7.0.1 SHA under a `# v5` comment, and a
dependabot bump rewrote three distinct checkout SHAs to one v7.0.1 SHA while
leaving `# v5` / `# v6` comments in place.

This script resolves each pinned SHA against the tag its comment names and
fails on any mismatch. Comments must be EXACT versions -- `# v5` is rejected
even when the SHA really is some v5.x, because "which v5" is precisely the
question a pin exists to answer.

Run locally with `gh auth token` available, or in CI with GITHUB_TOKEN.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WORKFLOW_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"
API = "https://api.github.com"

# A 5xx or a dropped connection from api.github.com says nothing about whether
# the pins are correct, but without a retry it fails the whole security-scan
# job and trains readers to wave red CI through. Seen 2026-08-17: a single
# HTTP 504 failed the gate on an unrelated commit.
HTTP_ATTEMPTS = 4
HTTP_BACKOFF_SECONDS = 2

# `uses: owner/repo[/sub/path]@<40-hex sha> # <version>`
PIN_RE = re.compile(
    r"uses:\s*(?P<owner>[\w.-]+)/(?P<repo>[\w.-]+)(?P<subpath>(?:/[\w.-]+)*)"
    r"@(?P<sha>[0-9a-f]{40})(?:\s*#\s*(?P<version>\S+))?"
)

# Docker-hosted or first-party actions that carry no resolvable upstream tag.
SKIP_REPOS: set[str] = set()


def _token() -> str | None:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=15)
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _api(path: str, token: str | None) -> dict | list | None:
    req = urllib.request.Request(f"{API}{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "portfolio-site-pin-audit")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for attempt in range(1, HTTP_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            # 404 and the rate-limit codes are ANSWERS, not transport failures:
            # retrying them changes nothing and hides the real cause.
            if exc.code == 404:
                return None
            if exc.code in (403, 429):
                print(
                    f"[-] GitHub API rate limit or forbidden on {path} "
                    f"({exc.code}). Provide GITHUB_TOKEN.",
                    file=sys.stderr,
                )
                sys.exit(2)
            if exc.code < 500 or attempt == HTTP_ATTEMPTS:
                raise
            transient = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            if attempt == HTTP_ATTEMPTS:
                raise
            transient = type(exc).__name__

        delay = HTTP_BACKOFF_SECONDS * (2 ** (attempt - 1))
        print(
            f"[!] {transient} on {path} (attempt {attempt}/{HTTP_ATTEMPTS}); retrying in {delay}s",
            file=sys.stderr,
        )
        time.sleep(delay)

    # Unreachable: the final attempt either returns or re-raises above.
    raise RuntimeError(f"exhausted retries for {path}")


def resolve_tag(repo: str, tag: str, token: str | None) -> tuple[str | None, str | None]:
    """Resolve a tag to (commit_sha, tag_object_sha).

    tag_object_sha is None for lightweight tags. The distinction matters:
    pinning the tag OBJECT of a moving major alias like `v4` looks like a
    SHA pin but is not one -- upstream re-points the alias on the next
    release, orphaning the object so no ref reaches it. It keeps resolving
    until it doesn't.
    """
    ref = _api(f"/repos/{repo}/git/ref/tags/{tag}", token)
    if not isinstance(ref, dict):
        return None, None
    obj = ref.get("object", {})
    if obj.get("type") == "tag":
        annotated = _api(f"/repos/{repo}/git/tags/{obj['sha']}", token)
        if isinstance(annotated, dict):
            return annotated.get("object", {}).get("sha"), obj["sha"]
        return None, obj["sha"]
    return obj.get("sha"), None


def main() -> int:
    token = _token()
    if not token:
        print("[!] No GITHUB_TOKEN and no gh auth token; unauthenticated API.")

    # (repo, sha, version) -> list of "file:line" so one lookup covers repeats.
    pins: dict[tuple[str, str, str | None], list[str]] = {}
    for path in sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            match = PIN_RE.search(line)
            if not match:
                continue
            repo = f"{match['owner']}/{match['repo']}"
            key = (repo, match["sha"], match["version"])
            pins.setdefault(key, []).append(f"{path.name}:{lineno}")

    if not pins:
        print("[-] No SHA-pinned actions found -- is the workflow directory right?")
        return 1

    failures: list[str] = []
    cache: dict[tuple[str, str], str | None] = {}

    for (repo, sha, version), locations in sorted(pins.items()):
        where = ", ".join(locations)
        if repo in SKIP_REPOS:
            continue
        if version is None:
            failures.append(f"{where}: {repo}@{sha[:12]} has no version comment")
            continue

        candidates = (version,) if version.startswith("v") else (version, f"v{version}")
        resolved, tag_object = None, None
        for candidate in candidates:
            if (repo, candidate) not in cache:
                cache[(repo, candidate)] = resolve_tag(repo, candidate, token)
            resolved, tag_object = cache[(repo, candidate)]
            if resolved:
                version = candidate
                break

        if resolved is None:
            failures.append(f"{where}: {repo} has no tag {version!r}")
        elif sha == tag_object:
            failures.append(
                f"{where}: {repo}@{sha[:12]} is the annotated TAG OBJECT of "
                f"{version}, not a commit. Pin the commit ({resolved[:12]}) -- "
                f"a tag object is orphaned when the tag moves."
            )
        elif resolved != sha:
            failures.append(
                f"{where}: {repo} comment says {version} (= {resolved[:12]}) but pin is {sha[:12]}"
            )
        else:
            print(f"[+] {repo}@{version} -> {sha[:12]}  ({where})")

    if failures:
        print(f"\n[-] {len(failures)} action pin(s) disagree with their comment:\n")
        for failure in failures:
            print(f"    {failure}")
        print(
            "\nFix the comment to the exact tag the SHA belongs to, or "
            "re-pin to the SHA of the version you meant."
        )
        return 1

    print(f"\n[+] All {len(pins)} pinned actions match their version comments.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
