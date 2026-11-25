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

A Docker action has the same gap when its own metadata names the image by tag:
ossf/scorecard-action's action.yaml runs
`docker://ghcr.io/ossf/scorecard-action:<tag>`, and the SHA pin fixes that
line, not what the tag points to. Such a `uses:` carries
`# image: ghcr.io/<repository>:<tag>@sha256:<digest>` among the comment lines
right under it. The tag must be the one the metadata names at the pinned SHA
and the digest the one ghcr.io serves for it, so a tag pushed again, or a bump
that leaves the comment behind, fails here. `--only ossf/scorecard-action`
checks that one action, for a job that must pass before the image is pulled.

Two checks cover the pin set as a whole. A `uses:` that names no full commit
SHA (nor a path in this repository, nor a Docker image by digest) fails: the
comparison above would otherwise pass over it in silence. And the colophon
page states how many actions are pinned, so a count that differs from the
pins found here fails as well.

Run locally with `gh auth token` available, or in CI with GITHUB_TOKEN.
"""

from __future__ import annotations

import argparse
import base64
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
COLOPHON = WORKFLOW_DIR.parent.parent / "frontend" / "src" / "views" / "ColophonView.vue"
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

# Every `uses:` key, quoted or not: a step's action or a job's reusable workflow.
USES_RE = re.compile(r"""^\s*(?:-\s+)?uses:\s*(?P<q>['"]?)(?P<ref>[^\s'"#]+)(?P=q)""")

# What a `uses:` may name: a commit by its full SHA, a path in this repository,
# or a Docker image by digest.
PINNED_USES_RE = re.compile(
    r"[\w.-]+/[\w.-]+(?:/[\w.-]+)*@[0-9a-f]{40}|\./\S*|docker://\S+@sha256:[0-9a-f]{64}"
)

# The colophon's count: "All <number> third-party build steps are pinned ...".
PIN_CLAIM_RE = re.compile(r"\bAll\s+(?P<count>[\w-]+)\s+third-party\s+build\s+steps\b")
_UNITS = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]
_TENS = ["twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

# Docker-hosted or first-party actions that carry no resolvable upstream tag.
SKIP_REPOS: set[str] = set()

# Actions whose `version:` input picks a ghcr.io image (see the docstring):
# action repo -> image repository on ghcr.io.
IMAGE_VERSION_ACTIONS = {"trufflesecurity/trufflehog": "trufflesecurity/trufflehog"}

# `<tag>@sha256:<digest>`, optionally quoted, optionally followed by a comment.
IMAGE_PIN_RE = re.compile(
    r"""^(?P<q>['"]?)(?P<tag>\w[\w.-]*)(?:@(?P<digest>sha256:[0-9a-f]{64}))?(?P=q)(?:\s+#.*)?$"""
)

# A Docker action's `runs.image` when it is a ghcr.io image named by tag.
GHCR_TAG_RE = re.compile(r"docker://ghcr\.io/(?P<image>[a-z0-9._/-]+):(?P<tag>\w[\w.-]*)")

# The comment that records such an image under its `uses:` (see the docstring).
IMAGE_COMMENT_RE = re.compile(
    r"#\s*image:\s*ghcr\.io/(?P<image>[a-z0-9._/-]+):(?P<tag>\w[\w.-]*)"
    r"@(?P<digest>sha256:[0-9a-f]{64})"
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


def image_comment(lines: list[str], uses_index: int) -> tuple[int, str] | None:
    """(line number, text) of the `# image:` line among the comments right under
    the `uses:` at lines[uses_index], or None when there is none."""
    for index in range(uses_index + 1, len(lines)):
        text = lines[index].strip()
        if not text.startswith("#"):
            break
        if re.match(r"#\s*image:", text):
            return index + 1, text
    return None


def docker_image(metadata: str) -> str | None:
    """`runs.image` of an action's metadata when `runs.using` is docker, else None.

    Line-based like step_input(): only the keys one level under `runs:` count.
    """
    in_runs, level, keys = False, 0, {}
    for line in metadata.splitlines():
        text = line.strip()
        if not text or text.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            in_runs, level = text.partition(":")[0] == "runs", 0
        elif in_runs:
            level = level or indent
            if indent == level:
                key, _, value = text.partition(":")
                keys[key] = value.split(" #")[0].strip().strip("'\"")
    return keys.get("image") if keys.get("using") == "docker" else None


def action_metadata(repo: str, subpath: str, sha: str, token: str | None) -> str | None:
    """The action.yml, else the action.yaml, of an action at `sha`; None when it has neither."""
    for name in ("action.yml", "action.yaml"):
        found = _api(f"/repos/{repo}/contents{subpath}/{name}?ref={sha}", token)
        if isinstance(found, dict) and isinstance(found.get("content"), str):
            return base64.b64decode(found["content"]).decode("utf-8")
    return None


def audit_docker_image(
    action: str, image: str, where: str, comment: tuple[str, int, str] | None
) -> str | None:
    """Failure message for one `uses:` of a Docker action whose metadata runs `image`, or None.

    `action` names the pin, `where` is its `uses:` line and `comment` the
    (file, line, text) of the `# image:` comment under it.
    """
    if not image.startswith("docker://") or "@sha256:" in image:
        # Built from the pinned commit's Dockerfile, or fixed by digest upstream.
        return None
    tagged = GHCR_TAG_RE.fullmatch(image)
    if tagged is None:
        return f"{where}: {action} runs {image}, a tag on a registry this script cannot read"
    ref = f"ghcr.io/{tagged['image']}:{tagged['tag']}"
    fix = (
        f"record `# image: {ref}@sha256:<digest>` under the `uses:`, from "
        f"`docker buildx imagetools inspect {ref}`"
    )
    if comment is None:
        return f"{where}: {action} runs {ref}, a tag its SHA pin does not fix -- {fix}"

    file_name, lineno, text = comment
    at = f"{file_name}:{lineno}"
    pin = IMAGE_COMMENT_RE.fullmatch(text)
    if pin is None:
        return f"{at}: {text!r} is not `# image: ghcr.io/<repository>:<tag>@sha256:<digest>`"
    if (pin["image"], pin["tag"]) != (tagged["image"], tagged["tag"]):
        return (
            f"{at}: records ghcr.io/{pin['image']}:{pin['tag']}, but {action} runs {ref}; "
            f"the comment must move with the action -- {fix}"
        )

    served = ghcr_digest(tagged["image"], tagged["tag"])
    if served is None:
        return f"{at}: ghcr.io/{tagged['image']} has no tag {tagged['tag']!r}"
    if served != pin["digest"]:
        return (
            f"{at}: {ref} is {served[:19]}, but the recorded digest is {pin['digest'][:19]} "
            "-- the tag was pushed again since it was recorded"
        )

    print(f"[+] {action} image {ref}@{served[:19]} = ghcr.io  ({at})")
    return None


def unpinned_uses(lines: list[str], file_name: str) -> list[str]:
    """A failure line for every `uses:` in a workflow that PINNED_USES_RE does not accept."""
    return [
        f"{file_name}:{lineno}: uses: {uses['ref']} is not pinned to a full commit SHA"
        for lineno, line in enumerate(lines, 1)
        if (uses := USES_RE.match(line)) and not PINNED_USES_RE.fullmatch(uses["ref"])
    ]


def number_word(word: str) -> int | None:
    """The value of digits or of an English number below one hundred, else None."""
    word = word.lower()
    if word.isdigit():
        return int(word)
    if word in _UNITS:
        return _UNITS.index(word)
    tens, _, unit = word.partition("-")
    if tens in _TENS and (not unit or unit in _UNITS[1:10]):
        return 20 + 10 * _TENS.index(tens) + (_UNITS.index(unit) if unit else 0)
    return None


def pin_claim(colophon: Path) -> tuple[str, int] | None:
    """(phrase, number) of the colophon's count of pinned steps, or None when it states none."""
    if not colophon.is_file():
        return None
    for match in PIN_CLAIM_RE.finditer(colophon.read_text(encoding="utf-8")):
        count = number_word(match["count"])
        if count is not None:
            return match[0], count
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify the action pins in .github/workflows.")
    parser.add_argument(
        "--only",
        action="append",
        metavar="OWNER/REPO",
        help="check only this action's pins, without the checks over the whole pin set",
    )
    only = parser.parse_args(argv).only
    token = _token()
    if not token:
        print("[!] No GITHUB_TOKEN and no gh auth token; unauthenticated API.")

    # (repo, sha, version) -> list of "file:line" so one lookup covers repeats.
    pins: dict[tuple[str, str, str | None], list[str]] = {}
    # (repo, "file:line" of the uses:, its version comment, (file, line, value)
    # of the step's version input or None) for IMAGE_VERSION_ACTIONS steps.
    image_pins: list[tuple[str, str, str | None, tuple[str, int, str] | None]] = []
    # (repo, subpath, sha) -> ("file:line" of a uses:, (file, line, text) of its
    # `# image:` comment or None) for every use, for the Docker image check.
    actions: dict[tuple[str, str, str], list[tuple[str, tuple[str, int, str] | None]]] = {}
    failures: list[str] = []
    for path in sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml")):
        lines = path.read_text(encoding="utf-8").splitlines()
        if not only:
            failures.extend(unpinned_uses(lines, path.name))
        for lineno, line in enumerate(lines, 1):
            match = PIN_RE.search(line)
            if not match:
                continue
            repo = f"{match['owner']}/{match['repo']}"
            if only and repo not in only:
                continue
            key = (repo, match["sha"], match["version"])
            pins.setdefault(key, []).append(f"{path.name}:{lineno}")
            if repo in IMAGE_VERSION_ACTIONS:
                found = step_input(lines, lineno - 1, "version")
                version_input = (path.name, *found) if found else None
                image_pins.append((repo, f"{path.name}:{lineno}", match["version"], version_input))
            noted = image_comment(lines, lineno - 1)
            comment = (path.name, *noted) if noted else None
            actions.setdefault((repo, match["subpath"], match["sha"]), []).append(
                (f"{path.name}:{lineno}", comment)
            )

    if not pins:
        print("[-] No SHA-pinned actions found -- is the workflow directory right?")
        return 1

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

    for (repo, subpath, sha), uses in sorted(actions.items()):
        if subpath.endswith((".yml", ".yaml")):
            continue  # a reusable workflow, which has no action metadata
        action = f"{repo}{subpath}@{sha[:12]}"
        metadata = action_metadata(repo, subpath, sha, token)
        if metadata is None:
            failures.append(f"{uses[0][0]}: {action} has no action.yml or action.yaml")
            continue
        image = docker_image(metadata)
        if image is None:
            continue
        for where, comment in uses:
            failure = audit_docker_image(action, image, where, comment)
            if failure:
                failures.append(failure)

    claim = None if only else pin_claim(COLOPHON)
    if claim is not None:
        page = COLOPHON.relative_to(WORKFLOW_DIR.parent.parent).as_posix()
        if claim[1] != len(pins):
            failures.append(
                f"{page}: says {claim[0]!r}, but {len(pins)} actions are pinned -- "
                "move the page's number with the pins"
            )
        else:
            print(f"[+] {page}: {claim[0]!r} = {len(pins)} pinned actions")

    if failures:
        print(f"\n[-] {len(failures)} action pin check(s) failed:\n")
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
