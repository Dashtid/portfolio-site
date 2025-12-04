"""
Tests for documents API endpoints
"""

import pytest
from fastapi.testclient import TestClient


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

    def test_documents_endpoint_method_not_allowed(self, client: TestClient):
        """Test POST to documents endpoint returns 405."""
        response = client.post("/api/v1/documents/", json={"title": "Test"})
        assert response.status_code == 405

    def test_documents_delete_not_allowed(self, client: TestClient):
        """Test DELETE to documents endpoint returns 405."""
        response = client.delete("/api/v1/documents/some-id")
        assert response.status_code == 405

    def test_documents_put_not_allowed(self, client: TestClient):
        """Test PUT to documents endpoint returns 405."""
        response = client.put("/api/v1/documents/some-id", json={"title": "Test"})
        assert response.status_code == 405


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

        # Test that HTTPException is raised with 500 status
        import asyncio

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_documents(mock_db))

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

        # Test that HTTPException is raised with 500 status
        import asyncio

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_document("test-id", mock_db))

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

        import asyncio

        with pytest.raises(HTTPException) as exc_info:
            asyncio.run(get_document("nonexistent-id", mock_db))

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

        import asyncio

        result = asyncio.run(get_document("valid-id", mock_db))
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

        import asyncio

        result = asyncio.run(get_documents(mock_db))
        assert result == mock_docs
        assert len(result) == 2
