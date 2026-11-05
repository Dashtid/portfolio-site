"""Docstrings and comments describe the change, not who decided it or why a claim went.

A style rule for the files where planning notes tend to collect: every
migration under alembic/versions, every module under app/ and the test suite. A
docstring or comment there says what the code does to which tables, columns
and rows, and which guard conditions make it safe to re-run. It does not
record who signed off on a change, cite planning notes or their sessions,
quote anyone, or argue why a professional claim was kept, reworded or
dropped. That belongs in private notes; this repository is public.

Only comments (tokenize) and docstrings (ast) are scanned. Code, string data
and identifiers are out of scope, so test data never trips the rule. Each
pattern is a plain phrase whose only quantifiers sit on single tokens (no
nested quantifiers), so matching stays linear in the size of a file. Words
are joined by \\s+, so a phrase that wraps onto the next line still matches.
"""

import ast
import io
import re
import tokenize
from pathlib import Path

import pytest

_BACKEND = Path(__file__).resolve().parents[1]
_SELF = Path(__file__).resolve()

# label -> pattern, matched case-insensitively against every docstring and
# every block of consecutive comment lines.
_RULES: dict[str, str] = {
    # Provenance: planning notes outside this repository, and their sessions.
    "planning-repo reference": r"\bcareer[\s-]+plan\b",
    "dated session citation": r"\bsession\s+\d{4}-\d{2}-\d{2}\b",
    "planning session": r"\bplanning\s+session\b",
    "dated requirements citation": r"\brequirements,?\s+\(?\d{4}-\d{2}-\d{2}\b",
    # Provenance: who decided.
    "decision credited to the owner": (
        r"\b(?:approved|signed[\s-]+off|declined|rejected|ruled|decided|chosen)"
        r"\s+by\s+the\s+owner\b"
    ),
    "the owner deciding": (
        r"\bthe\s+owner\s+(?:approved|signed|declined|rejected|ruled|chose|decided|said)\b"
    ),
    "owner-approved": r"\bowner-(?:approved|decided|ruled|chosen)\b",
    "owner ruling": r"\bowner\s+(?:rule|ruling|directive|decision|verdict|review|call)\b",
    "owner's ruling": (
        r"\bowner['\u2019]s\s+"
        r"(?:review|verdict|directive|decision|ruling|register|keyword\s+set)\b"
    ),
    "owner's named rule": r"\bowner['\u2019]s\s+[\w-]+\s+rule\b",
    "dated owner attribution": r"\bowner(?:['\u2019]s|,)?\s+\d{4}-\d{2}-\d{2}\b",
    "review verdict": r"\breview\s+verdict\b",
    "sign-off": r"\bsigned[\s-]+off\b",
    "approved copy": r"\bthe\s+approved\b",
    # Claim review: registers, gates and the vocabulary of auditing a CV.
    "claims register": r"\b(?:defensible[\s-]+claims?|claims?\s+register)\b",
    "register reference": r"\b(?:register['\u2019]s|register-exact|per\s+the\s+register)\b",
    "tier map": r"\btier[\s-]+map\b",
    "claim gate": r"\bclaim[\s-]+gat(?:e|ed|ing)\b",
    "over- or under-claiming": r"\b(?:over|under)[\s-]?claim",
    "unbacked or unearned": r"\b(?:unbacked|unearned|unfalsifiable)\b",
    "named claim": r"\b(?:banned|authorship|ownership|strongest)\s+claim\b",
    "claim ranking": r"\b(?:strength\s+order|weakest\s+claims?)\b",
    "honest subset": r"\bhonest\s+(?:set|pair|split)\b",
    "audit judgement": r"\b(?:vaguest|safe\s+direction)\b",
    "evidence census": r"\b(?:work|workload|code)\s+anywhere\b",
    "audit defect number": r"\bdefect\s+#\d",
    "quiz rule": r"\bquiz",
    # Facts about a CV kept outside this repository.
    "real CV": r"\b(?:real|hand-made)\s+CV\b",
    "page count": r"\b\d+-page\b",
    # Third-person narration about a person.
    "third-person narration": r"\b(?:himself|his\s+own)\b",
}

# Migrations add one more: their docstrings describe schema, not the private
# contact fields by name.
_MIGRATION_DOCSTRING_RULES: dict[str, str] = {
    "private contact field named in a migration docstring": r"\bpersonnummer\b",
}


def _compile(rules: dict[str, str]) -> tuple[tuple[str, re.Pattern[str]], ...]:
    return tuple((label, re.compile(pattern, re.IGNORECASE)) for label, pattern in rules.items())


_COMPILED = _compile(_RULES)
_COMPILED_MIGRATION = _compile(_MIGRATION_DOCSTRING_RULES)


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


