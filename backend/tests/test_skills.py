"""
Tests for skills API endpoints
"""

from typing import Any

from fastapi.testclient import TestClient


def test_get_skills_public(client: TestClient):
    """Test getting skills without authentication."""
    response = client.get("/api/v1/skills/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_skill_requires_auth(client: TestClient):
    """Test that creating skill requires authentication."""
    skill_data = {
        "name": "Python",
        "category": "Programming Languages",
        "proficiency": 90,
        "order_index": 1,
    }
    response = client.post("/api/v1/skills/", json=skill_data)
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_create_skill_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test creating skill with database-backed authentication."""
    skill_data = {
        "name": "Python",
        "category": "Programming Languages",
        "proficiency": 90,
        "order_index": 1,
    }
    response = client.post("/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"])
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Python"
    assert data["category"] == "Programming Languages"
    assert data["proficiency"] == 90
    assert "id" in data


def test_get_skill_by_id(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test getting a specific skill by ID."""
    # First create a skill
    skill_data = {
        "name": "JavaScript",
        "category": "Programming Languages",
        "proficiency": 85,
        "order_index": 2,
    }
    create_response = client.post(
        "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    skill_id = create_response.json()["id"]

    # Get the skill
    response = client.get(f"/api/v1/skills/{skill_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == skill_id
    assert data["name"] == "JavaScript"


def test_update_skill_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test updating a skill with database-backed authentication."""
    # Create a skill first
    skill_data = {
        "name": "TypeScript",
        "category": "Programming Languages",
        "proficiency": 75,
        "order_index": 3,
    }
    create_response = client.post(
        "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    skill_id = create_response.json()["id"]

    # Update the skill
    update_data = {
        "name": "TypeScript",
        "category": "Programming Languages",
        "proficiency": 95,
        "order_index": 1,
    }
    response = client.put(
        f"/api/v1/skills/{skill_id}", json=update_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["proficiency"] == 95
    assert data["order_index"] == 1


def test_delete_skill_with_db_auth(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test deleting a skill with database-backed authentication."""
    # Create a skill first
    skill_data = {
        "name": "Skill to Delete",
        "category": "Test",
        "proficiency": 50,
        "order_index": 99,
    }
    create_response = client.post(
        "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
    )
    assert create_response.status_code == 201
    skill_id = create_response.json()["id"]

    # Delete the skill
    response = client.delete(f"/api/v1/skills/{skill_id}", headers=admin_user_in_db["headers"])
    assert response.status_code == 204

    # Verify it's deleted
    get_response = client.get(f"/api/v1/skills/{skill_id}")
    assert get_response.status_code == 404


def test_get_skill_not_found(client: TestClient):
    """Test getting a non-existent skill."""
    response = client.get("/api/v1/skills/nonexistent-id")
    assert response.status_code == 404


def test_update_skill_requires_auth(client: TestClient):
    """Test that updating skill requires authentication."""
    update_data = {"name": "Updated Skill"}
    response = client.put("/api/v1/skills/some-id", json=update_data)
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_delete_skill_requires_auth(client: TestClient):
    """Test that deleting skill requires authentication."""
    response = client.delete("/api/v1/skills/some-id")
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_skill_validation(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test skill field validation."""
    # Missing required fields (name is required)
    invalid_skill = {"category": "Test"}
    response = client.post(
        "/api/v1/skills/", json=invalid_skill, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 422


def test_skill_proficiency_validation(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test skill proficiency range validation."""
    # Proficiency out of range (should be 0-100)
    invalid_skill = {
        "name": "Test Skill",
        "category": "Test",
        "proficiency": 150,  # Invalid - over 100
        "order_index": 1,
    }
    response = client.post(
        "/api/v1/skills/", json=invalid_skill, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 422


def test_update_skill_not_found(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test updating a non-existent skill."""
    update_data = {
        "name": "Updated Skill",
        "category": "Updated Category",
        "proficiency": 85,
        "order_index": 1,
    }
    response = client.put(
        "/api/v1/skills/nonexistent-id", json=update_data, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 404


def test_delete_skill_not_found(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test deleting a non-existent skill."""
    response = client.delete("/api/v1/skills/nonexistent-id", headers=admin_user_in_db["headers"])
    assert response.status_code == 404


def test_get_skills_empty_list(client: TestClient):
    """Test that skills returns empty list when none exist."""
    response = client.get("/api/v1/skills/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_skill_proficiency_negative(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test skill with negative proficiency."""
    invalid_skill = {
        "name": "Test Skill",
        "category": "Test",
        "proficiency": -10,  # Invalid - negative
        "order_index": 1,
    }
    response = client.post(
        "/api/v1/skills/", json=invalid_skill, headers=admin_user_in_db["headers"]
    )
    assert response.status_code == 422


def test_skill_ordering(client: TestClient, admin_user_in_db: dict[str, Any]):
    """Test that skills are returned ordered by order_index."""
    # Create skills with different order_index values
    skills = [
        {"name": "Skill C", "category": "Test", "proficiency": 80, "order_index": 3},
        {"name": "Skill A", "category": "Test", "proficiency": 90, "order_index": 1},
        {"name": "Skill B", "category": "Test", "proficiency": 85, "order_index": 2},
    ]

    for skill_data in skills:
        response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201

    # Get all skills
    response = client.get("/api/v1/skills/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Verify ordering
    assert data[0]["name"] == "Skill A"
    assert data[1]["name"] == "Skill B"
    assert data[2]["name"] == "Skill C"


class TestSkillEdgeCases:
    """Edge case tests for skills API."""

    def test_create_skill_with_all_fields(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating skill with all optional fields."""
        skill_data = {
            "name": "Full Skill",
            "category": "Frameworks",
            "proficiency": 95,
            "years_experience": 5.5,
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Full Skill"
        assert data["category"] == "Frameworks"
        assert data["proficiency"] == 95
        assert data["years_experience"] == 5.5
        assert data["order_index"] == 1

    def test_create_skill_minimal_fields(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test creating skill with only required fields."""
        skill_data = {"name": "Minimal Skill"}
        response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Skill"
        assert data["category"] is None
        assert data["proficiency"] is None

    def test_update_partial_fields(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test updating only some fields preserves others."""
        # Create skill
        skill_data = {
            "name": "Partial Update Skill",
            "category": "Original Category",
            "proficiency": 70,
            "order_index": 5,
        }
        create_response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert create_response.status_code == 201
        skill_id = create_response.json()["id"]

        # Update only proficiency
        update_response = client.put(
            f"/api/v1/skills/{skill_id}",
            json={"proficiency": 90},
            headers=admin_user_in_db["headers"],
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["proficiency"] == 90
        assert data["name"] == "Partial Update Skill"
        assert data["category"] == "Original Category"
        assert data["order_index"] == 5

    def test_skill_boundary_proficiency_zero(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test skill with proficiency at boundary (0)."""
        skill_data = {
            "name": "Zero Proficiency Skill",
            "proficiency": 0,
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        assert response.json()["proficiency"] == 0

    def test_skill_boundary_proficiency_hundred(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test skill with proficiency at boundary (100)."""
        skill_data = {
            "name": "Max Proficiency Skill",
            "proficiency": 100,
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        assert response.json()["proficiency"] == 100

    def test_skill_with_years_experience(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Test skill with years of experience."""
        skill_data = {
            "name": "Experienced Skill",
            "years_experience": 3.5,
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        assert response.json()["years_experience"] == 3.5

    def test_get_skill_by_invalid_uuid_format(self, client: TestClient):
        """Test getting skill with valid UUID format but non-existent."""
        response = client.get("/api/v1/skills/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404

    def test_skill_response_schema(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Test that skill response matches expected schema."""
        skill_data = {
            "name": "Schema Test Skill",
            "category": "Test",
            "proficiency": 85,
            "order_index": 1,
        }
        response = client.post(
            "/api/v1/skills/", json=skill_data, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
        data = response.json()
        # Check expected fields exist
        assert "id" in data
        assert "name" in data
        assert "category" in data
        assert "proficiency" in data
        assert "order_index" in data
        assert "created_at" in data
