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

One action needs a second pin. trufflesecurity/trufflehog's script runs
`docker run ghcr.io/trufflesecurity/trufflehog:<version input>`, and that input
defaults to `latest`: the SHA pin fixed the wrapper while the scanner was
whatever `latest` meant that day. Dependabot moves the SHA and its comment but
never reads a `with:` input, so the step's `version:` must be
`<the comment's version>@sha256:<digest>`, and the digest must be what ghcr.io
serves for that tag. Docker runs the digest when a reference carries both, so a
digest left behind by a version bump would run the old scanner under the new
name.

Run locally with `gh auth token` available, or in CI with GITHUB_TOKEN.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

WORKFLOW_DIR = Path(__file__).resolve().parent.parent / ".github" / "workflows"
API = "https://api.github.com"
GHCR = "https://ghcr.io"

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

# Actions whose `version:` input picks a ghcr.io image (see the docstring):
# action repo -> image repository on ghcr.io.
IMAGE_VERSION_ACTIONS = {"trufflesecurity/trufflehog": "trufflesecurity/trufflehog"}

# `<tag>@sha256:<digest>`, optionally quoted, optionally followed by a comment.
IMAGE_PIN_RE = re.compile(
    r"""^(?P<q>['"]?)(?P<tag>\w[\w.-]*)(?:@(?P<digest>sha256:[0-9a-f]{64}))?(?P=q)(?:\s+#.*)?$"""
)

# Accept the multi-arch index types: the tag points at an index, and without
# them a registry may answer with a different manifest, whose sha256 is not the
# tag's digest.
MANIFEST_ACCEPT = (
    "application/vnd.oci.image.index.v1+json, "
    "application/vnd.docker.distribution.manifest.list.v2+json, "
    "application/vnd.oci.image.manifest.v1+json, "
    "application/vnd.docker.distribution.manifest.v2+json"
)

T = TypeVar("T")


