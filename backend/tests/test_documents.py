"""
Tests for documents API endpoints
"""

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
