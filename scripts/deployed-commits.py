"""Print, for each half of production, the commit its path filter starts from.

ci-cd.yml picks the jobs a push runs from the paths that push changed. When a
deploy fails, is skipped or never runs, the next push looks only at its own
diff, so one half of production can stay behind main while the newest run is
green. On every push the changes job runs this script and applies the path
filters to the range from each printed commit to the pushed one as well, so a
half that is behind runs its checks and deploys again.

The commits come from the deployment records the deploy jobs leave in the
GitHub environment. Each deploy job sets its own environment URL, and a half's
commit is the one of the newest deployment that has a success status at that
URL. Every status is read, not only the newest: a later deploy by the same job
adds an inactive status to the earlier deployment. When that commit is newer
than the checked-out one (a re-run of an older pipeline run), the checked-out
commit is printed instead: the filter then finds nothing, so catching up never
deploys an older tree.

For each NAME=URL argument the script appends NAME=<commit> to the file named
by $GITHUB_OUTPUT, or prints it when that is unset. The commit is empty when
none of the newest 100 deployments succeeded at the URL, when the API cannot
be read, or when git does not have the commit; the workflow treats an empty
commit as drift, so a failure here costs an extra check and deploy, never a
skipped one.

Standard library and git only; run it in a full-history checkout. Reads
GITHUB_REPOSITORY, and GITHUB_TOKEN when set.

Usage:
    python3 scripts/deployed-commits.py ENVIRONMENT NAME=URL [NAME=URL ...]
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping, Sequence

API = os.environ.get("GITHUB_API_URL", "https://api.github.com")
PER_PAGE = 100
ATTEMPTS = 3
RETRY_SECONDS = 5
COMMIT_RE = re.compile(r"[0-9a-f]{40}")

Get = Callable[[str], object]
Git = Callable[..., subprocess.CompletedProcess[str]]


def deployed_commits(environment: str, urls: Mapping[str, str], get: Get) -> dict[str, str]:
    """NAME -> commit of the newest deployment with a success status at urls[NAME].

    `get` takes an API path below the repository and returns the parsed JSON.
    A name is missing from the result when no listed deployment succeeded at
    its URL, and maps to "" when that deployment's commit is not a full SHA.
    """
    wanted = {name: url.rstrip("/") for name, url in urls.items()}
    query = urllib.parse.urlencode({"environment": environment, "per_page": PER_PAGE})
    deployments = get(f"/deployments?{query}")
    if not isinstance(deployments, list):
        raise TypeError(f"expected a list of deployments, got {type(deployments).__name__}")
    found: dict[str, str] = {}
    newest_first = sorted(deployments, key=lambda d: (d["created_at"], d["id"]), reverse=True)
    for deployment in newest_first:
        if len(found) == len(wanted):
            break
        statuses = get(f"/deployments/{deployment['id']}/statuses?per_page={PER_PAGE}")
        if not isinstance(statuses, list):
            raise TypeError(f"expected a list of statuses, got {type(statuses).__name__}")
        succeeded = {
            str(status.get("environment_url") or "").rstrip("/")
            for status in statuses
            if status.get("state") == "success"
        }
        sha = str(deployment.get("sha") or "")
        for name, url in wanted.items():
            if name not in found and url in succeeded:
                found[name] = sha if COMMIT_RE.fullmatch(sha) else ""
    return found


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], capture_output=True, text=True, check=False)


def filter_base(deployed: str, head: str, git: Git = _git) -> str:
    """The commit to filter from for a half last deployed from `deployed`.

    `deployed` itself when it is `head`, one of its ancestors, or on another
    line of history; `head` when `deployed` descends from it (production is
    ahead of this run); "" when git cannot place `deployed`.
    """
    if deployed == head:
        return deployed
    # --is-ancestor exits 0 for yes and 1 for no; any other code is an error,
    # such as a commit this clone does not have.
    behind = git("merge-base", "--is-ancestor", deployed, head).returncode
    if behind == 0:
        return deployed
    if behind != 1:
        return ""
    ahead = git("merge-base", "--is-ancestor", head, deployed).returncode
    if ahead == 0:
        return head
    return deployed if ahead == 1 else ""


def _get_json(url: str, token: str | None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "deployed-commits",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as exc:
            # A 4xx is an answer; only a server error is worth another try.
            if exc.code < 500 or attempt == ATTEMPTS:
                raise
        except OSError:
            if attempt == ATTEMPTS:
                raise
        time.sleep(RETRY_SECONDS)
    raise AssertionError("unreachable: the last attempt returns or raises")


def _repository_api() -> Get:
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    if not repository:
        raise RuntimeError("GITHUB_REPOSITORY is not set")
    token = os.environ.get("GITHUB_TOKEN") or None
    return lambda path: _get_json(f"{API}/repos/{repository}{path}", token)


def main(argv: Sequence[str], get: Get | None = None, git: Git = _git) -> int:
    pairs = [arg.partition("=") for arg in argv[2:]]
    if len(argv) < 3 or not all(name and sep and url for name, sep, url in pairs):
        print(__doc__)
        return 2
    environment = argv[1]
    urls = {name: url for name, _, url in pairs}
    try:
        found = deployed_commits(environment, urls, get or _repository_api())
    except Exception as exc:  # noqa: BLE001 - every failure leaves the commits unknown (drift)
        print(f"::warning::Could not read the {environment} deployments: {exc}")
        found = {}
    head = git("rev-parse", "HEAD").stdout.strip()
    lines = []
    for name, url in urls.items():
        deployed = found.get(name, "")
        base = filter_base(deployed, head, git) if deployed and head else ""
        if not base:
            print(f"::warning::No usable successful deploy to {url}; {name} runs its checks")
        elif base == deployed:
            print(f"[+] {name}: the last successful deploy to {url} was {deployed}")
        else:
            print(f"[i] {name}: the last deploy to {url}, {deployed}, is newer than {head}")
        lines.append(f"{name}={base}\n")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.writelines(lines)
    else:
        sys.stdout.writelines(lines)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
