"""The production image's build steps, read from backend/Dockerfile.

No CI job builds the image: Fly's remote builder builds it from this file at
deploy time, so a regression in these steps would pass every other test. The
CI installs of the same requirements files are held to its install flags too.
"""

import re
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"
WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "ci-cd.yml"


def _instructions() -> list[tuple[str, str]]:
    """(keyword, arguments) per instruction: comments dropped, continuations
    joined, and each run of whitespace in the arguments made one space.
    """
    lines = DOCKERFILE.read_text(encoding="utf-8").splitlines()
    text = "\n".join(line for line in lines if not line.lstrip().startswith("#"))
    steps = []
    for line in re.sub(r"\\\n", " ", text).splitlines():
        keyword, _, arguments = line.strip().partition(" ")
        if keyword:
            steps.append((keyword.upper(), " ".join(arguments.split())))
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


def test_the_runtime_stage_removes_pip() -> None:
    """Nothing installs packages at runtime, so the image keeps no installer.

    ensurepip's bundled wheel goes too: `python -m ensurepip` reinstalls pip
    from it.
    """
    stage = _runtime_stage()
    removals = [
        (i, arguments)
        for i, (keyword, arguments) in enumerate(stage)
        if keyword == "RUN" and "pip uninstall" in arguments
    ]
    assert len(removals) == 1
    [(removal, command)] = removals
    assert command.startswith("python -m pip uninstall --yes pip && ")
    assert "ensurepip" in command and "'_bundled'" in command
    # Nothing copied or installed into the Python prefix later brings pip back.
    later = [a for i, (k, a) in enumerate(stage) if i > removal and k in {"ADD", "COPY", "RUN"}]
    assert [a for a in later if "pip" in a or "/usr/local" in a] == []


def test_requirement_installs_take_hash_checked_wheels_only() -> None:
    """pip would build a pin without a matching wheel from its sdist, and it
    installs a build's dependencies without checking any hash.

    The CI installs refuse sdists as the image build does, so such a pin fails
    the backend job before Fly's builder sees it.
    """
    image = [a for keyword, a in _instructions() if keyword == "RUN" and "pip install" in a]
    ci = [
        line.strip()
        for line in WORKFLOW.read_text(encoding="utf-8").splitlines()
        if re.match(r"\s*(python -m )?pip install ", line)
    ]
    assert len(image) == 1
    assert image[0].endswith(" -r requirements.txt")
    for requirements in ("requirements-pip.txt", "requirements.txt", "requirements-dev.txt"):
        assert [c for c in ci if c.endswith(f" -r {requirements}")], requirements
    for command in image + ci:
        assert "--require-hashes" in command.split(), command
        assert "--only-binary=:all:" in command.split(), command
