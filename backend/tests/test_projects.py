"""
Tests for projects API endpoints
"""

from typing import Any

from fastapi.testclient import TestClient


def test_get_projects_public(client: TestClient):
    """Test getting projects without authentication."""
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_project_requires_auth(client: TestClient):
    """Test that creating project requires authentication."""
    project_data = {
        "name": "Test Project",
        "description": "Test description",
        "technologies": ["Python", "FastAPI"],
        "github_url": "https://github.com/test/project",
        "live_url": "https://example.com",
        "order_index": 1,
    }
    response = client.post("/api/v1/projects/", json=project_data)
    # HTTPBearer returns 403 when no Authorization header is present
    assert response.status_code == 403


def test_create_project_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test creating project with database-backed authentication."""
    project_data = {
        "name": "Test Project",
        "description": "A test project description",
        "technologies": ["Python", "FastAPI", "Vue.js"],
        "github_url": "https://github.com/test/project",
        "live_url": "https://example.com",
        "order_index": 1,
    }
    response = client.post(
        "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Project"
    assert data["description"] == "A test project description"
    assert data["technologies"] == ["Python", "FastAPI", "Vue.js"]
    assert data["github_url"] == "https://github.com/test/project"
    assert data["live_url"] == "https://example.com"
    assert "id" in data


def test_get_project_by_id(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test getting a specific project by ID."""
    # First create a project
    project_data = {
        "name": "Project to Get",
        "description": "A project to retrieve",
        "technologies": ["Python"],
        "order_index": 1,
    }
    create_response = client.post(
        "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Get the project
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Project to Get"


def test_update_project_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test updating a project with database-backed authentication."""
    # Create a project first
    project_data = {
        "name": "Original Project",
        "description": "Original description",
        "technologies": ["Python"],
        "github_url": "https://github.com/original/project",
        "order_index": 1,
    }
    create_response = client.post(
        "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Update the project
    update_data = {
        "name": "Updated Project",
        "description": "Updated description with more details",
        "technologies": ["Python", "FastAPI", "PostgreSQL"],
        "github_url": "https://github.com/updated/project",
        "live_url": "https://updated.example.com",
        "order_index": 2,
    }
    response = client.put(
        f"/api/v1/projects/{project_id}", json=update_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Project"
    assert data["description"] == "Updated description with more details"
    assert data["technologies"] == ["Python", "FastAPI", "PostgreSQL"]
    assert data["order_index"] == 2


def test_delete_project_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test deleting a project with database-backed authentication."""
    # Create a project first
    project_data = {
        "name": "Project to Delete",
        "description": "Will be deleted",
        "technologies": ["Test"],
        "order_index": 99,
    }
    create_response = client.post(
        "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    # Delete the project
    response = client.delete(
        f"/api/v1/projects/{project_id}", headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/projects/{project_id}")
    assert get_response.status_code == 404


def test_project_validation(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test project field validation."""
    # Missing required fields (name is required)
    invalid_project = {"description": "Missing name"}
    response = client.post(
        "/api/v1/projects/", json=invalid_project, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 422


def test_get_project_not_found(client: TestClient):
    """Test getting a non-existent project."""
    response = client.get("/api/v1/projects/nonexistent-project-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_update_project_not_found(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test updating a non-existent project."""
    update_data = {
        "name": "Updated Project",
        "description": "Updated description",
        "order_index": 1,
    }
    response = client.put(
        "/api/v1/projects/nonexistent-id", json=update_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 404


def test_delete_project_not_found(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test deleting a non-existent project."""
    response = client.delete(
        "/api/v1/projects/nonexistent-id", headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 404


def test_update_project_requires_auth(client: TestClient):
    """Test that updating project requires authentication."""
    update_data = {
        "name": "Updated Project",
        "description": "Updated description",
        "order_index": 1,
    }
    response = client.put("/api/v1/projects/some-id", json=update_data)
    # HTTPBearer returns 403 when no Authorization header is present
    assert response.status_code == 403


def test_delete_project_requires_auth(client: TestClient):
    """Test that deleting project requires authentication."""
    response = client.delete("/api/v1/projects/some-id")
    # HTTPBearer returns 403 when no Authorization header is present
    assert response.status_code == 403


def test_get_projects_empty_list(client: TestClient):
    """Test that projects returns empty list when none exist."""
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_project_ordering(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test that projects are returned ordered by order_index."""
    # Create projects with different order_index values
    projects = [
        {"name": "Project C", "description": "Third", "technologies": ["Test"], "order_index": 3},
        {"name": "Project A", "description": "First", "technologies": ["Test"], "order_index": 1},
        {"name": "Project B", "description": "Second", "technologies": ["Test"], "order_index": 2},
    ]

    for project_data in projects:
        response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201

    # Get all projects
    response = client.get("/api/v1/projects/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Verify ordering
    assert data[0]["name"] == "Project A"
    assert data[1]["name"] == "Project B"
    assert data[2]["name"] == "Project C"
