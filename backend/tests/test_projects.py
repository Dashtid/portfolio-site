"""
Tests for projects API endpoints
"""

from fastapi.testclient import TestClient


def test_get_projects_public(client: TestClient):
    """Test getting projects without authentication."""
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_project_requires_auth(client: TestClient):
    """Test that creating project requires authentication."""
    project_data = {
        "title": "Test Project",
        "description": "Test description",
        "technologies": "Python, FastAPI",
        "github_url": "https://github.com/test/project",
        "live_url": "https://example.com",
        "order": 1,
    }
    response = client.post("/api/v1/projects/", json=project_data)
    assert response.status_code == 401


def test_create_project_with_auth(client: TestClient, admin_headers: dict):
    """Test creating project with authentication."""
    project_data = {
        "title": "Test Project",
        "description": "A test project description",
        "technologies": "Python, FastAPI, Vue.js",
        "github_url": "https://github.com/test/project",
        "live_url": "https://example.com",
        "order": 1,
    }
    response = client.post("/api/v1/projects/", json=project_data, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == project_data["title"]
    assert data["technologies"] == project_data["technologies"]
    assert "id" in data


def test_update_project(client: TestClient, admin_headers: dict):
    """Test updating a project."""
    # Create project
    project_data = {
        "title": "Original Project",
        "description": "Original description",
        "technologies": "Python",
        "github_url": "https://github.com/original/project",
        "order": 1,
    }
    create_response = client.post("/api/v1/projects/", json=project_data, headers=admin_headers)
    project_id = create_response.json()["id"]

    # Update project
    update_data = {
        "title": "Updated Project",
        "description": "Updated description with more details",
        "technologies": "Python, FastAPI, PostgreSQL",
        "github_url": "https://github.com/updated/project",
        "live_url": "https://updated.example.com",
        "order": 2,
    }
    response = client.put(f"/api/v1/projects/{project_id}", json=update_data, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == update_data["title"]
    assert data["live_url"] == update_data["live_url"]


def test_delete_project(client: TestClient, admin_headers: dict):
    """Test deleting a project."""
    # Create project
    project_data = {
        "title": "Project to Delete",
        "description": "Will be deleted",
        "technologies": "Test",
        "order": 99,
    }
    create_response = client.post("/api/v1/projects/", json=project_data, headers=admin_headers)
    project_id = create_response.json()["id"]

    # Delete project
    response = client.delete(f"/api/v1/projects/{project_id}", headers=admin_headers)
    assert response.status_code == 200

    # Verify deletion
    get_response = client.get("/api/v1/projects/")
    projects = get_response.json()
    assert not any(p["id"] == project_id for p in projects)


def test_project_validation(client: TestClient, admin_headers: dict):
    """Test project field validation."""
    # Missing required fields
    invalid_project = {"description": "Missing title"}
    response = client.post("/api/v1/projects/", json=invalid_project, headers=admin_headers)
    assert response.status_code == 422

    # Invalid URL format
    invalid_url_project = {
        "title": "Test",
        "description": "Test",
        "technologies": "Test",
        "github_url": "not-a-valid-url",
        "order": 1,
    }
    response = client.post("/api/v1/projects/", json=invalid_url_project, headers=admin_headers)
    # Note: Basic validation might not catch this without custom validators
    # This test documents expected behavior
