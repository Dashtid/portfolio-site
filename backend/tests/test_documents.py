"""
Tests for documents API endpoints
"""

from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient


def _make_mock_request() -> Request:
    """Build a minimal Request instance for direct endpoint calls.

    The rate-limit decorator unwraps `request` from function args, so tests
    that invoke endpoint functions directly need a real Request object. The
    scope must include `path` (slowapi reads it) and `app` (so the state lookup
    can resolve even though we skip the actual rate-limit check path).
    """
    from unittest.mock import MagicMock

    mock_app = MagicMock()
    mock_app.state.limiter = None  # Forces slowapi to skip the check
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/documents/",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "query_string": b"",
        "app": mock_app,
    }
    return Request(scope)


def test_get_documents_list(client: TestClient):
    """Test getting all documents returns a list."""
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_document_not_found(client: TestClient):
    """Test getting non-existent document returns 404."""
    response = client.get("/api/v1/documents/nonexistent-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_document_invalid_id(client: TestClient):
    """Test getting document with invalid ID format."""
    response = client.get("/api/v1/documents/invalid-uuid-format")
    # Should return 404 since document doesn't exist
    assert response.status_code == 404


def test_documents_endpoint_returns_empty_list_initially(client: TestClient):
    """Test that documents endpoint returns empty list when no documents exist."""
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # In a fresh test database, there should be no documents
    assert len(data) == 0


def test_download_document_not_found(client: TestClient):
    """Test downloading non-existent document returns 404."""
    response = client.get("/api/v1/documents/nonexistent-id/download")
    assert response.status_code == 404


def test_documents_response_structure(client: TestClient):
    """Test that documents endpoint returns proper structure."""
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    # Verify it's a JSON array
    data = response.json()
    assert isinstance(data, list)


class TestDocumentsEndpoints:
    """Extended tests for documents API endpoints."""

    def test_documents_router_exists(self):
        """Test that documents router is properly configured."""
        from app.api.v1.endpoints.documents import router

        assert router is not None

    def test_document_model_exists(self):
        """Test that Document model is importable."""
        from app.models.document import Document

        assert Document is not None

    def test_document_schemas_exist(self):
        """Test that document schemas are importable."""
        from app.schemas.document import DocumentCreate, DocumentResponse, DocumentUpdate

        assert DocumentCreate is not None
        assert DocumentResponse is not None
        assert DocumentUpdate is not None

    def test_get_documents_returns_list(self, client: TestClient):
        """Test GET /documents/ returns a list."""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_get_single_document_not_found(self, client: TestClient):
        """Test GET /documents/{id} returns 404 for non-existent document."""
        response = client.get("/api/v1/documents/non-existent-id-12345")
        assert response.status_code == 404

    def test_documents_logger_exists(self):
        """Test that documents module has logger configured."""
        from app.api.v1.endpoints.documents import logger

        assert logger is not None


class TestDocumentsEdgeCases:
    """Edge case tests for documents API."""

    def test_get_documents_empty_list(self, client: TestClient):
        """Test that empty database returns empty list."""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_document_with_valid_uuid_format(self, client: TestClient):
        """Test getting document with valid UUID format but non-existent."""
        response = client.get("/api/v1/documents/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_document_with_special_characters_id(self, client: TestClient):
        """Test getting document with special characters in ID."""
        response = client.get("/api/v1/documents/test!@%23$%special")
        assert response.status_code == 404

    def test_documents_response_is_json(self, client: TestClient):
        """Test that documents endpoint returns JSON content type."""
        response = client.get("/api/v1/documents/")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_get_document_by_id_returns_json(self, client: TestClient):
        """Test that document endpoint returns JSON content type."""
        response = client.get("/api/v1/documents/nonexistent-id")
        assert response.status_code == 404
        assert "application/json" in response.headers.get("content-type", "")

    def test_documents_post_without_auth_rejected(self, client: TestClient):
        """ADMIN-04: POST is admin-only; anonymous -> 401/403, not 405."""
        response = client.post("/api/v1/documents/", json={"title": "Test"})
        assert response.status_code in (401, 403)

    def test_documents_delete_without_auth_rejected(self, client: TestClient):
        """ADMIN-04: DELETE is admin-only; anonymous -> 401/403, not 405."""
        response = client.delete("/api/v1/documents/some-id")
        assert response.status_code in (401, 403)

    def test_documents_put_without_auth_rejected(self, client: TestClient):
        """ADMIN-04: PUT is admin-only; anonymous -> 401/403, not 405."""
        response = client.put("/api/v1/documents/some-id", json={"title": "Test"})
        assert response.status_code in (401, 403)


class TestDocumentsAdminCrud:
    """ADMIN-04: end-to-end CRUD round-trips for the admin document API."""

    _CREATE_PAYLOAD = {
        "id": "test-doc-1",
        "title": "Master Thesis",
        "description": "A paper on something academic",
        "document_type": "thesis",
        # Schema's validate_safe_url requires a leading slash or http(s)://.
        "file_path": "/documents/test.pdf",
        "file_size": 4096,
        "file_url": "/static/documents/test.pdf",
        "published_date": "2024-05-01",
        "order_index": 1,
    }

    def test_admin_can_create_document(self, client: TestClient, admin_user_in_db: dict):
        response = client.post(
            "/api/v1/documents/",
            json=self._CREATE_PAYLOAD,
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 201
        body = response.json()
        assert body["title"] == "Master Thesis"
        assert body["file_url"].endswith("/test.pdf")

    def test_duplicate_id_rejected(self, client: TestClient, admin_user_in_db: dict):
        client.post(
            "/api/v1/documents/",
            json=self._CREATE_PAYLOAD,
            headers=admin_user_in_db["headers"],
        )
        response = client.post(
            "/api/v1/documents/",
            json=self._CREATE_PAYLOAD,
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 409

    def test_admin_can_update_document(self, client: TestClient, admin_user_in_db: dict):
        client.post(
            "/api/v1/documents/",
            json=self._CREATE_PAYLOAD,
            headers=admin_user_in_db["headers"],
        )
        response = client.put(
            "/api/v1/documents/test-doc-1",
            json={"title": "Renamed Thesis", "order_index": 5},
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        body = response.json()
        assert body["title"] == "Renamed Thesis"
        assert body["order_index"] == 5

    def test_update_nonexistent_returns_404(self, client: TestClient, admin_user_in_db: dict):
        response = client.put(
            "/api/v1/documents/does-not-exist",
            json={"title": "Renamed"},
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 404

    def test_admin_can_delete_document(self, client: TestClient, admin_user_in_db: dict):
        client.post(
            "/api/v1/documents/",
            json=self._CREATE_PAYLOAD,
            headers=admin_user_in_db["headers"],
        )
        response = client.delete(
            "/api/v1/documents/test-doc-1", headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 204
        # Confirm it's gone.
        get_response = client.get("/api/v1/documents/test-doc-1")
        assert get_response.status_code == 404

    def test_delete_nonexistent_returns_404(self, client: TestClient, admin_user_in_db: dict):
        response = client.delete(
            "/api/v1/documents/does-not-exist", headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 404


class TestDocumentsAdminUpload:
    """ADMIN-04: PDF upload endpoint round-trip + rejection cases."""

    def _make_pdf_bytes(self, size: int = 64) -> bytes:
        # Minimal PDF magic + filler. The endpoint accepts the file based
        # on the MIME type the client claims, not magic-byte sniffing —
        # tests just need a payload the right shape for size assertions.
        return b"%PDF-1.4\n" + b"0" * size + b"\n%%EOF"

    def test_admin_upload_pdf_succeeds(self, client: TestClient, admin_user_in_db: dict, tmp_path):
        # Run the upload inside the tmp_path CWD so the test doesn't
        # leave files in the repo's static/documents folder.
        import os  # noqa: PLC0415

        cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            payload = self._make_pdf_bytes(128)
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("paper.pdf", payload, "application/pdf")},
                headers=admin_user_in_db["headers"],
            )
        finally:
            os.chdir(cwd)

        assert response.status_code == 200
        body = response.json()
        # Uploads are served from the /media mount (settings.UPLOAD_DIR,
        # the persistent volume in prod) — not /static, which serves
        # image-baked assets only.
        assert body["file_url"].startswith("/media/")
        assert body["file_url"].endswith(".pdf")
        assert body["file_size"] == len(payload)
        assert body["original_filename"] == "paper.pdf"

    def test_upload_without_auth_rejected(self, client: TestClient):
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("paper.pdf", b"%PDF-1.4\n", "application/pdf")},
        )
        assert response.status_code in (401, 403)

    def test_upload_rejects_non_pdf_content_type(self, client: TestClient, admin_user_in_db: dict):
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("paper.txt", b"plain text", "text/plain")},
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 415

    def test_upload_rejects_non_pdf_extension(self, client: TestClient, admin_user_in_db: dict):
        """Even with the right MIME type, a non-.pdf filename is rejected.

        Belt-and-braces — catches a forged content-type alongside a
        ``.exe`` filename, which Windows clients would happily try to
        execute when downloaded.
        """
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("payload.exe", b"%PDF-1.4\n", "application/pdf")},
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 415

    def test_upload_rejects_oversize_file(
        self, client: TestClient, admin_user_in_db: dict, tmp_path
    ):
        import os  # noqa: PLC0415

        cwd = Path.cwd()
        os.chdir(tmp_path)
        try:
            oversize = b"%PDF-1.4\n" + b"0" * (26 * 1024 * 1024)  # > 25 MB cap
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("big.pdf", oversize, "application/pdf")},
                headers=admin_user_in_db["headers"],
            )
        finally:
            os.chdir(cwd)
        assert response.status_code == 413

    def test_safe_filename_strips_path_traversal(self):
        """Direct unit check on the filename sanitiser.

        Even if a future endpoint passes the raw filename straight to
        ``Path(...) / name``, the sanitiser cannot let ``..\\evil`` through.
        ``Path(...).name`` is the first defence — it discards every
        directory component, so ``../../etc/passwd`` becomes ``passwd``
        before the regex pass runs.
        """
        from app.api.v1.endpoints.documents import _safe_filename  # noqa: PLC0415

        # Each case: (raw input, expected output OR None for "any UUID hex").
        cases = [
            ("../../etc/passwd", "passwd"),
            ("..\\..\\Windows\\System32\\evil.pdf", "evil.pdf"),
            ("with spaces.pdf", "with-spaces.pdf"),
            ("/already/slashed.pdf", "slashed.pdf"),
            ("../../", None),  # collapses to empty; sanitiser falls back to UUID hex
        ]
        for raw, expected in cases:
            cleaned = _safe_filename(raw)
            # Must never contain a path separator or traversal marker.
            assert "/" not in cleaned
            assert "\\" not in cleaned
            assert ".." not in cleaned
            assert cleaned != ""  # never returns empty
            if expected is not None:
                assert cleaned == expected
            else:
                # Empty input falls back to a 32-char UUID hex.
                assert len(cleaned) == 32 and all(c in "0123456789abcdef" for c in cleaned)

    def test_media_mount_missing_file_returns_404(self, client: TestClient):
        """A miss on the /media mount must be a 404, not a 500.

        StaticFiles(check_dir=False) defers its directory-exists check to
        the first request and raises RuntimeError if UPLOAD_DIR is still
        absent; lifespan startup creates the directory so this never
        happens. Regression for the post-deploy 500 on 2026-07-02.
        """
        response = client.get("/media/does-not-exist.pdf")
        assert response.status_code == 404


