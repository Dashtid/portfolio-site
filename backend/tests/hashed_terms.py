"""Match text against SHA-256 digests of lowercased terms.

A term list kept as digests can be checked against text without the terms
being readable in this repository. ``candidates`` lowercases the text,
collapses every run of whitespace to one space and splits it into words (runs
of a-z and 0-9). Every run of 1 to ``MAX_WORDS`` consecutive words joined only
by ``.``, ``_``, ``/``, ``-`` or a space is a candidate, with its separators
kept as written. A term is therefore found on its own, inside a longer
hyphenated or dotted token, after an ``owner/`` prefix and before a ``.git``
suffix, but not inside a longer word.

frontend/scripts/hashedTerms.mjs runs the same algorithm over the baked pages
and the tracked tree, and carries the same ``EXCLUDED_REPO_DIGESTS`` and
``OTHER_REPO_DIGESTS``.
"""

import hashlib
import re
from collections.abc import Iterable, Iterator

MAX_WORDS = 8
"""Longest term, in words, that a candidate can match."""

_RUN = re.compile(r"[a-z0-9]+(?:[._/ -]+[a-z0-9]+)*")
_SEPARATOR = re.compile(r"([._/ -]+)")

EXCLUDED_REPO_DIGESTS: frozenset[str] = frozenset(
    {
        "3deec02d5707093b099ddfd80276066a84a5acbff860e5d3be87e88faa60aa23",
        "7e48c7b23b459c446e01a5cf805f95bd6ef268933a2c00a349c33d829a50a6ac",
        "8f452d3012fe2f0d1e4deb459db896dd2124b242ea3e1b43f99ba0353fa0ba4a",
        "cada8352d32b8c4bb62c801b1cfb46d7d6c9e03c9107caf4dce40d1c3c52a633",
        "dadded746f1d20cb34cc7eb59726ec80cac6d273bc12394b5ab491d2cefdb645",
    }
)
"""Digests of the repository names excluded from the public dashboard."""

OTHER_REPO_DIGESTS: frozenset[str] = frozenset(
    {
        "13c59540372a16e775ade0189e39462ad2a91e1c43e3f2d806d8eed980150411",
        "74a101de23165892589d74647e0423eb2ae50265920554e747248cb148d8cbe3",
    }
)
"""Digests of two more repository names, which are not dashboard entries."""


def digest(term: str) -> str:
    """SHA-256 hex digest of ``term``, lowercased."""
    return hashlib.sha256(term.lower().encode("utf-8")).hexdigest()


def candidates(text: str) -> Iterator[str]:
    """Every run of 1 to MAX_WORDS joined words in ``text``, lowercased."""
    for run in _RUN.findall(" ".join(text.lower().split())):
        parts = _SEPARATOR.split(run)  # word, separator, word, ...
        for start in range(0, len(parts), 2):
            span = parts[start]
            yield span
            for end in range(start + 2, min(len(parts), start + 2 * MAX_WORDS - 1), 2):
                span += parts[end - 1] + parts[end]
                yield span


def find(text: str, digests: Iterable[str]) -> list[str]:
    """The candidates of ``text`` whose digest is in ``digests``, sorted and unique."""
    wanted = frozenset(digests)
    return sorted({c for c in candidates(text) if digest(c) in wanted})
