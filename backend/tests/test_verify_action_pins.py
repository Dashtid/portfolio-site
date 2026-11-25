"""scripts/verify_action_pins.py holds every action reference to a full commit SHA.

security-scan runs it on every push and pull request. These tests give it
workflow files written here, with tag lookups answered from a table, and run
its offline checks over the repository's own workflows.
"""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[2]


def _load_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "verify_action_pins", ROOT / "scripts" / "verify_action_pins.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pins = _load_script()

CHECKOUT = "3d3c42e5aac5ba805825da76410c181273ba90b1"
SETUP_NODE = "949feb2413d6458794dcd2491c4babbbce0c15c1"
TAGS = {("actions/checkout", "v7.0.1"): CHECKOUT, ("actions/setup-node", "v7.1.0"): SETUP_NODE}
PINNED = f"""jobs:
  build:
    steps:
      - uses: actions/checkout@{CHECKOUT} # v7.0.1
      - uses: actions/setup-node@{SETUP_NODE} # v7.1.0
"""


def test_every_uses_without_a_full_commit_sha_is_reported() -> None:
    lines = f"""jobs:
  build:
    steps:
      - uses: actions/checkout@{CHECKOUT} # v7.0.1
      - uses: actions/checkout@v4
      - name: quoted
        uses: "actions/setup-node@v6"
      - uses: 'owner/repo/sub/path@main'
      - uses: docker://alpine:3.20
      - uses: docker://alpine@sha256:{"a" * 64}
      - uses: ./.github/actions/local
      # uses: actions/checkout@v3 in a comment is not a step
      - uses: actions/checkout@{CHECKOUT}0
  reuse:
    uses: owner/repo/.github/workflows/build.yml@v1
""".splitlines()
    assert pins.unpinned_uses(lines, "ci.yml") == [
        "ci.yml:5: uses: actions/checkout@v4 is not pinned to a full commit SHA",
        "ci.yml:7: uses: actions/setup-node@v6 is not pinned to a full commit SHA",
        "ci.yml:8: uses: owner/repo/sub/path@main is not pinned to a full commit SHA",
        "ci.yml:9: uses: docker://alpine:3.20 is not pinned to a full commit SHA",
        f"ci.yml:13: uses: actions/checkout@{CHECKOUT}0 is not pinned to a full commit SHA",
        "ci.yml:15: uses: owner/repo/.github/workflows/build.yml@v1 is not pinned to a full "
        "commit SHA",
    ]


@pytest.mark.parametrize(
    ("word", "value"),
    [("fifteen", 15), ("Sixteen", 16), ("15", 15), ("twenty", 20), ("twenty-one", 21)],
)
def test_number_words_read_as_numbers(word: str, value: int) -> None:
    assert pins.number_word(word) == value


@pytest.mark.parametrize("word", ["Every", "twenty-ten", "one-twenty", ""])
def test_other_words_are_not_numbers(word: str) -> None:
    assert pins.number_word(word) is None


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository layout with no workflows yet; tag lookups answer from TAGS."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    colophon = tmp_path / "frontend" / "src" / "views" / "ColophonView.vue"
    colophon.parent.mkdir(parents=True)
    monkeypatch.setattr(pins, "WORKFLOW_DIR", workflows)
    monkeypatch.setattr(pins, "COLOPHON", colophon)
    monkeypatch.setattr(pins, "_token", lambda: "token")
    monkeypatch.setattr(pins, "resolve_tag", lambda repo, tag, _: (TAGS.get((repo, tag)), None))
    return tmp_path


def _write(repo: Path, workflow: str, colophon: str | None = None) -> None:
    (repo / ".github" / "workflows" / "ci.yml").write_text(workflow, encoding="utf-8")
    if colophon is not None:
        (repo / "frontend" / "src" / "views" / "ColophonView.vue").write_text(
            colophon, encoding="utf-8"
        )


def test_pins_that_match_their_comments_pass(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _write(repo, PINNED)
    assert pins.main() == 0
    assert "[+] All 2 pinned actions match their version comments." in capsys.readouterr().out


def test_a_tag_reference_fails_the_run(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(repo, PINNED + "      - uses: actions/cache@v5\n")
    assert pins.main() == 1
    assert "ci.yml:6: uses: actions/cache@v5 is not pinned" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("claim", "code"),
    [
        ("All two third-party build steps are pinned to an exact commit", 0),
        ("All 2 third-party build steps are pinned to an exact commit", 0),
        ("All three third-party build steps are pinned to an exact commit", 1),
        ("Every third-party build step is pinned to an exact commit", 0),
    ],
)
def test_the_colophon_count_must_match_the_pins(
    repo: Path, capsys: pytest.CaptureFixture[str], claim: str, code: int
) -> None:
    _write(repo, PINNED, f"<script>\nconst text = '{claim}.'\n</script>\n")
    assert pins.main() == code
    out = capsys.readouterr().out
    if code:
        assert (
            "frontend/src/views/ColophonView.vue: says 'All three third-party build steps'" in out
        )
        assert "but 2 actions are pinned" in out


def test_the_repository_pins_every_uses_and_states_the_right_count() -> None:
    files = sorted(pins.WORKFLOW_DIR.glob("*.yml")) + sorted(pins.WORKFLOW_DIR.glob("*.yaml"))
    assert files
    keys = set()
    for path in files:
        lines = path.read_text(encoding="utf-8").splitlines()
        assert pins.unpinned_uses(lines, path.name) == []
        for line in lines:
            if match := pins.PIN_RE.search(line):
                keys.add((f"{match['owner']}/{match['repo']}", match["sha"], match["version"]))
    claim = pins.pin_claim(pins.COLOPHON)
    if claim is not None:
        assert claim[1] == len(keys), claim[0]