def _token() -> str | None:
    for var in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(var):
            return os.environ[var]
    try:
        out = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=15, check=False
        )
        if out.returncode == 0 and out.stdout.strip():
            return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _fetch(url: str, headers: dict[str, str], parse: Callable[[bytes], T]) -> T | None:
    """GET `url` and return parse(body), or None on 404, retrying transient failures."""
    req = urllib.request.Request(url, headers={"User-Agent": "portfolio-site-pin-audit", **headers})
    for attempt in range(1, HTTP_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return parse(resp.read())
        except urllib.error.HTTPError as exc:
            # 404 and the rate-limit codes are ANSWERS, not transport failures:
            # retrying them changes nothing and hides the real cause.
            if exc.code == 404:
                return None
            if exc.code in (403, 429):
                hint = " Provide GITHUB_TOKEN." if url.startswith(API) else ""
                print(
                    f"[-] Rate limit or forbidden on {url} ({exc.code}).{hint}",
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
            f"[!] {transient} on {url} (attempt {attempt}/{HTTP_ATTEMPTS}); retrying in {delay}s",
            file=sys.stderr,
        )
        time.sleep(delay)

    # Unreachable: the final attempt either returns or re-raises above.
    raise RuntimeError(f"exhausted retries for {url}")


def _api(path: str, token: str | None) -> dict | list | None:
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return _fetch(f"{API}{path}", headers, json.loads)


def ghcr_digest(image: str, tag: str) -> str | None:
    """The digest ghcr.io serves for image:tag, or None when there is no such tag.

    A manifest's digest IS the sha256 of its bytes, so it is computed from the
    body that came back rather than taken from a response header.
    """
    grant = _fetch(f"{GHCR}/token?scope=repository:{image}:pull", {}, json.loads)
    headers = {"Accept": MANIFEST_ACCEPT}
    if isinstance(grant, dict) and grant.get("token"):
        headers["Authorization"] = f"Bearer {grant['token']}"
    return _fetch(
        f"{GHCR}/v2/{image}/manifests/{tag}",
        headers,
        lambda body: f"sha256:{hashlib.sha256(body).hexdigest()}",
    )


def step_input(lines: list[str], uses_index: int, name: str) -> tuple[int, str] | None:
    """(line number, raw value) of input `name` in the `with:` block of the step
    whose `uses:` is lines[uses_index], or None when the step has no such input.

    Line-based like the pin scan, so CI needs no YAML library: the step's keys
    share the column of `uses:`, the step opens with the `- ` two columns left
    of them, and the first shallower line after that closes it.
    """
    key_col = lines[uses_index].index("uses:")
    dash = " " * (key_col - 2) + "- "
    start = uses_index
    while start > 0 and not lines[start].startswith(dash):
        start -= 1

    in_with, input_col = False, 0
    for index in range(start, len(lines)):
        text = lines[index].strip()
        col = len(lines[index]) - len(lines[index].lstrip())
        if index == start:
            text, col = text[2:].lstrip(), key_col
        if not text or text.startswith("#"):
            continue
        if col < key_col:
            break
        key, sep, value = text.partition(":")
        if col == key_col:
            in_with, input_col = (key == "with" and sep == ":"), 0
        elif in_with:
            input_col = input_col or col
            if col == input_col and sep and key == name:
                return index + 1, value.strip()
    return None


def audit_image_pin(
    repo: str,
    where: str,
    comment: str | None,
    version_input: tuple[str, int, str] | None,
) -> str | None:
    """Failure message for the image pin of an IMAGE_VERSION_ACTIONS step, or None.

    `where` is the step's `uses:` line, `comment` its `# vX.Y.Z`, and
    `version_input` the (file, line, raw value) of its `version:` input.
    """
    image = IMAGE_VERSION_ACTIONS[repo]
    want = (comment or "").removeprefix("v") or "<X.Y.Z>"
    fix = (
        f"set `version: {want}@sha256:<digest>` from "
        f"`docker buildx imagetools inspect ghcr.io/{image}:{want}`"
    )
    if version_input is None:
        return (
            f"{where}: {repo} has no `version:` input, so it runs "
            f"ghcr.io/{image}:latest whatever the SHA pin says -- {fix}"
        )

    file_name, lineno, raw = version_input
    at = f"{file_name}:{lineno}"
    pin = IMAGE_PIN_RE.match(raw)
    if pin is None or pin["digest"] is None:
        return f"{at}: {repo} version {raw!r} is not <tag>@sha256:<digest> -- {fix}"
    if pin["tag"] != want:
        return (
            f"{at}: {repo} image is {pin['tag']} but the action pin says "
            f"{comment or 'nothing'} ({where}); the image must move with the action tag -- {fix}"
        )

    served = ghcr_digest(image, pin["tag"])
    if served is None:
        return f"{at}: ghcr.io/{image} has no tag {pin['tag']!r}"
    if served != pin["digest"]:
        return (
            f"{at}: ghcr.io/{image}:{pin['tag']} is {served[:19]}, but the pin is "
            f"{pin['digest'][:19]} -- Docker runs the pinned digest, not the tag"
        )

    print(f"[+] {repo} image {pin['tag']}@{served[:19]} = ghcr.io/{image}:{pin['tag']}  ({at})")
    return None


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
    # (repo, "file:line" of the uses:, its version comment, (file, line, value)
    # of the step's version input or None) for IMAGE_VERSION_ACTIONS steps.
    image_pins: list[tuple[str, str, str | None, tuple[str, int, str] | None]] = []
    for path in sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        for lineno, line in enumerate(lines, 1):
            match = PIN_RE.search(line)
            if not match:
                continue
            repo = f"{match['owner']}/{match['repo']}"
            key = (repo, match["sha"], match["version"])
            pins.setdefault(key, []).append(f"{path.name}:{lineno}")
            if repo in IMAGE_VERSION_ACTIONS:
                found = step_input(lines, lineno - 1, "version")
                version_input = (path.name, *found) if found else None
                image_pins.append((repo, f"{path.name}:{lineno}", match["version"], version_input))

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

    for repo, where, comment, version_input in image_pins:
        failure = audit_image_pin(repo, where, comment, version_input)
        if failure:
            failures.append(failure)

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
