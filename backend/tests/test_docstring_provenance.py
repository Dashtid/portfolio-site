"""Docstrings and comments describe the change, not where it came from.

A style rule for the files where planning notes tend to collect: every
migration under alembic/versions, every module under app/ and the test suite.
A docstring or comment there says what the code does to which tables, columns
and rows, and which guard conditions make it safe to re-run. It does not
credit a change to a person, put a date on a person, a session or a
requirements document, number a defect, count a document's pages, cite notes
kept outside this repository, or use a phrase or name a repository whose
digest is listed below.

Only comments (tokenize) and docstrings (ast) are scanned. Code, string data
and identifiers are out of scope, so test data never trips the rule. Each
docstring and each block of consecutive comment lines meets two kinds of check:

- ``_PATTERNS``: regular expressions, matched case-insensitively. Their only
  quantifiers sit on single tokens or on one bounded group, so matching stays
  linear in the size of a file, and words are joined by ``\\s+`` or
  ``[\\s-]+``, so a phrase that wraps onto the next line still matches.
- ``_HASHED``: SHA-256 digests of lowercased terms, found with
  ``tests.hashed_terms`` after every apostrophe in the text has become a
  space, so a possessive ``x's`` is the two-word candidate ``x s``. Only the
  digests are kept in this repository.
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
    "dated requirements citation": re.compile(
        r"\brequirements,?\s+\(?\d{4}-\d{2}-\d{2}\b", re.IGNORECASE
    ),
    "numbered defect": re.compile(r"\bdefect\s+#\d", re.IGNORECASE),
    "page count": re.compile(r"\b\d+-page\b", re.IGNORECASE),
}

# label -> digests of lowercased terms, matched against every docstring and
# comment block. The repository names gain one spelling: one name in
# OTHER_REPO_DIGESTS with a space or a line break in place of its hyphen.
_HASHED: dict[str, frozenset[str]] = {
    "repository name": hashed_terms.EXCLUDED_REPO_DIGESTS
    | hashed_terms.OTHER_REPO_DIGESTS
    | frozenset({"9f48a1a2dfc6fa12f2c7576ccf94bb38ccbf1e384cd6ba49d2d2b59800724c1a"}),
    "listed phrase": frozenset(
        {
            "05edab2681bdf16b426847c04372fa0d96cb9e33d334128b066b11135e9eb7b3",
            "10571bbf66ef64493545d9d3ced9098bc8f07ea0bcb7abbbbce68cae52a35b31",
            "179f28b3287806c52d6de92104247f1c8dc77b4d5370653556381dd565c672ef",
            "1e3f7455d5823bce8f8f23b36b79266398c9cb4547a38f68810d3ba67a66b4f7",
            "2021a928c4d56ab83c9bf395f26dd2de2dc85d7316c105192f7ac77c788b9b35",
            "20a977ea3c9c8edc68c4f107d9905095d664b0ac200ad98088cb766c1cf6f7e2",
            "2199d345945e6a6854524089ada9eb66b9125bbf498b3f456255c88eae0b415c",
            "21af263d01f94887492818e28cd0b3dd0dafaa280e98be0aed029d200e202700",
            "2212f2021ed3fb090ebc9ffe830832349e89e89f8682a0254229f8c498d70817",
            "25ac26f6d809acce3bf36f1e290bbf6bc6f33a3768bee18adf2a571caa4fa24d",
            "25e2eb1e9fb9f53e0c643f87fbca010c07a4daef0aed4b7919fe98f436065cce",
            "25f92f11854bf7e46bf7489cf856694770d0555503dfdd1c995a9818977f238f",
            "26bf5c6c71e457dfcd15763b32cffa3b8ae9f8cea591348e0e200092e1918dca",
            "2fdf88e1d523c24491ffe40b768f313b7db6e13938116d11a60af4939ba697e2",
            "30e5e6b0f43a98ec1ea58342d771924c126efdb945491a358eea0c0b408d7c34",
            "3d28dd1666516e55bfd41481085f5d320a8031a239284ad732542d940528ab5e",
            "3f3c942dd1dd983bb5f0ae376178dcf7152845493ed3e73ad652af6f9050cd86",
            "3fd00a42816b40e446d851b4fb0397b32e049863b038eb9ecc6d13a27ff81f7f",
            "442c621dafad2a69126dfd65d498ed9579f821696023e2c70ce9fc944d6ae47f",
            "48e5014c86e320b924e492db6b182a56592a750067d63147c562c146c881e76d",
            "4ab146662af54e68a773966cfefc8d8644e9113c4fd5777dc7566d2f89a6bfdf",
            "4b509922fab88aa57cfbc898a4b18c5e41530fc4c7b63e77b211ff133017ed8c",
            "4c67f117f2bb7bbcf493d0572cac4f194a43f5e26d7eedb6aea92ec413b3a6b2",
            "4cea5b55fd1653f8dd42e21225a48dc3c52532c9465255e67a96eebe50bb3e99",
            "554db15b0148a9f57768d819105278bfd1cb6ce20336360086f00ebf4a005dc6",
            "598de6843395d5293ee07107bb8da3552bfe2be35b665f023db9922aeca6ba95",
            "5bcd29c2078952759bdbf596d330e44f04e18203c8639ad927d030ffcd6d1574",
            "6017db77508455af060a70184eee6e9fd2ce6c552cc0c66f5b518f691e31c9b4",
            "6285e3f8a58093d2a59d562cd63f18a513dfd0b2fb4ec299bba90be5223ac9ea",
            "6a9864e89727629f3f86304a7206d6f41d978624d7108602f1201652640c8ea1",
            "6c1418e25df0ba8510fdc4295dfe7992e51e3226a00f79b0c6774f78b090a522",
            "6e0c8f4ead3a964710fc173050465de8665574b6d3a2a003e1ac5bec766d79cd",
            "6ea8eec0a9489bd0bd760715b4cdcfbf63a267f626cb0a43013f2f5275a5f130",
            "77fc64abb49904d2230744ff80ebb8a99f17fc817bb3e0e82d9aeb8671c55700",
            "79e8549e044e9ef387ef64c2f73e3969df352a029ae9cfc6d7dca122eec73d15",
            "7c24992cc868eb8169552574c996f8ba934da935672669a6cb8d4146adb2a9e5",
            "7cf9ffe2035bbe956c4f7e16fc17b7b3c594094cfb286b7a18714f76a723f72c",
            "7e1b0ab8aacd529771afd53a6f772dbd477451635a68881d5d2fb4e12de9de89",
            "8e13ec08c74a0787c09bce3c14f19e3f64ee8305d1692fbecc455830dfda01e4",
            "8ec673e49ff741b8182276c2143add071a65c7e9c6e03b9ac3a7d61879f89d5f",
            "936b156d98f98ab83da9fec1f28d9f958a2543284e9fad8e9da1e2d8c94c5ec6",
            "97303992b996ede0d37e3b874855569a630d6e0d68d645af81c37c9c2e8ac561",
            "9d98ce221dd52eccf27cad6a01bcd49b14d3d718a9eeeb3be94f0e231a5787ae",
            "a2caabf56797ef09362c0073022cee0d85e7520b52153d5dc50ec6e14af658ee",
            "a39f78ba9d55a8c2848b09415330d2361a0f8f50302939df89940a5021dc15d8",
            "a7c4c0f437e2c720199c4d405263870bfc829ef628ab4324b6434d0e7404c25d",
            "abab23fe0d52b33d69368843280056b40ac4164657efefb460eb27ca5c242d50",
            "ac34216cbde40b0c58b601a5f6b36730b709147870f0667183ae6b8fc788f29c",
            "ae5666bb418906e0e2b2f98a4891edebf524aec334d70a35e1d74469e92628c0",
            "b1084333c21142b3b458fec970e8e8c54ad70fbe7cb241d7311ab75bb0141b4c",
            "b1753997b3814641b1bff3aa1a232b0628ac2912d9456c71dfbb22d6d6ffaefc",
            "b473fa69a87a0240cc0a3d6262f44e14a71a39f0fbc3dbaa3130bfe29b3e43a8",
            "b53c244ae458c8109e67f6c84e87fbd3b3af932b8dd9d3c09898b2d365636374",
            "b53f0a4c5810f26d3be797a91e2d632d07b17a2d5c66b825ad51f8dfeb0351b4",
            "b61b5440870526b18c6e955d1f899382bfbbbecad18514ca9b433010d372f6eb",
            "b731e1ccf1dec6c30623e4aba3370f191d8ed9d2f02cf5a46cd6a8ccfa813abe",
            "b84e4c5300f8c957d3d451f3dc3e35b8a89e5d23b49f377c02510d69b970baaf",
            "bc23ef1b68761a26f1e4988e9d5953d8355470abebd063ceedec2afb0ebefc5f",
            "bd1e0c1722a94aa28be93159b727197076650edb1eccdaee6c4b8737f0d2594d",
            "c1b30cdbc480c81fc9ea0f670d252d9aef2e591d85c89eb965c649218497d468",
            "c1c7b8e2062d7db98d018b4859c6bbf71554448ba602628536ec21acfee4e51d",
            "c59b4767cee69599d0f7adbef0c4eac3b39b12b83d96aaef3450635981bad3f3",
            "c6dcee8df935d1effff271a0ba7d2d9a52bd861c4902e3f95ae44fad1c0da9d5",
            "c8dff29e825b55a345619a2edc32eedd0f702097b098e5b695f110f3d16f4c24",
            "ca13786620feb8a855ed4cc5dc1dd9f36f604369ac525d69a947560763bbf811",
            "cacfb56b19719cf061c8e781313850b7215a2a8afa3d277dd2cba2124c00c3e0",
            "d30184e4ce26e298c0447514cba323865200d70ded28310e72383ef0c04557aa",
            "d3119dc7d16ef365bb313d41ba50892c7b737227240cabf45429f4505530d594",
            "d6cbc9c95d9e772ce34cc2de12c95653e44e7075e860766c69576b1cba9d0595",
            "dd09065a1f077850496ff4451e1c6b0d90bde2fac12cab92d38a3f0ecff0fc13",
            "e0f219ecde02e968b042c4441fc1a3ed70d2dc15a15e4774650689b83587c2c0",
            "e3f607619ba63696f9ef2f76990c33a11ee0c0ed3df52b5b40cb414121982037",
            "e67e0a4c6e1bd9a7739ad4899cbe3d014f04df2019de7db77c2fb2a6ac9dcedc",
            "ebd3b3b2f8069ff0b67117317361bf0fbaeae0136153b68e4c5c159a44000168",
            "ec3f23e90612a5c745eef868d7d3b0a52e09a752cc905aa2e63f29a799b18448",
            "f0d01c91ac8fec8470016b3dc57726a6e6447380427a1db9771be10c0f2ffd6d",
            "f49e2745fd542bb44bb8e42bb92fb4f5585f3fb2581534b72b480eb032d632b1",
            "f69534d3174e877165136998bba4c628ca6e62040787fcd4ca5f5afb09935c0d",
            "fcac9e6a55ff02190279692da1b7811cbbfb7af6676a923b7c5175937319f63b",
            "fd2e1994acaa6ff6f9554a5da33b456badccd2c42cd86c87050ace6c7aee15c8",
            "fd8d1fc8e06d9d9a0b6c7c5be46d9d772ae4d1170239c69a428b8fb9b962dbdd",
        }
    ),
}

# The straight and the typographic apostrophe; each becomes a space before the
# digests are matched.
_APOSTROPHE = re.compile("['\N{RIGHT SINGLE QUOTATION MARK}]")

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
    # One character for one, so an offset in `words` is the same offset in `text`.
    words = _APOSTROPHE.sub(" ", text)
    spans = {span: hashed_terms.digest(span) for span in set(hashed_terms.candidates(words))}
    hits.extend(
        (label, _offset(words, span), span)
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
        "A docstring or comment credits a change to a person, dates a person, a "
        "session or a requirements document, numbers a defect, counts pages, or "
        "carries a listed term. Describe the change and its guards instead:\n" + "\n".join(hits)
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
        "repository name": 8,
        "listed phrase": 81,
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


def test_a_dated_requirements_citation_a_defect_number_and_a_page_count_are_flagged() -> None:
    day = date(2000, 1, 1).isoformat()
    assert _flags(f"Per the data requirements ({day}).")
    assert _flags(f"requirements, {day}")
    assert _flags("Fixes defect #7.")
    assert _flags("Fits a 2-page layout.")
    assert not _flags(f"requirements.txt was compiled on {day}.")
    assert not _flags("A defect in the parser.")
    assert not _flags("Page 2 of the export.")


def test_an_apostrophe_becomes_a_space_before_the_digests_are_matched() -> None:
    hashed = {"listed phrase": frozenset({hashed_terms.digest("example s")})}
    hit = [("listed phrase", 4, "example s")]
    assert _unit_hits("The example's note.", hashed) == hit
    assert _unit_hits("The example\N{RIGHT SINGLE QUOTATION MARK}s note.", hashed) == hit
    assert _unit_hits("The examples note.", hashed) == []


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
