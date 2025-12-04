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
    # HTTPBearer returns 401 when no Authorization header is present
    assert response.status_code == 401


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
    response = client.delete(f"/api/v1/projects/{project_id}", headers=admin_user_in_db["headers"])
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
    response = client.delete("/api/v1/projects/nonexistent-id", headers=admin_user_in_db["headers"])
    assert response.status_code == 404


def test_update_project_requires_auth(client: TestClient):
    """Test that updating project requires authentication."""
    update_data = {
        "name": "Updated Project",
        "description": "Updated description",
        "order_index": 1,
    }
    response = client.put("/api/v1/projects/some-id", json=update_data)
    # HTTPBearer returns 401 when no Authorization header is present
    assert response.status_code == 401


def test_delete_project_requires_auth(client: TestClient):
    """Test that deleting project requires authentication."""
    response = client.delete("/api/v1/projects/some-id")
    # HTTPBearer returns 401 when no Authorization header is present
    assert response.status_code == 401


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


class TestProjectEdgeCases:
    """Edge case tests for projects API."""

    def test_create_project_with_all_fields(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating project with all optional fields."""
        project_data = {
            "name": "Full Project",
            "description": "Short description",
            "detailed_description": "Very detailed description here",
            "technologies": ["Python", "FastAPI", "Vue.js"],
            "github_url": "https://github.com/test/full",
            "live_url": "https://full.example.com",
            "image_url": "https://example.com/image.png",
            "video_url": "https://youtube.com/watch?v=123",
            "video_title": "Project Demo",
            "map_url": "https://maps.google.com/?q=test",
            "map_title": "Project Location",
            "featured": True,
            "order_index": 1,
            "responsibilities": ["Task 1", "Task 2"],
        }
        response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Full Project"
        assert data["detailed_description"] == "Very detailed description here"
        assert data["video_url"] == "https://youtube.com/watch?v=123"
        assert data["featured"] is True
        assert data["responsibilities"] == ["Task 1", "Task 2"]

    def test_create_project_minimal_fields(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating project with only required fields."""
        project_data = {"name": "Minimal Project"}
        response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Project"
        assert data["description"] is None
        assert data["technologies"] == []

    def test_update_partial_fields(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test updating only some fields preserves others."""
        # Create project
        project_data = {
            "name": "Partial Update Project",
            "description": "Original description",
            "technologies": ["Python"],
            "github_url": "https://github.com/original",
            "order_index": 5,
        }
        create_response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Update only description
        update_response = client.put(
            f"/api/v1/projects/{project_id}",
            json={"description": "Updated description only"},
            headers=admin_user_in_db["headers"],
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["description"] == "Updated description only"
        assert data["name"] == "Partial Update Project"
        assert data["technologies"] == ["Python"]
        assert data["github_url"] == "https://github.com/original"
        assert data["order_index"] == 5

    def test_project_with_featured_flag(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test creating a featured project."""
        project_data = {
            "name": "Featured Project",
            "featured": True,
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        assert response.json()["featured"] is True

    def test_project_with_company_id(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test creating project linked to a company."""
        project_data = {
            "name": "Company Project",
            "company_id": "00000000-0000-0000-0000-000000000001",
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        assert response.json()["company_id"] == "00000000-0000-0000-0000-000000000001"

    def test_get_project_by_invalid_uuid_format(self, client: TestClient):
        """Test getting project with valid UUID format but non-existent."""
        response = client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_project_response_schema(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test that project response matches expected schema."""
        project_data = {
            "name": "Schema Test Project",
            "description": "Test description",
            "technologies": ["Python"],
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        # Check expected fields exist
        assert "id" in data
        assert "name" in data
        assert "description" in data
        assert "technologies" in data
        assert "github_url" in data
        assert "live_url" in data
        assert "featured" in data
        assert "order_index" in data
        assert "created_at" in data

    def test_project_with_empty_technologies(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating project with empty technologies array."""
        project_data = {
            "name": "No Tech Project",
            "technologies": [],
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        assert response.json()["technologies"] == []

    def test_update_project_clear_optional_field(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test updating project to clear an optional field."""
        # Create project with live_url
        project_data = {
            "name": "Clear Field Project",
            "live_url": "https://example.com",
            "order_index": 1,
        }
        create_response = client.post(
            "/api/v1/projects/", json=project_data, headers=admin_user_in_db["headers"]
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Update to clear live_url
        update_response = client.put(
            f"/api/v1/projects/{project_id}",
            json={"live_url": None},
            headers=admin_user_in_db["headers"],
        )
        assert update_response.status_code == 200
        assert update_response.json()["live_url"] is None
