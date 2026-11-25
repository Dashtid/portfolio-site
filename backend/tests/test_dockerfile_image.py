"""The production image's build steps, read from backend/Dockerfile.

No CI job builds the image: Fly's remote builder builds it from this file at
deploy time, so a regression in these steps would pass every other test.
"""

import re
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def _instructions() -> list[tuple[str, str]]:
    """(keyword, arguments) per instruction; comments dropped, continuations joined."""
    lines = DOCKERFILE.read_text(encoding="utf-8").splitlines()
    text = "\n".join(line for line in lines if not line.lstrip().startswith("#"))
    steps = []
    for line in re.sub(r"\\\n\s*", " ", text).splitlines():
        keyword, _, arguments = line.strip().partition(" ")
        if keyword:
            steps.append((keyword.upper(), arguments.strip()))
    return steps


def _runtime_stage() -> list[tuple[str, str]]:
    """The instructions after the last FROM: the stage production runs."""
    steps = _instructions()
    last_from = max(i for i, (keyword, _) in enumerate(steps) if keyword == "FROM")
    return steps[last_from + 1 :]


def test_the_code_is_root_owned_and_the_server_runs_as_appuser() -> None:
    """A COPY without --chown leaves the files owned by root, so the server
    can read the code but not rewrite it; it writes only to UPLOAD_DIR and /tmp.
    """
    stage = _runtime_stage()
    copies = [arguments for keyword, arguments in stage if keyword == "COPY"]
    assert copies
    assert [c for c in copies if "--chown" in c or "--chmod" in c] == []
    [useradd] = [arguments for keyword, arguments in stage if "useradd" in arguments]
    uid = re.search(r"--uid (\d+)", useradd)
    assert uid and int(uid.group(1)) != 0
    assert useradd.endswith(" appuser")
    users = [i for i, (keyword, _) in enumerate(stage) if keyword == "USER"]
    assert [stage[i][1] for i in users] == ["appuser"]
    # Every step that writes to the image runs before privileges drop.
    writes = [i for i, (keyword, _) in enumerate(stage) if keyword in {"ADD", "COPY", "RUN"}]
    assert max(writes) < users[0]
