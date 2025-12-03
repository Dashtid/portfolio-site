"""
Tests for companies API endpoints
"""

from typing import Any

from fastapi.testclient import TestClient


def test_get_companies_unauthenticated(client: TestClient):
    """Test getting companies without authentication should work."""
    response = client.get("/api/v1/companies/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_companies_returns_empty_list_initially(client: TestClient):
    """Test that companies endpoint returns empty list when no companies exist."""
    response = client.get("/api/v1/companies/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_company_not_found(client: TestClient):
    """Test getting a non-existent company returns 404."""
    response = client.get("/api/v1/companies/nonexistent-company-id")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_company_requires_auth(client: TestClient):
    """Test creating company without authentication should fail."""
    company_data = {
        "name": "Test Company",
        "title": "Software Engineer",
        "description": "Test description",
        "order_index": 1,
    }
    response = client.post("/api/v1/companies/", json=company_data)
    # HTTPBearer returns 401 when no Authorization header is present
    assert response.status_code == 401


def test_create_company_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test creating company with database-backed admin authentication."""
    company_data = {
        "name": "Test Company",
        "title": "Software Engineer",
        "description": "Test description",
        "location": "Stockholm, Sweden",
        "start_date": "2023-01-01",
        "order_index": 1,
    }
    response = client.post(
        "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Company"
    assert data["title"] == "Software Engineer"
    assert data["description"] == "Test description"
    assert data["location"] == "Stockholm, Sweden"
    assert "id" in data


def test_get_company_by_id(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test getting a specific company by ID."""
    # First create a company
    company_data = {
        "name": "Company to Get",
        "title": "Developer",
        "description": "A company to retrieve",
        "order_index": 1,
    }
    create_response = client.post(
        "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    company_id = create_response.json()["id"]

    # Get the company
    response = client.get(f"/api/v1/companies/{company_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == company_id
    assert data["name"] == "Company to Get"


def test_update_company_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test updating a company with database-backed authentication."""
    # Create a company first
    company_data = {
        "name": "Original Company",
        "title": "Junior Developer",
        "description": "Original description",
        "order_index": 1,
    }
    create_response = client.post(
        "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    company_id = create_response.json()["id"]

    # Update the company
    update_data = {
        "name": "Updated Company",
        "title": "Senior Developer",
        "description": "Updated description with more details",
        "location": "Gothenburg, Sweden",
        "order_index": 2,
    }
    response = client.put(
        f"/api/v1/companies/{company_id}", json=update_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Company"
    assert data["title"] == "Senior Developer"
    assert data["location"] == "Gothenburg, Sweden"
    assert data["order_index"] == 2


def test_delete_company_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test deleting a company with database-backed authentication."""
    # Create a company first
    company_data = {
        "name": "Company to Delete",
        "title": "Test Role",
        "description": "Will be deleted",
        "order_index": 99,
    }
    create_response = client.post(
        "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    company_id = create_response.json()["id"]

    # Delete the company
    response = client.delete(f"/api/v1/companies/{company_id}", headers=admin_user_in_db["headers"])
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/companies/{company_id}")
    assert get_response.status_code == 404


def test_update_company_not_found(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test updating a non-existent company returns 404."""
    update_data = {
        "name": "Updated Company",
        "title": "Updated Role",
        "description": "Updated description",
        "order_index": 1,
    }
    response = client.put(
        "/api/v1/companies/nonexistent-id", json=update_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 404


def test_delete_company_not_found(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test deleting a non-existent company returns 404."""
    response = client.delete(
        "/api/v1/companies/nonexistent-id", headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 404


def test_update_company_requires_auth(client: TestClient):
    """Test that updating a company requires authentication."""
    update_data = {
        "name": "Updated Company",
        "title": "Updated Role",
        "description": "Updated description",
        "order_index": 1,
    }
    response = client.put("/api/v1/companies/some-id", json=update_data)
    # HTTPBearer returns 401 when no Authorization header is present
    assert response.status_code == 401


def test_delete_company_requires_auth(client: TestClient):
    """Test that deleting a company requires authentication."""
    response = client.delete("/api/v1/companies/some-id")
    # HTTPBearer returns 401 when no Authorization header is present
    assert response.status_code == 401


def test_company_validation(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test company field validation."""
    # Missing required fields (name and title are required)
    invalid_company = {"description": "Missing name and title"}
    response = client.post(
        "/api/v1/companies/", json=invalid_company, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 422


def test_company_ordering(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test that companies are returned in correct order."""
    # Create multiple companies with different orders
    companies = [
        {
            "name": "Third Company",
            "title": "Role 3",
            "description": "Description 3",
            "order_index": 3,
        },
        {
            "name": "First Company",
            "title": "Role 1",
            "description": "Description 1",
            "order_index": 1,
        },
        {
            "name": "Second Company",
            "title": "Role 2",
            "description": "Description 2",
            "order_index": 2,
        },
    ]

    for company in companies:
        response = client.post(
            "/api/v1/companies/", json=company, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201

    # Get all companies
    response = client.get("/api/v1/companies/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Verify ordering
    assert data[0]["name"] == "First Company"
    assert data[1]["name"] == "Second Company"
    assert data[2]["name"] == "Third Company"


def test_rebuild_complete_data_temp_requires_auth(client: TestClient):
    """Test rebuild-complete-data-temp endpoint requires authentication."""
    response = client.post("/api/v1/companies/rebuild-complete-data-temp")
    # HTTPBearer returns 401 when no Authorization header is present
    assert response.status_code == 401


def test_rebuild_complete_data_temp(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test rebuild-complete-data-temp endpoint with authentication."""
    response = client.post(
        "/api/v1/companies/rebuild-complete-data-temp",
        headers=admin_user_in_db["headers"],
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "success"
    assert "count" in data
    assert data["count"] == 7  # Expected number of companies


def test_rebuild_complete_data_creates_companies(
    client: TestClient, admin_user_in_db: dict[str, Any]
):
    """Test that rebuild creates expected companies."""
    # First rebuild the data (with auth)
    response = client.post(
        "/api/v1/companies/rebuild-complete-data-temp",
        headers=admin_user_in_db["headers"],
    )
    assert response.status_code == 200

    # Then get all companies
    response = client.get("/api/v1/companies/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 7

    # Check some expected companies exist
    company_names = [c["name"] for c in data]
    assert "Scania" in company_names
    assert "Hermes Medical Solutions AB" in company_names
    assert "Karolinska University Hospital" in company_names


def test_get_company_by_id_success(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test getting a company by ID after rebuild."""
    # First rebuild the data (with auth)
    client.post(
        "/api/v1/companies/rebuild-complete-data-temp",
        headers=admin_user_in_db["headers"],
    )

    # Get all companies to find an ID
    response = client.get("/api/v1/companies/")
    companies = response.json()
    if companies:
        company_id = companies[0]["id"]
        response = client.get(f"/api/v1/companies/{company_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == company_id


def test_company_response_schema(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test that company response matches expected schema."""
    # First rebuild the data (with auth)
    client.post(
        "/api/v1/companies/rebuild-complete-data-temp",
        headers=admin_user_in_db["headers"],
    )

    # Get all companies
    response = client.get("/api/v1/companies/")
    data = response.json()
    if data:
        company = data[0]
        # Check expected fields exist
        assert "id" in company
        assert "name" in company
        assert "title" in company
        assert "description" in company
        assert "order_index" in company


class TestCompanyEdgeCases:
    """Edge case tests for companies API."""

    def test_update_partial_fields(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test updating only some fields preserves others."""
        company_data = {
            "name": "Partial Update Company",
            "title": "Original Title",
            "description": "Original description",
            "location": "Original Location",
            "order_index": 10,
        }
        create_response = client.post(
            "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
        )
        assert create_response.status_code == 201
        company_id = create_response.json()["id"]

        # Update only title
        update_response = client.put(
            f"/api/v1/companies/{company_id}",
            json={"title": "Updated Title Only"},
            headers=admin_user_in_db["headers"],
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["title"] == "Updated Title Only"
        assert data["name"] == "Partial Update Company"
        assert data["description"] == "Original description"
        assert data["location"] == "Original Location"

    def test_create_company_with_all_fields(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating company with all optional fields."""
        company_data = {
            "name": "Full Company",
            "title": "Full Title",
            "description": "Short description",
            "detailed_description": "Very detailed description here",
            "location": "Stockholm, Sweden",
            "start_date": "2020-01-15",
            "end_date": "2023-12-31",
            "website": "https://example.com",
            "order_index": 5,
            "responsibilities": ["Task 1", "Task 2"],
            "technologies": ["Python", "FastAPI"],
        }
        response = client.post(
            "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Full Company"
        assert data["detailed_description"] == "Very detailed description here"
        assert data["website"] == "https://example.com"
        assert "responsibilities" in data
        assert "technologies" in data

    def test_create_company_minimal_fields(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating company with only required fields."""
        company_data = {
            "name": "Minimal Company",
            "title": "Minimal Title",
        }
        response = client.post(
            "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Company"
        assert data["title"] == "Minimal Title"

    def test_create_company_missing_name(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating company without name fails validation."""
        company_data = {
            "title": "Has Title",
            "description": "Has description",
        }
        response = client.post(
            "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 422

    def test_create_company_without_title(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating company without title succeeds (title is optional)."""
        company_data = {
            "name": "Company Without Title",
            "description": "Has description",
        }
        response = client.post(
            "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Company Without Title"
        assert data["title"] is None

    def test_rebuild_clears_existing_data(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test that rebuild clears existing companies first."""
        # Create a custom company
        custom_company = {
            "name": "Custom Company",
            "title": "Custom Title",
            "description": "Should be removed after rebuild",
            "order_index": 100,
        }
        create_response = client.post(
            "/api/v1/companies/", json=custom_company, headers=admin_user_in_db["headers"]
        )
        assert create_response.status_code == 201

        # Rebuild the data
        rebuild_response = client.post(
            "/api/v1/companies/rebuild-complete-data-temp",
            headers=admin_user_in_db["headers"],
        )
        assert rebuild_response.status_code == 200

        # Get all companies
        response = client.get("/api/v1/companies/")
        data = response.json()
        company_names = [c["name"] for c in data]

        # Custom company should be gone, only rebuilt data remains
        assert "Custom Company" not in company_names
        assert len(data) == 7  # Only the rebuilt companies

    def test_get_company_by_invalid_uuid_format(self, client: TestClient):
        """Test getting company with invalid ID format."""
        # Valid UUID format but non-existent
        response = client.get("/api/v1/companies/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_company_with_current_position(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating a company with no end date (current position)."""
        company_data = {
            "name": "Current Employer",
            "title": "Current Role",
            "description": "Still working here",
            "start_date": "2023-01-01",
            "end_date": None,
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/companies/", json=company_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["end_date"] is None
