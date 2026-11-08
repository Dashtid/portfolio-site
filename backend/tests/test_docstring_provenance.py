"""Docstrings and comments describe the change, not where it came from.

A style rule for the files where planning notes tend to collect: every
migration under alembic/versions, every module under app/ and the test suite.
A docstring or comment there says what the code does to which tables, columns
and rows, and which guard conditions make it safe to re-run. It does not
credit a change to a person, put a date on a person or a session, cite notes
kept outside this repository, or name a repository whose digest is listed
below.

Only comments (tokenize) and docstrings (ast) are scanned. Code, string data
and identifiers are out of scope, so test data never trips the rule. Each
docstring and each block of consecutive comment lines meets two kinds of check:

- ``_PATTERNS``: two regular expressions, matched case-insensitively. Their
  only quantifiers sit on single tokens or on one bounded group, so matching
  stays linear in the size of a file, and words are joined by ``\\s+`` or
  ``[\\s-]+``, so a phrase that wraps onto the next line still matches.
- ``_HASHED``: SHA-256 digests of lowercased terms, found with
  ``tests.hashed_terms``. Only the digests are kept in this repository.
"""

import ast
import io
import re
import tokenize
from datetime import date
from pathlib import Path

import pytest

from tests import hashed_terms

_BACKEND = Path(__file__).resolve().parents[1]
_SELF = Path(__file__).resolve()

_DECISION = (
    r"(?:approv(?:e|ed|al)|decid(?:e|ed)|decision|rul(?:e|ed|ing)|cho(?:se|sen|ice)"
    r"|reject(?:ed)?|declin(?:e|ed)|signed[\s-]+off|signed|sign-off|verdict|directive"
    r"|call|review|reported|said)"
)

_PATTERNS: dict[str, re.Pattern[str]] = {
    # The owner, then up to three words, then a decision word; or a decision
    # word, then "by (the) owner".
    "decision credited to the owner": re.compile(
        rf"\bowner(?:['\u2019]s)?[\s-]+(?:[\w'\u2019-]+\s+){{0,3}}?{_DECISION}\b"
        rf"|\b{_DECISION}\s+by\s+(?:the\s+)?owner\b",
        re.IGNORECASE,
    ),
    "date on the owner or a session": re.compile(
        r"\b(?:owner(?:['\u2019]s|,)?|session)\s+\d{4}-\d{2}-\d{2}\b", re.IGNORECASE
    ),
}

# label -> digests of lowercased terms, matched against every docstring and
# comment block.
_HASHED: dict[str, frozenset[str]] = {
    "repository name": hashed_terms.EXCLUDED_REPO_DIGESTS
    | frozenset({"13c59540372a16e775ade0189e39462ad2a91e1c43e3f2d806d8eed980150411"}),
    "listed phrase": frozenset(
        {
            "05edab2681bdf16b426847c04372fa0d96cb9e33d334128b066b11135e9eb7b3",
            "21af263d01f94887492818e28cd0b3dd0dafaa280e98be0aed029d200e202700",
            "3fd00a42816b40e446d851b4fb0397b32e049863b038eb9ecc6d13a27ff81f7f",
            "598de6843395d5293ee07107bb8da3552bfe2be35b665f023db9922aeca6ba95",
            "97303992b996ede0d37e3b874855569a630d6e0d68d645af81c37c9c2e8ac561",
            "9d98ce221dd52eccf27cad6a01bcd49b14d3d718a9eeeb3be94f0e231a5787ae",
            "a7c4c0f437e2c720199c4d405263870bfc829ef628ab4324b6434d0e7404c25d",
            "ae5666bb418906e0e2b2f98a4891edebf524aec334d70a35e1d74469e92628c0",
            "ca13786620feb8a855ed4cc5dc1dd9f36f604369ac525d69a947560763bbf811",
            "dd09065a1f077850496ff4451e1c6b0d90bde2fac12cab92d38a3f0ecff0fc13",
            "e67e0a4c6e1bd9a7739ad4899cbe3d014f04df2019de7db77c2fb2a6ac9dcedc",
            "fcac9e6a55ff02190279692da1b7811cbbfb7af6676a923b7c5175937319f63b",
        }
    ),
}

# Migration docstrings describe schema; they add one more list.
_HASHED_MIGRATION_DOCSTRING: dict[str, frozenset[str]] = {
    "listed field name": frozenset(
        {"5f1260f685647378e07be184a82a71b59418ac89b904a56e05fd3deccabd15bb"}
    ),
}