def scan(path: Path, base: Path = _BACKEND) -> list[str]:
    """Every rule hit in the comments and docstrings of one file, as file:line lines."""
    source = path.read_text(encoding="utf-8")
    rel = path.relative_to(base).as_posix()
    is_migration = rel.startswith("alembic/versions/")
    units = [("docstring", line, text) for line, text in _docstrings(ast.parse(source))]
    units += [("comment", line, text) for line, text in _comment_blocks(source)]
    hits: list[str] = []
    for kind, start, text in units:
        rules = _COMPILED + (_COMPILED_MIGRATION if is_migration and kind == "docstring" else ())
        hits.extend(
            f"{rel}:{_line(start, text, match.start())}: {kind}: {label}: {match.group(0)!r}"
            for label, pattern in rules
            for match in pattern.finditer(text)
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
        "A docstring or comment records who decided a change or why a claim went. "
        "Describe the change and its guards instead:\n" + "\n".join(hits)
    )


def test_scope_covers_migrations_seed_data_and_tests() -> None:
    rels = {_ids(path) for path in scoped_files()}
    assert "app/seed_data.py" in rels
    assert "app/api/v1/cv.py" in rels
    assert any(rel.startswith("alembic/versions/") for rel in rels)
    assert any(rel.startswith("tests/") for rel in rels)
    assert "tests/test_docstring_provenance.py" not in rels


def _hit(text: str, migration: bool = False) -> bool:
    rules = _COMPILED + (_COMPILED_MIGRATION if migration else ())
    return any(pattern.search(text) for _, pattern in rules)


# Synthetic phrasings of each kind of note the rule keeps out.
_FLAGGED = (
    "Applied after the career-plan review.",
    "Decided in the planning session of 2020-01-01.",
    "See the review session 2020-01-01 notes.",
    "Per the data requirements (2020-01-01).",
    "Signed off by the owner.",
    "Approved by the owner before release.",
    "The owner rejected the draft.",
    "An owner-approved rewrite.",
    "Owner directive: be brief.",
    "Owner, 2020-01-01: keep it short.",
    "The owner's 2020-01-01 review.",
    "Per the owner's decision.",
    "Apply the owner's two-line rule here.",
    "Final review verdict.",
    "Uses the approved wording.",
    "Checked against the claims register.",
    "The register's preferred framing.",
    "Gated by the tier map.",
    "A claim-gated term.",
    "This was an overclaim.",
    "Under-claiming is fine.",
    "Unbacked rows are deleted.",
    "Drops the unearned items.",
    "Shows an unfalsifiable number.",
    "Lists the strongest claim first.",
    "Sorted by strength order.",
    "Keeps an honest pair.",
    "Pick the vaguest label.",
    "No work anywhere backs the term.",
    "Fixes defect #7.",
    "See the quiz notes.",
    "Compare it with the real CV.",
    "Fits a 2-page layout.",
    "The reviewer ran it himself.",
)

# Engineering notes the rule must leave alone, including the kinds of owner
# mention this repository keeps on purpose.
_ALLOWED = (
    "Guarded on the exact previous value, so an admin edit is never trampled.",
    "Keyed on start month because the DB and the JSON disagree on company names.",
    "An EMPTY table is a no-op: fresh databases are seeded by seed_data.py instead.",
    "The owner's own CMS sessions are not visitor traffic.",
    "The payload carries the owner's private contact, so authorization comes first.",
    "If the owner already created the row by hand, the owner's row wins.",
    "Blank by default; the owner fills email/phone through the admin CV form.",
    "A visitor hits the owner's entry -> LRU bump.",
    "Public-surface rule: describe the domain generically.",
    "Regression for the 2026-07 S2 review.",
    "Verified public 2026-08-29 with an unauthenticated call.",
    "Downgrade is a deliberate no-op: the deleted rows are not recorded here.",
)


@pytest.mark.parametrize("text", _FLAGGED)
def test_rule_flags_provenance_and_claim_review_phrasing(text: str) -> None:
    assert _hit(text), f"no rule matched: {text!r}"


@pytest.mark.parametrize("text", _ALLOWED)
def test_rule_leaves_engineering_notes_alone(text: str) -> None:
    assert not _hit(text, migration=True), f"a rule matched: {text!r}"


def test_private_contact_field_is_flagged_only_in_migration_docstrings() -> None:
    text = "Private contact (email / phone / personnummer) stays blank."
    assert _hit(text, migration=True)
    assert not _hit(text)


def test_a_phrase_wrapped_across_lines_still_matches() -> None:
    assert _hit("Signed\n    off by the\n    owner.")
