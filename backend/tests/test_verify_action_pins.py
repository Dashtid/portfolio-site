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


NODE_ACTION = "name: x\nruns:\n  using: node24\n  main: dist/index.js\n"
SCORECARD = "fa7117db83c52d787ae5a89f350999701505d78e"
SCORECARD_ACTION = (
    'runs:\n  using: "docker"\n  image: "docker://ghcr.io/ossf/scorecard-action:v2.5.0"\n'
)
DIGEST = "sha256:" + "1e" * 32
SERVED = {("ossf/scorecard-action", "v2.5.0"): DIGEST}


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A repository layout with no workflows yet. Tag lookups answer from TAGS,
    action metadata is a node action's but scorecard-action's, and ghcr.io
    serves SERVED."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    colophon = tmp_path / "frontend" / "src" / "views" / "ColophonView.vue"
    colophon.parent.mkdir(parents=True)
    monkeypatch.setattr(pins, "WORKFLOW_DIR", workflows)
    monkeypatch.setattr(pins, "COLOPHON", colophon)
    monkeypatch.setattr(pins, "_token", lambda: "token")
    tags = {**TAGS, ("ossf/scorecard-action", "v2.5.0"): SCORECARD}
    monkeypatch.setattr(pins, "resolve_tag", lambda repo, tag, _: (tags.get((repo, tag)), None))
    monkeypatch.setattr(
        pins,
        "action_metadata",
        lambda repo, *_: SCORECARD_ACTION if repo == "ossf/scorecard-action" else NODE_ACTION,
    )
    monkeypatch.setattr(pins, "ghcr_digest", lambda image, tag: SERVED.get((image, tag)))
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
    assert pins.main([]) == 0
    assert "[+] All 2 pinned actions match their version comments." in capsys.readouterr().out


def test_a_tag_reference_fails_the_run(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(repo, PINNED + "      - uses: actions/cache@v5\n")
    assert pins.main([]) == 1
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
    assert pins.main([]) == code
    out = capsys.readouterr().out
    if code:
        assert (
            "frontend/src/views/ColophonView.vue: says 'All three third-party build steps'" in out
        )
        assert "but 2 actions are pinned" in out


@pytest.mark.parametrize(
    ("metadata", "image"),
    [
        (SCORECARD_ACTION, "docker://ghcr.io/ossf/scorecard-action:v2.5.0"),
        ("runs:\n  using: 'docker'\n  image: 'Dockerfile' # built here\n", "Dockerfile"),
        (NODE_ACTION, None),
        ("runs:\n  using: composite\n  steps:\n    - uses: docker://alpine:3.20\n", None),
        # Only the keys right under runs: count, not the env: below it.
        ("runs:\n  using: docker\n  env:\n    image: x\n  image: docker://y:1\n", "docker://y:1"),
        ("image: docker://y:1\nruns:\n  using: node24\n", None),
    ],
)
def test_docker_image_reads_the_runs_block(metadata: str, image: str | None) -> None:
    assert pins.docker_image(metadata) == image


STEP = f"""      - name: Run analysis
        uses: ossf/scorecard-action@{SCORECARD} # v2.5.0
        # The image the pinned action.yaml names; move it with the action.
        # image: ghcr.io/ossf/scorecard-action:v2.5.0@{DIGEST}
        with:
          results_format: sarif
"""


def test_the_image_comment_sits_among_the_comments_under_the_uses() -> None:
    lines = STEP.splitlines()
    assert pins.image_comment(lines, 1) == (
        4,
        f"# image: ghcr.io/ossf/scorecard-action:v2.5.0@{DIGEST}",
    )
    # A key between the uses: and the comment ends the search.
    assert pins.image_comment([lines[1], lines[4], lines[3]], 0) is None


ACTION = f"ossf/scorecard-action@{SCORECARD[:12]}"
TAGGED = "docker://ghcr.io/ossf/scorecard-action:v2.5.0"


def _audit(image: str, comment: str | None) -> str | None:
    return pins.audit_docker_image(
        ACTION, image, "scorecard.yml:30", ("scorecard.yml", 32, comment) if comment else None
    )


@pytest.mark.parametrize(
    ("image", "comment", "problem"),
    [
        (TAGGED, None, "a tag its SHA pin does not fix"),
        (TAGGED, "# image: ghcr.io/ossf/scorecard-action:v2.5.0", "is not `# image:"),
        (
            TAGGED,
            f"# image: ghcr.io/ossf/scorecard-action:v2.4.3@{DIGEST}",
            "records ghcr.io/ossf/scorecard-action:v2.4.3, but",
        ),
        (
            TAGGED,
            f"# image: ghcr.io/ossf/scorecard-action:v2.5.0@sha256:{'0' * 64}",
            "the tag was pushed again since it was recorded",
        ),
        (
            "docker://ghcr.io/ossf/scorecard-action:v9.9.9",
            f"# image: ghcr.io/ossf/scorecard-action:v9.9.9@{DIGEST}",
            "has no tag 'v9.9.9'",
        ),
        ("docker://alpine:3.20", None, "a registry this script cannot read"),
    ],
)
def test_an_image_tag_without_its_recorded_digest_fails(
    monkeypatch: pytest.MonkeyPatch, image: str, comment: str | None, problem: str
) -> None:
    monkeypatch.setattr(pins, "ghcr_digest", lambda image, tag: SERVED.get((image, tag)))
    failure = _audit(image, comment)
    assert failure is not None
    assert problem in failure


def test_an_image_the_sha_already_fixes_needs_no_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pins, "ghcr_digest", lambda image, tag: SERVED.get((image, tag)))
    assert _audit(f"docker://ghcr.io/ossf/scorecard-action@{DIGEST}", None) is None
    assert _audit("Dockerfile", None) is None
    assert _audit(TAGGED, f"# image: ghcr.io/ossf/scorecard-action:v2.5.0@{DIGEST}") is None


