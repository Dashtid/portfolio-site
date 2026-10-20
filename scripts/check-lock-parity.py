"""Fail when backend/uv.lock disagrees with pyproject.toml or the requirements files.

CI installs the backend from requirements.txt and requirements-dev.txt under
--require-hashes, and nothing else in CI reads uv.lock. A bump that moves
pyproject.toml and the requirements files but skips `uv lock` therefore leaves
the lock stale in total silence, and the drift resurfaces later as a large
unrelated diff the next time someone runs `uv export` (which
scripts/gen-dev-requirements.py does).

This guard needs nothing but the standard library (tomllib, Python 3.11+), so
CI runs it before installing anything. It fails when any package pinned in
either requirements file, or pinned exactly (`name==version`) in
pyproject.toml's dependencies or optional dependencies, is absent from uv.lock
or locked at another version. A pyproject.toml range such as `>=2.7.0` is not
checked: it names no single version, and comparing ranges needs a version
parser the standard library does not have. It reads only the pins: hashes are
pip's job at install time, and lock entries nothing pins (the project itself,
packages for other platforms) are not its concern.

Usage, from the repository root:
    python scripts/check-lock-parity.py [backend-dir]
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

REQUIREMENT_FILES = ("requirements.txt", "requirements-dev.txt")

# A pinned requirement line, as uv writes them:
#     sqlalchemy==2.1.4 \
#     colorama==0.4.6 ; sys_platform == 'win32' \
# Extras are tolerated (`name[extra]==1.0`) although uv does not emit them.
PIN_RE = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?==([^\s;\\]+)")

# An exact pin in pyproject.toml, e.g. "uvicorn[standard]==0.54.0", with an
# optional environment marker. Anything else (a range, several specifiers, a
# URL) does not match and is not an exact pin.
PYPROJECT_PIN_RE = re.compile(
    r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)\s*(?:\[[^\]]*\])?\s*==\s*([^\s;,]+)\s*(?:;.*)?$"
)

REGENERATE = """\
Regenerate the lock and both requirements files together. In backend/:
    uv lock
    uv pip compile pyproject.toml -o requirements.txt --generate-hashes \\
        --python-platform x86_64-unknown-linux-gnu --python-version 3.14
then from the repository root:
    python scripts/gen-dev-requirements.py backend"""


def normalise(name: str) -> str:
    """PEP 503 name normalisation, the form uv.lock records names in."""
    return re.sub(r"[-_.]+", "-", name).lower()


def read_pins(path: Path) -> list[tuple[int, str, str]]:
    """Return (line number, normalised name, version) for every pin in a file.

    A top-level line that is not an exact `name==version` pin is an error, not
    something to skip: these files are fully pinned and hash-locked, so an
    unparseable line means the file or this parser changed, and a guard that
    silently skips what it cannot read passes over exactly that.
    """
    pins: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line[0].isspace():
            # The `--hash` continuation lines that belong to the pin above.
            # Any other indented line is NOT harmless: pip reads an indented
            # `pkg==1.0` as a requirement of its own, so skipping it would
            # let an unlocked package through.
            if stripped.startswith("--hash="):
                continue
            raise SystemExit(
                f"[-] {path}:{lineno}: indented line that is not a --hash continuation: {line!r}"
            )
        match = PIN_RE.match(line)
        if match is None:
            raise SystemExit(f"[-] {path}:{lineno}: not an exact `name==version` pin: {line!r}")
        pins.append((lineno, normalise(match.group(1)), match.group(2)))
    return pins


def read_pyproject_pins(path: Path) -> list[tuple[str, str, str]]:
    """Return (table, normalised name, version) for every exact pin in pyproject.toml.

    Reads [project] dependencies and every [project.optional-dependencies]
    group. Requirements that are not exact pins are skipped (see the module
    docstring).
    """
    with path.open("rb") as fh:
        project = tomllib.load(fh).get("project", {})
    groups: list[tuple[str, list[str]]] = [("dependencies", project.get("dependencies", []))]
    for group, requirements in project.get("optional-dependencies", {}).items():
        groups.append((f"optional-dependencies.{group}", requirements))
    pins: list[tuple[str, str, str]] = []
    for table, requirements in groups:
        for requirement in requirements:
            match = PYPROJECT_PIN_RE.match(requirement)
            if match is not None:
                pins.append((table, normalise(match.group(1)), match.group(2)))
    return pins


def read_lock(path: Path) -> dict[str, set[str]]:
    """Map each normalised package name in uv.lock to its locked version(s).

    A universal lock can hold more than one version of a package when the
    resolution forks on a marker, hence a set.
    """
    with path.open("rb") as fh:
        data = tomllib.load(fh)
    locked: dict[str, set[str]] = {}
    for package in data.get("package", []):
        version = package.get("version")
        if version is not None:
            locked.setdefault(normalise(package["name"]), set()).add(version)
    return locked


def main() -> int:
    default_backend = Path(__file__).resolve().parent.parent / "backend"
    backend = Path(sys.argv[1]) if len(sys.argv) > 1 else default_backend

    lock_path = backend / "uv.lock"
    pyproject_path = backend / "pyproject.toml"
    expected = (lock_path, pyproject_path, *(backend / f for f in REQUIREMENT_FILES))
    missing = [p for p in expected if not p.is_file()]
    if missing:
        print(f"[-] missing: {', '.join(str(p) for p in missing)}")
        return 1

    locked = read_lock(lock_path)
    if not locked:
        print(f"[-] {lock_path} holds no packages")
        return 1

    problems: list[str] = []
    counts: list[str] = []
    for filename in REQUIREMENT_FILES:
        path = backend / filename
        pins = read_pins(path)
        if not pins:
            # An empty pin list would "pass" while checking nothing.
            problems.append(f"{path}: no `name==version` pins found")
        counts.append(f"{len(pins)} in {filename}")
        for lineno, name, version in pins:
            versions = locked.get(name)
            if versions is None:
                problems.append(f"{path}:{lineno}: {name}=={version} is not in uv.lock at all")
            elif version not in versions:
                have = ", ".join(sorted(versions))
                problems.append(f"{path}:{lineno}: {name}=={version} but uv.lock has {have}")

    pyproject_pins = read_pyproject_pins(pyproject_path)
    if not pyproject_pins:
        problems.append(f"{pyproject_path}: no exact `name==version` pins found")
    counts.append(f"{len(pyproject_pins)} in pyproject.toml")
    for table, name, version in pyproject_pins:
        versions = locked.get(name)
        if versions is None:
            problems.append(
                f"{pyproject_path} [{table}]: {name}=={version} is not in uv.lock at all"
            )
        elif version not in versions:
            have = ", ".join(sorted(versions))
            problems.append(f"{pyproject_path} [{table}]: {name}=={version} but uv.lock has {have}")

    if problems:
        print(f"[-] {lock_path} does not match pyproject.toml or the requirements files:")
        for problem in problems:
            print(f"    {problem}")
        print()
        print(REGENERATE)
        return 1

    print(f"[+] {lock_path} matches every pin ({', '.join(counts)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
