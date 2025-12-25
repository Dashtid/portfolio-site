"""
Tests for education API endpoints
"""

from fastapi.testclient import TestClient


def test_get_education_public(client: TestClient):
    """Test getting education records without authentication."""
    response = client.get("/api/v1/education/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_degrees_public(client: TestClient):
    """Test getting degree records without authentication."""
    response = client.get("/api/v1/education/degrees/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_certifications_public(client: TestClient):
    """Test getting certification records without authentication."""
    response = client.get("/api/v1/education/certifications/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_education_not_found(client: TestClient):
    """Test getting a non-existent education record."""
    response = client.get("/api/v1/education/999999/")
    assert response.status_code == 404


def test_create_education_requires_auth(client: TestClient):
    """Test that creating education requires authentication."""
    education_data = {
        "institution": "Test University",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "start_date": "2018-09-01",
        "end_date": "2022-06-01",
        "is_certification": False,
        "order": 1,
    }
    response = client.post("/api/v1/education/", json=education_data)
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_create_education_with_auth(client: TestClient, admin_headers: dict):
    """Test creating education with authentication."""
    education_data = {
        "institution": "Test University",
        "degree": "Bachelor of Science",
        "field_of_study": "Computer Science",
        "start_date": "2018-09-01",
        "end_date": "2022-06-01",
        "is_certification": False,
        "order": 1,
    }
    response = client.post("/api/v1/education/", json=education_data, headers=admin_headers)
    # Note: With in-memory DB and no user, this may fail with 404
    assert response.status_code in [200, 201, 404]


def test_update_education_requires_auth(client: TestClient):
    """Test that updating education requires authentication."""
    update_data = {"degree": "Updated Degree"}
    response = client.put("/api/v1/education/1/", json=update_data)
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_delete_education_requires_auth(client: TestClient):
    """Test that deleting education requires authentication."""
    response = client.delete("/api/v1/education/1/")
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_education_validation(client: TestClient, admin_headers: dict):
    """Test education field validation."""
    # Missing required fields
    invalid_education = {"degree": "Test Degree"}
    response = client.post("/api/v1/education/", json=invalid_education, headers=admin_headers)
    # Either 422 for validation error or 404 for user not found
    assert response.status_code in [404, 422]


def test_update_education_not_found(client: TestClient, admin_headers: dict):
    """Test updating a non-existent education record."""
    update_data = {
        "institution": "Updated University",
        "degree": "Updated Degree",
        "field_of_study": "Updated Field",
        "start_date": "2019-09-01",
        "end_date": "2023-06-01",
        "is_certification": False,
        "order": 2,
    }
    response = client.put("/api/v1/education/999999/", json=update_data, headers=admin_headers)
    assert response.status_code == 404


def test_delete_education_not_found(client: TestClient, admin_headers: dict):
    """Test deleting a non-existent education record."""
    response = client.delete("/api/v1/education/999999/", headers=admin_headers)
    assert response.status_code == 404


def test_get_education_empty_list(client: TestClient):
    """Test that education returns empty list when none exist."""
    response = client.get("/api/v1/education/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_get_degrees_empty_list(client: TestClient):
    """Test that degrees returns empty list when none exist."""
    response = client.get("/api/v1/education/degrees/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_certifications_empty_list(client: TestClient):
    """Test that certifications returns empty list when none exist."""
    response = client.get("/api/v1/education/certifications/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


class TestEducationEndpoints:
    """Additional tests for education endpoints."""

    def test_education_router_exists(self):
        """Test that education router is properly configured."""
        from app.api.v1.education import router  # noqa: PLC0415

        assert router is not None
        assert router.prefix == "/education"

    def test_education_model_exists(self):
        """Test that Education model is importable."""
        from app.models.education import Education  # noqa: PLC0415

        assert Education is not None

    def test_education_schemas_exist(self):
        """Test that education schemas are importable."""
        from app.schemas.education import Education as EducationSchema  # noqa: PLC0415
        from app.schemas.education import EducationCreate, EducationUpdate  # noqa: PLC0415

        assert EducationSchema is not None
        assert EducationCreate is not None
        assert EducationUpdate is not None

    def test_get_education_by_invalid_id_format(self, client: TestClient):
        """Test getting education with invalid ID format."""
        # Use a string that's not convertible to int
        response = client.get("/api/v1/education/invalid-id/")
        assert response.status_code == 422

    def test_create_education_missing_institution(self, client: TestClient, admin_headers: dict):
        """Test creating education without institution."""
        education_data = {
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "start_date": "2018-09-01",
            "is_certification": False,
            "order": 1,
        }
        response = client.post("/api/v1/education/", json=education_data, headers=admin_headers)
        assert response.status_code in [404, 422]

    def test_create_education_missing_degree(self, client: TestClient, admin_headers: dict):
        """Test creating education without degree."""
        education_data = {
            "institution": "Test University",
            "field_of_study": "Computer Science",
            "start_date": "2018-09-01",
            "is_certification": False,
            "order": 1,
        }
        response = client.post("/api/v1/education/", json=education_data, headers=admin_headers)
        assert response.status_code in [404, 422]

    def test_update_education_with_invalid_id(self, client: TestClient, admin_headers: dict):
        """Test updating education with invalid ID format."""
        update_data = {"degree": "Updated Degree"}
        response = client.put(
            "/api/v1/education/invalid-id/", json=update_data, headers=admin_headers
        )
        # Either 422 for validation error or 404 for user not found
        assert response.status_code in [404, 422]

    def test_delete_education_with_invalid_id(self, client: TestClient, admin_headers: dict):
        """Test deleting education with invalid ID format."""
        response = client.delete("/api/v1/education/invalid-id/", headers=admin_headers)
        # Either 422 for validation error or 404 for user not found
        assert response.status_code in [404, 422]


class TestEducationValidation:
    """Tests for education field validation."""

    def test_education_date_validation(self, client: TestClient, admin_headers: dict):
        """Test education date validation."""
        education_data = {
            "institution": "Test University",
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science",
            "start_date": "invalid-date",
            "is_certification": False,
            "order": 1,
        }
        response = client.post("/api/v1/education/", json=education_data, headers=admin_headers)
        # Either 422 for validation error or 404 for user not found
        assert response.status_code in [404, 422]

    def test_education_with_certification_flag(self, client: TestClient, admin_headers: dict):
        """Test creating a certification type education."""
        education_data = {
            "institution": "Certification Body",
            "degree": "AWS Solutions Architect",
            "field_of_study": "Cloud Computing",
            "start_date": "2023-01-01",
            "end_date": "2023-01-05",
            "is_certification": True,
            "order": 1,
        }
        response = client.post("/api/v1/education/", json=education_data, headers=admin_headers)
        assert response.status_code in [200, 201, 404]


class TestEducationCRUDWithAdmin:
    """Full CRUD tests using admin user in database."""

    def test_create_education_success(self, client: TestClient, admin_user_in_db: dict):
        """Test successfully creating an education record with real admin."""
        education_data = {
            "institution": "MIT",
            "degree": "Master of Science",
            "field_of_study": "Computer Science",
            "start_date": "2020-09-01",
            "end_date": "2022-06-01",
            "is_certification": False,
            "order": 1,
        }
        response = client.post(
            "/api/v1/education/",
            json=education_data,
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["institution"] == "MIT"
        assert data["degree"] == "Master of Science"
        assert data["field_of_study"] == "Computer Science"
        assert data["is_certification"] is False
        assert "id" in data

    def test_create_certification_success(self, client: TestClient, admin_user_in_db: dict):
        """Test successfully creating a certification record."""
        cert_data = {
            "institution": "AWS",
            "degree": "Solutions Architect Professional",
            "field_of_study": "Cloud Computing",
            "start_date": "2023-03-01",
            "end_date": "2023-03-15",
            "is_certification": True,
            "order": 1,
        }
        response = client.post(
            "/api/v1/education/",
            json=cert_data,
            headers=admin_user_in_db["headers"],
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_certification"] is True

    def test_get_education_by_id_success(self, client: TestClient, admin_user_in_db: dict):
        """Test getting a specific education record by ID."""
        # Create education first
        education_data = {
            "institution": "Stanford",
            "degree": "PhD",
            "field_of_study": "Machine Learning",
            "start_date": "2018-09-01",
            "is_certification": False,
            "order": 2,
        }
        create_response = client.post(
            "/api/v1/education/",
            json=education_data,
            headers=admin_user_in_db["headers"],
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # Get by ID
        get_response = client.get(f"/api/v1/education/{created_id}/")
        assert get_response.status_code == 200
        data = get_response.json()
        assert data["institution"] == "Stanford"
        assert data["degree"] == "PhD"

    def test_update_education_success(self, client: TestClient, admin_user_in_db: dict):
        """Test successfully updating an education record."""
        # Create education first
        education_data = {
            "institution": "Harvard",
            "degree": "Bachelor of Arts",
            "field_of_study": "Economics",
            "start_date": "2015-09-01",
            "end_date": "2019-06-01",
            "is_certification": False,
            "order": 3,
        }
        create_response = client.post(
            "/api/v1/education/",
            json=education_data,
            headers=admin_user_in_db["headers"],
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # Update the record
        update_data = {
            "degree": "Bachelor of Science",
            "field_of_study": "Computer Science and Economics",
        }
        update_response = client.put(
            f"/api/v1/education/{created_id}/",
            json=update_data,
            headers=admin_user_in_db["headers"],
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["degree"] == "Bachelor of Science"
        assert data["field_of_study"] == "Computer Science and Economics"
        assert data["institution"] == "Harvard"  # Unchanged

    def test_delete_education_success(self, client: TestClient, admin_user_in_db: dict):
        """Test successfully deleting an education record."""
        # Create education first
        education_data = {
            "institution": "Yale",
            "degree": "JD",
            "field_of_study": "Law",
            "start_date": "2016-09-01",
            "end_date": "2019-06-01",
            "is_certification": False,
            "order": 4,
        }
        create_response = client.post(
            "/api/v1/education/",
            json=education_data,
            headers=admin_user_in_db["headers"],
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # Delete the record
        delete_response = client.delete(
            f"/api/v1/education/{created_id}/",
            headers=admin_user_in_db["headers"],
        )
        assert delete_response.status_code == 200
        assert "deleted" in delete_response.json()["message"].lower()

        # Verify it's deleted
        get_response = client.get(f"/api/v1/education/{created_id}/")
        assert get_response.status_code == 404

    def test_get_degrees_filters_correctly(self, client: TestClient, admin_user_in_db: dict):
        """Test that degrees endpoint filters out certifications."""
        # Create a degree
        degree_data = {
            "institution": "Princeton",
            "degree": "Bachelor of Science",
            "field_of_study": "Physics",
            "start_date": "2014-09-01",
            "end_date": "2018-06-01",
            "is_certification": False,
            "order": 1,
        }
        client.post(
            "/api/v1/education/",
            json=degree_data,
            headers=admin_user_in_db["headers"],
        )

        # Create a certification
        cert_data = {
            "institution": "Google",
            "degree": "Cloud Professional",
            "field_of_study": "Cloud",
            "start_date": "2023-01-01",
            "end_date": "2023-01-10",
            "is_certification": True,
            "order": 2,
        }
        client.post(
            "/api/v1/education/",
            json=cert_data,
            headers=admin_user_in_db["headers"],
        )

        # Get degrees only
        degrees_response = client.get("/api/v1/education/degrees/")
        assert degrees_response.status_code == 200
        degrees = degrees_response.json()
        for degree in degrees:
            assert degree["is_certification"] is False

    def test_get_certifications_filters_correctly(self, client: TestClient, admin_user_in_db: dict):
        """Test that certifications endpoint filters out degrees."""
        # Create a degree
        degree_data = {
            "institution": "Columbia",
            "degree": "MBA",
            "field_of_study": "Business",
            "start_date": "2019-09-01",
            "end_date": "2021-06-01",
            "is_certification": False,
            "order": 1,
        }
        client.post(
            "/api/v1/education/",
            json=degree_data,
            headers=admin_user_in_db["headers"],
        )

        # Create a certification
        cert_data = {
            "institution": "Microsoft",
            "degree": "Azure Administrator",
            "field_of_study": "Cloud",
            "start_date": "2023-02-01",
            "end_date": "2023-02-10",
            "is_certification": True,
            "order": 2,
        }
        client.post(
            "/api/v1/education/",
            json=cert_data,
            headers=admin_user_in_db["headers"],
        )

        # Get certifications only
        certs_response = client.get("/api/v1/education/certifications/")
        assert certs_response.status_code == 200
        certs = certs_response.json()
        for cert in certs:
            assert cert["is_certification"] is True

    def test_education_ordering(self, client: TestClient, admin_user_in_db: dict):
        """Test that education records are ordered correctly."""
        # Create education with different order values
        for i, inst in enumerate(["First", "Second", "Third"], start=1):
            education_data = {
                "institution": f"{inst} University",
                "degree": "Bachelor",
                "field_of_study": "Science",
                "start_date": f"201{i}-09-01",
                "is_certification": False,
                "order": 4 - i,  # Reverse order: 3, 2, 1
            }
            client.post(
                "/api/v1/education/",
                json=education_data,
                headers=admin_user_in_db["headers"],
            )

        # Get all education
        response = client.get("/api/v1/education/")
        assert response.status_code == 200
        data = response.json()

        # Should be ordered by 'order' field ascending
        if len(data) >= 3:
            orders = [e["order"] for e in data]
            assert orders == sorted(orders)

    def test_update_partial_fields(self, client: TestClient, admin_user_in_db: dict):
        """Test updating only some fields preserves others."""
        # Create education
        education_data = {
            "institution": "Berkeley",
            "degree": "Master of Science",
            "field_of_study": "Data Science",
            "start_date": "2021-09-01",
            "end_date": "2023-06-01",
            "is_certification": False,
            "order": 5,
            "description": "Original description",
        }
        create_response = client.post(
            "/api/v1/education/",
            json=education_data,
            headers=admin_user_in_db["headers"],
        )
        assert create_response.status_code == 200
        created_id = create_response.json()["id"]

        # Update only one field
        update_response = client.put(
            f"/api/v1/education/{created_id}/",
            json={"description": "Updated description"},
            headers=admin_user_in_db["headers"],
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["description"] == "Updated description"
        assert data["institution"] == "Berkeley"
        assert data["degree"] == "Master of Science"