class TestDocumentsExceptionHandling:
    """Tests for exception handling in documents endpoints."""

    def test_get_documents_database_error_handling(self):
        """Test that database errors are handled in get_documents."""
        from unittest.mock import AsyncMock

        from fastapi import HTTPException

        from app.api.v1.endpoints.documents import get_documents

        # Create a mock db session that raises an exception
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection error")

        mock_request = _make_mock_request()

        # Test that HTTPException is raised with 500 status
        import asyncio

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_documents(mock_request, mock_db))

        assert exc_info.value.status_code == 500
        assert "Failed to fetch documents" in exc_info.value.detail

    def test_get_document_database_error_handling(self):
        """Test that database errors are handled in get_document."""
        from unittest.mock import AsyncMock

        from fastapi import HTTPException

        from app.api.v1.endpoints.documents import get_document

        # Create a mock db session that raises an exception
        mock_db = AsyncMock()
        mock_db.execute.side_effect = Exception("Database connection error")

        mock_request = _make_mock_request()

        # Test that HTTPException is raised with 500 status
        import asyncio

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_document(mock_request, "test-id", mock_db))

        assert exc_info.value.status_code == 500
        assert "Failed to fetch document" in exc_info.value.detail

    def test_get_document_not_found_reraises(self):
        """Test that 404 HTTPException is re-raised properly."""
        from unittest.mock import AsyncMock, MagicMock

        from fastapi import HTTPException

        from app.api.v1.endpoints.documents import get_document

        # Create a mock db session that returns None
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        mock_request = _make_mock_request()

        import asyncio

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_document(mock_request, "nonexistent-id", mock_db))

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    def test_get_document_success_path(self):
        """Test successful document retrieval."""
        from unittest.mock import AsyncMock, MagicMock

        from app.api.v1.endpoints.documents import get_document

        # Create a mock document
        mock_document = MagicMock()
        mock_document.title = "Test Document"

        # Create a mock db session
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_document
        mock_db.execute.return_value = mock_result

        mock_request = _make_mock_request()

        import asyncio

        result = asyncio.run(get_document(mock_request, "valid-id", mock_db))
        assert result == mock_document

    def test_get_documents_success_path(self):
        """Test successful documents list retrieval."""
        from unittest.mock import AsyncMock, MagicMock

        from app.api.v1.endpoints.documents import get_documents

        # Create mock documents
        mock_docs = [MagicMock(), MagicMock()]

        # Create a mock db session
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_docs
        mock_db.execute.return_value = mock_result

        mock_request = _make_mock_request()

        import asyncio

        # Direct calls bypass FastAPI's Query() default extraction; pass
        # explicit skip/limit values so SQLAlchemy gets ints, not Query stubs.
        result = asyncio.run(get_documents(mock_request, mock_db, skip=0, limit=50))
        assert result == mock_docs
        assert len(result) == 2

    def test_get_documents_pagination_params(self):
        """Pagination params are forwarded to the SQL query."""
        from unittest.mock import AsyncMock, MagicMock

        from app.api.v1.endpoints.documents import get_documents

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result

        mock_request = _make_mock_request()

        import asyncio

        asyncio.run(get_documents(mock_request, mock_db, skip=5, limit=10))

        # The compiled select should reflect the offset/limit we passed.
        executed_stmt = mock_db.execute.call_args.args[0]
        compiled = str(executed_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "OFFSET 5" in compiled
        assert "LIMIT 10" in compiled