def _docstrings(tree: ast.Module) -> list[tuple[int, str]]:
    """(first line, text) of the module docstring and every class/def docstring."""
    nodes: list[ast.AST] = [tree]
    nodes.extend(
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    )
    found: list[tuple[int, str]] = []
    for node in nodes:
        body = getattr(node, "body", [])
        first = body[0] if body else None
        if (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            found.append((first.lineno, first.value.value))
    return found


def _comment_blocks(source: str) -> list[tuple[int, str]]:
    """(first line, text) of every run of comments on consecutive lines."""
    comments = [
        (tok.start[0], tok.string.lstrip("#").strip())
        for tok in tokenize.generate_tokens(io.StringIO(source).readline)
        if tok.type == tokenize.COMMENT
    ]
    blocks: list[tuple[int, list[str]]] = []
    previous = -1
    for line, text in comments:
        if blocks and line == previous + 1:
            blocks[-1][1].append(text)
        else:
            blocks.append((line, [text]))
        previous = line
    return [(start, "\n".join(texts)) for start, texts in blocks]


def _line(start: int, text: str, offset: int) -> int:
    """Source line of `offset` in a docstring or comment block that starts on `start`."""
    return start + text.count("\n", 0, offset)


def _offset(text: str, term: str) -> int:
    """Offset of a hashed-term match in `text`; a space in `term` matches any whitespace."""
    found = re.search(r"\s+".join(map(re.escape, term.split(" "))), text, re.IGNORECASE)
    return found.start() if found else 0


def _unit_hits(text: str, hashed: dict[str, frozenset[str]]) -> list[tuple[str, int, str]]:
    """(label, offset, matched text) for every rule hit in one docstring or comment block."""
    hits = [
        (label, match.start(), match.group(0))
        for label, pattern in _PATTERNS.items()
        for match in pattern.finditer(text)
    ]
    spans = {span: hashed_terms.digest(span) for span in set(hashed_terms.candidates(text))}
    hits.extend(
        (label, _offset(text, span), span)
        for label, digests in hashed.items()
        for span, digest in sorted(spans.items())
        if digest in digests
    )
    return hits


def scan(
    path: Path,
    base: Path = _BACKEND,
    hashed: dict[str, frozenset[str]] = _HASHED,
    migration_hashed: dict[str, frozenset[str]] = _HASHED_MIGRATION_DOCSTRING,
) -> list[str]:
    """Every rule hit in the comments and docstrings of one file, as file:line lines."""
    source = path.read_text(encoding="utf-8")
    rel = path.relative_to(base).as_posix()
    is_migration = rel.startswith("alembic/versions/")
    units = [("docstring", line, text) for line, text in _docstrings(ast.parse(source))]
    units += [("comment", line, text) for line, text in _comment_blocks(source)]
    hits: list[str] = []
    for kind, start, text in units:
        lists = {**hashed, **(migration_hashed if is_migration and kind == "docstring" else {})}
        hits.extend(
            f"{rel}:{_line(start, text, offset)}: {kind}: {label}: {term!r}"
            for label, offset, term in _unit_hits(text, lists)
        )
    return sorted(hits)


def scoped_files(base: Path = _BACKEND) -> list[Path]:
    """The files this rule covers, relative to a backend directory."""
    files = sorted((base / "alembic" / "versions").glob("*.py"))
    files.extend(sorted((base / "app").rglob("*.py")))
    files.extend(sorted(p for p in (base / "tests").rglob("*.py") if p.name != _SELF.name))
    return files


def _ids(path: Path) -> str:
    return path.relative_to(_BACKEND).as_posix()


@pytest.mark.parametrize("path", scoped_files(), ids=_ids)
def test_docstrings_and_comments_describe_the_change(path: Path) -> None:
    hits = scan(path)
    assert not hits, (
        "A docstring or comment credits a change to a person, dates a person or a "
        "session, or carries a listed term. Describe the change and its guards "
        "instead:\n" + "\n".join(hits)
    )


def test_scope_covers_migrations_seed_data_and_tests() -> None:
    rels = {_ids(path) for path in scoped_files()}
    assert "app/seed_data.py" in rels
    assert "app/api/v1/cv.py" in rels
    assert "tests/hashed_terms.py" in rels
    assert any(rel.startswith("alembic/versions/") for rel in rels)
    assert any(rel.startswith("tests/") for rel in rels)
    assert "tests/test_docstring_provenance.py" not in rels


def test_hashed_lists_hold_sha256_digests() -> None:
    lists = {**_HASHED, **_HASHED_MIGRATION_DOCSTRING}
    assert {label: len(digests) for label, digests in lists.items()} == {
        "repository name": 6,
        "listed phrase": 12,
        "listed field name": 1,
    }
    for digests in lists.values():
        assert all(len(d) == 64 and set(d) <= set("0123456789abcdef") for d in digests)


def _flags(text: str) -> bool:
    return any(pattern.search(text) for pattern in _PATTERNS.values())


@pytest.mark.parametrize(
    "word", ["approved", "decision", "ruling", "call", "signed off", "reported"]
)
def test_a_credited_decision_is_flagged_in_either_word_order(word: str) -> None:
    assert _flags(f"owner {word}")
    assert _flags(f"owner's {word}")
    assert _flags(f"owner-{word}")
    assert _flags(f"{word} by the owner")
    assert _flags(f"{word}\n    by the\n    owner")


def test_up_to_three_words_may_sit_between_the_owner_and_the_decision() -> None:
    assert _flags("owner's alpha beta gamma call")
    assert not _flags("owner's alpha beta gamma delta call")


def test_a_date_on_the_owner_or_a_session_is_flagged() -> None:
    day = date(2000, 1, 1).isoformat()
    assert _flags(f"owner, {day}")
    assert _flags(f"owner's {day}")
    assert _flags(f"session {day}")
    assert not _flags(f"measured {day}")


# Engineering notes the rules must leave alone, including the operational kind
# of owner mention this repository keeps.
_ALLOWED = (
    "Guarded on the exact previous value, so an admin edit is never trampled.",
    "Keyed on start month because the DB and the JSON disagree on company names.",
    "An EMPTY table is a no-op: fresh databases are seeded by seed_data.py instead.",
    "The owner's own CMS sessions are not visitor traffic.",
    "The payload carries the owner's private contact, so authorization comes first.",
    "If the owner already created the row by hand, the owner's row wins.",
    "Blank by default; the owner fills email/phone through the admin CV form.",
    "A visitor hits the owner's entry -> LRU bump.",
    "Downgrade is a deliberate no-op: the deleted rows are not recorded here.",
    "A rule with no match is skipped; the decision table is read once per request.",
    "The session cookie is set by the login route.",
)


@pytest.mark.parametrize("text", _ALLOWED)
def test_rules_leave_engineering_notes_alone(text: str) -> None:
    assert not _unit_hits(text, {**_HASHED, **_HASHED_MIGRATION_DOCSTRING})


def _module(tmp_path: Path, rel: str, text: str) -> Path:
    path = tmp_path / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_scan_flags_a_listed_term_in_a_docstring_and_in_a_comment(tmp_path: Path) -> None:
    hashed = {"listed phrase": frozenset({hashed_terms.digest("example notes")})}
    path = _module(
        tmp_path,
        "app/example.py",
        '"""Built from the example notes."""\n\n# Same as the example\n# notes say.\nVALUE = 1\n',
    )
    assert scan(path, base=tmp_path, hashed=hashed) == [
        "app/example.py:1: docstring: listed phrase: 'example notes'",
        "app/example.py:3: comment: listed phrase: 'example notes'",
    ]


def test_scan_flags_a_listed_repository_name_after_an_owner_prefix(tmp_path: Path) -> None:
    hashed = {"repository name": _HASHED["repository name"] | {hashed_terms.digest("example-repo")}}
    path = _module(tmp_path, "tests/test_example.py", "# Mirrors Dashtid/example-repo.\nX = 1\n")
    assert scan(path, base=tmp_path, hashed=hashed) == [
        "tests/test_example.py:1: comment: repository name: 'example-repo'",
    ]


def test_a_listed_field_name_is_flagged_only_in_migration_docstrings(tmp_path: Path) -> None:
    field = {"listed field name": frozenset({hashed_terms.digest("example_field")})}
    text = '"""Adds the example_field column."""\n'
    migration = _module(tmp_path, "alembic/versions/x_example.py", text)
    module = _module(tmp_path, "app/example.py", text)
    assert scan(migration, base=tmp_path, migration_hashed=field) == [
        "alembic/versions/x_example.py:1: docstring: listed field name: 'example_field'",
    ]
    assert scan(module, base=tmp_path, migration_hashed=field) == []
