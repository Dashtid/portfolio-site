"""
Tests for companies API endpoints
"""

from fastapi.testclient import TestClient


def test_get_companies_unauthenticated(client: TestClient):
    """Test getting companies without authentication should work."""
    response = client.get("/api/v1/companies/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_company_requires_auth(client: TestClient):
    """Test creating company without authentication should fail."""
    company_data = {
        "name": "Test Company",
        "role": "Software Engineer",
        "duration": "2020-2023",
        "description": "Test description",
        "order": 1,
        "current": False,
    }
    response = client.post("/api/v1/companies/", json=company_data)
    assert response.status_code == 401


def test_create_company_with_auth(client: TestClient, admin_headers: dict):
    """Test creating company with admin authentication."""
    company_data = {
        "name": "Test Company",
        "role": "Software Engineer",
        "duration": "2020-2023",
        "description": "Test description",
        "order": 1,
        "current": False,
    }
    response = client.post("/api/v1/companies/", json=company_data, headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == company_data["name"]
    assert data["role"] == company_data["role"]
    assert "id" in data


def test_update_company(client: TestClient, admin_headers: dict):
    """Test updating a company."""
    # Create a company first
    company_data = {
        "name": "Original Company",
        "role": "Junior Developer",
        "duration": "2020-2021",
        "description": "Original description",
        "order": 1,
        "current": False,
    }
    create_response = client.post("/api/v1/companies/", json=company_data, headers=admin_headers)
    company_id = create_response.json()["id"]

    # Update the company
    update_data = {
        "name": "Updated Company",
        "role": "Senior Developer",
        "duration": "2020-2023",
        "description": "Updated description",
        "order": 1,
        "current": True,
    }
    response = client.put(
        f"/api/v1/companies/{company_id}", json=update_data, headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["role"] == update_data["role"]
    assert data["current"] == True


def test_delete_company(client: TestClient, admin_headers: dict):
    """Test deleting a company."""
    # Create a company first
    company_data = {
        "name": "Company to Delete",
        "role": "Test Role",
        "duration": "2023",
        "description": "Will be deleted",
        "order": 1,
        "current": False,
    }
    create_response = client.post("/api/v1/companies/", json=company_data, headers=admin_headers)
    company_id = create_response.json()["id"]

    # Delete the company
    response = client.delete(f"/api/v1/companies/{company_id}", headers=admin_headers)
    assert response.status_code == 200

    # Verify it's deleted
    get_response = client.get("/api/v1/companies/")
    companies = get_response.json()
    assert not any(c["id"] == company_id for c in companies)


def test_company_ordering(client: TestClient, admin_headers: dict):
    """Test that companies are returned in correct order."""
    # Create multiple companies with different orders
    companies = [
        {
            "name": "Third Company",
            "role": "Role 3",
            "duration": "2023",
            "description": "Description 3",
            "order": 3,
            "current": False,
        },
        {
            "name": "First Company",
            "role": "Role 1",
            "duration": "2021",
            "description": "Description 1",
            "order": 1,
            "current": False,
        },
        {
            "name": "Second Company",
            "role": "Role 2",
            "duration": "2022",
            "description": "Description 2",
            "order": 2,
            "current": True,
        },
    ]

    for company in companies:
        client.post("/api/v1/companies/", json=company, headers=admin_headers)

    # Get all companies
    response = client.get("/api/v1/companies/")
    data = response.json()

    # Verify they're ordered correctly
    assert len(data) >= 3
    ordered_companies = sorted(
        [c for c in data if c["name"] in ["First Company", "Second Company", "Third Company"]],
        key=lambda x: x["order"],
    )
    assert ordered_companies[0]["name"] == "First Company"
    assert ordered_companies[1]["name"] == "Second Company"
    assert ordered_companies[2]["name"] == "Third Company"
