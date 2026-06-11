"""
Tests for ``validate_safe_url`` across every Pydantic schema that uses it.

Covers BACKEND-TESTS-04. The shared validator lives in
``app.schemas._validators`` and is wired onto every URL-bearing field across
the company / project / education / document schemas. The risk if it
regresses: an attacker who can write to one of those fields (admin-only,
but an account compromise or a future public form) could store a
``javascript:`` URL that later renders as an ``href``, executing in the
victim's browser when clicked.

We test:
  * Every dangerous URL scheme is rejected (javascript, data, vbscript,
    file, ftp, chrome-extension).
  * Schemes without a scheme separator (no ``://``) are rejected unless
    they start with ``/`` (a relative path).
  * Valid HTTPS/HTTP URLs and relative paths are accepted.
  * Empty string and None are accepted (the field is optional).
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas._validators import SAFE_URL_PATTERN, validate_safe_url
from app.schemas.company import CompanyCreate, CompanyUpdate
from app.schemas.document import DocumentCreate
from app.schemas.education import EducationCreate, EducationUpdate
from app.schemas.project import ProjectCreate, ProjectUpdate

# Concrete payloads pulled from the OWASP XSS filter-evasion cheat sheet and
# the W3C URL spec — every one of these must be rejected by the validator.
DANGEROUS_URLS = [
    "javascript:alert(1)",
    "JavaScript:alert(1)",  # capitalised
    "JAVASCRIPT:alert(1)",
    "data:text/html,<script>alert(1)</script>",
    "data:application/javascript,alert(1)",
    "vbscript:msgbox(1)",
    "VBSCRIPT:msgbox(1)",
    "file:///etc/passwd",
    "file://C:/Windows/System32",
    "ftp://attacker.example.com/payload",
    "chrome-extension://abcd/payload.html",
    "about:blank",
    "tel:+1234567890",
    "mailto:a@b.example",
    # Whitespace tricks and protocol-relative URLs.
    " javascript:alert(1)",
    "java\tscript:alert(1)",
    "//attacker.example.com/payload",  # protocol-relative
    "noschemejustletters",  # no scheme separator at all
]

# These should pass — http(s) URLs, relative paths starting with /, empty/None.
VALID_URLS = [
    "https://example.com",
    "https://example.com/path/to/resource?q=1",
    "http://example.com",
    "/relative/path",
    "/images/foo.png",
    "/a",  # minimum-length relative path
    "",
    None,
]


class TestValidateSafeUrlPure:
    """Direct unit tests on the validator function."""

    @pytest.mark.parametrize("payload", DANGEROUS_URLS)
    def test_rejects_dangerous_url(self, payload):
        """Every known XSS / non-HTTP scheme is rejected with ValueError."""
        with pytest.raises(ValueError, match="HTTP"):
            validate_safe_url(payload, "test_field")

    @pytest.mark.parametrize("payload", VALID_URLS)
    def test_accepts_valid_url(self, payload):
        """Valid HTTP(S) URLs, relative paths, empty/None all round-trip."""
        result = validate_safe_url(payload, "test_field")
        assert result == payload

    def test_pattern_anchors_at_start(self):
        """The regex is anchored at ``^`` — embedding the safe prefix later
        in the string must NOT bypass it.

        e.g. ``javascript:alert(1) //https://safe.example.com`` is
        unsafe but contains the substring ``https://``.
        """
        sneaky = "javascript:alert(1) //https://safe.example.com"
        assert SAFE_URL_PATTERN.match(sneaky) is None

    def test_field_name_in_error_message(self):
        """The thrown ValueError mentions the field name so the API error
        body tells the caller WHICH field was bad."""
        with pytest.raises(ValueError, match="logo_url"):
            validate_safe_url("javascript:alert(1)", "logo_url")


class TestCompanySchemaUrlValidation:
    """All four URL fields on CompanyCreate / CompanyUpdate."""

    URL_FIELDS = ["logo_url", "website", "video_url", "map_url"]

    @pytest.mark.parametrize("field", URL_FIELDS)
    @pytest.mark.parametrize("payload", ["javascript:alert(1)", "data:text/html,<x>"])
    def test_company_create_rejects_dangerous_url(self, field, payload):
        kwargs = {
            "name": "Test Co",
            "title": "Engineer",
            "description": "desc",
            "location": "SE",
            "start_date": date(2020, 1, 1),
            field: payload,
        }
        with pytest.raises(ValidationError):
            CompanyCreate(**kwargs)

    @pytest.mark.parametrize("field", URL_FIELDS)
    def test_company_update_rejects_dangerous_url(self, field):
        with pytest.raises(ValidationError):
            CompanyUpdate(**{field: "javascript:alert(1)"})

    def test_company_create_accepts_safe_url(self):
        c = CompanyCreate(
            name="Test Co",
            title="Engineer",
            description="desc",
            location="SE",
            start_date=date(2020, 1, 1),
            website="https://example.com",
            logo_url="/logos/test.svg",
        )
        assert c.website == "https://example.com"
        assert c.logo_url == "/logos/test.svg"


class TestProjectSchemaUrlValidation:
    """All five URL fields on ProjectCreate / ProjectUpdate."""

    URL_FIELDS = ["github_url", "live_url", "image_url", "video_url", "map_url"]

    @pytest.mark.parametrize("field", URL_FIELDS)
    @pytest.mark.parametrize("payload", ["javascript:alert(1)", "data:text/html,<x>"])
    def test_project_create_rejects_dangerous_url(self, field, payload):
        kwargs = {
            "name": "Test Project",
            "description": "desc",
            "technologies": ["Python"],
            field: payload,
        }
        with pytest.raises(ValidationError):
            ProjectCreate(**kwargs)

    @pytest.mark.parametrize("field", URL_FIELDS)
    def test_project_update_rejects_dangerous_url(self, field):
        with pytest.raises(ValidationError):
            ProjectUpdate(**{field: "javascript:alert(1)"})

    def test_project_create_accepts_safe_urls(self):
        p = ProjectCreate(
            name="Test Project",
            description="desc",
            technologies=["Python"],
            github_url="https://github.com/example/repo",
            live_url="https://example.com",
            image_url="/images/project.png",
        )
        assert p.github_url == "https://github.com/example/repo"
        assert p.image_url == "/images/project.png"


class TestEducationSchemaUrlValidation:
    """Both URL fields on EducationCreate / EducationUpdate."""

    URL_FIELDS = ["logo_url", "certificate_url"]

    @pytest.mark.parametrize("field", URL_FIELDS)
    @pytest.mark.parametrize("payload", ["javascript:alert(1)", "vbscript:msgbox(1)"])
    def test_education_create_rejects_dangerous_url(self, field, payload):
        kwargs = {
            "institution": "Uni",
            "degree": "BSc",
            field: payload,
        }
        with pytest.raises(ValidationError):
            EducationCreate(**kwargs)

    @pytest.mark.parametrize("field", URL_FIELDS)
    def test_education_update_rejects_dangerous_url(self, field):
        with pytest.raises(ValidationError):
            EducationUpdate(**{field: "javascript:alert(1)"})

    def test_education_create_accepts_safe_url(self):
        e = EducationCreate(
            institution="Uni",
            degree="BSc",
            logo_url="https://uni.example/logo.svg",
            certificate_url="/certs/abc.pdf",
        )
        assert e.logo_url == "https://uni.example/logo.svg"
        assert e.certificate_url == "/certs/abc.pdf"


class TestDocumentSchemaUrlValidation:
    """``file_url`` and ``file_path`` on DocumentCreate.

    Note: Document's URL validators raise on None as well (the fields are
    required), so the None-passes behaviour from other schemas does not
    apply here.
    """

    @pytest.mark.parametrize("field", ["file_url", "file_path"])
    @pytest.mark.parametrize("payload", ["javascript:alert(1)", "data:text/html,<x>"])
    def test_document_create_rejects_dangerous_url(self, field, payload):
        kwargs = {
            "id": "test-doc-1",
            "title": "Test Doc",
            "document_type": "paper",
            "file_path": "/docs/test.pdf",
            "file_size": 1024,
            "file_url": "/docs/test.pdf",
        }
        kwargs[field] = payload
        with pytest.raises(ValidationError):
            DocumentCreate(**kwargs)

    def test_document_create_accepts_safe_url(self):
        d = DocumentCreate(
            id="test-doc-1",
            title="Test Doc",
            document_type="paper",
            file_path="/docs/test.pdf",
            file_size=1024,
            file_url="https://cdn.example/test.pdf",
        )
        assert d.file_url == "https://cdn.example/test.pdf"
        assert d.file_path == "/docs/test.pdf"
