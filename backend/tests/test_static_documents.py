"""
The PDFs served from backend/static/documents carry no e-mail address.

pdfTeX writes a title page's text into a Flate-compressed content stream, so
an address is invisible to a scan of the raw file. Each PDF is checked in its
raw bytes and in every Flate stream it holds, decompressed.
"""

import re
import zlib
from collections.abc import Iterator
from pathlib import Path

import pytest

DOCUMENTS = Path(__file__).resolve().parents[1] / "static" / "documents"
EMAIL = re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
STREAM = re.compile(rb"(?<!end)stream\r?\n")


def _flate_streams(data: bytes) -> Iterator[bytes]:
    """Every stream body in the file that inflates; other filters are skipped."""
    for match in STREAM.finditer(data):
        end = data.find(b"endstream", match.end())
        if end < 0:
            return
        try:
            yield zlib.decompressobj().decompress(data[match.end() : end])
        except zlib.error:
            continue


def test_the_documents_folder_holds_pdfs():
    assert sorted(DOCUMENTS.glob("*.pdf"))


@pytest.mark.parametrize("pdf", sorted(DOCUMENTS.glob("*.pdf")), ids=lambda path: path.name)
def test_a_served_pdf_carries_no_email_address(pdf: Path):
    data = pdf.read_bytes()
    assert EMAIL.search(data) is None

    inflated = 0
    for body in _flate_streams(data):
        inflated += 1
        assert EMAIL.search(body) is None, f"an e-mail address in a compressed stream of {pdf.name}"
    assert inflated > 0