SCORECARD_WORKFLOW = f"""jobs:
  analysis:
    steps:
      - uses: actions/checkout@{CHECKOUT} # v7.0.1
{STEP}"""


def test_a_run_checks_the_scorecard_image(repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write(repo, SCORECARD_WORKFLOW)
    assert pins.main([]) == 0
    out = capsys.readouterr().out
    assert f"[+] {ACTION} image ghcr.io/ossf/scorecard-action:v2.5.0@{DIGEST[:19]}" in out
    _write(repo, SCORECARD_WORKFLOW.replace(DIGEST, f"sha256:{'0' * 64}"))
    assert pins.main([]) == 1


def test_only_checks_the_named_action_and_nothing_repository_wide(
    repo: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    unpinned = "      - uses: actions/cache@v5\n"
    claim = "<p>All nine third-party build steps are pinned</p>\n"
    _write(repo, SCORECARD_WORKFLOW + unpinned, claim)
    assert pins.main(["--only", "ossf/scorecard-action"]) == 0
    out = capsys.readouterr().out
    assert "[+] All 1 pinned actions match their version comments." in out
    assert "actions/checkout" not in out
    assert pins.main([]) == 1
    out = capsys.readouterr().out
    assert "actions/cache@v5 is not pinned" in out
    assert "says 'All nine third-party build steps'" in out
    # An --only for an action no workflow pins fails instead of passing empty.
    assert pins.main(["--only", "ossf/scorecard"]) == 1


def test_the_scorecard_step_records_its_image() -> None:
    lines = (pins.WORKFLOW_DIR / "scorecard.yml").read_text(encoding="utf-8").splitlines()
    [index] = [i for i, line in enumerate(lines) if "uses: ossf/scorecard-action@" in line]
    found = pins.image_comment(lines, index)
    assert found is not None
    assert pins.IMAGE_COMMENT_RE.fullmatch(found[1])


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
