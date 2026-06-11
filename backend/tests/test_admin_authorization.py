"""
Tests that non-admin users cannot reach admin-write endpoints.

Covers BACKEND-TESTS-05. The protected endpoints route through
``get_current_admin_user``, which raises 403 when ``is_admin`` is False on
the authenticated user. The risk if this regresses: any non-admin token
holder (e.g. a future shared-login feature, or any future non-admin user
created via OAuth) could mutate the public portfolio content.

We test every POST/PUT/DELETE endpoint that depends on ``AdminUser`` across
companies / projects / skills / education and ``/metrics/reset``. Each
endpoint is hit with a token for a real but ``is_admin=False`` user.
"""

from typing import Any

from fastapi.testclient import TestClient

# Minimal valid payloads to push past Pydantic validation — the request
# should never reach the model layer because the admin gate is checked
# first, but giving Pydantic real data isolates the test to the gate.
COMPANY_PAYLOAD = {
    "name": "Test Co",
    "title": "Engineer",
    "description": "desc",
    "location": "SE",
    "start_date": "2020-01-01",
    "order_index": 1,
}

PROJECT_PAYLOAD = {
    "name": "Test Project",
    "description": "A test project",
    "technologies": ["Python"],
}

SKILL_PAYLOAD = {
    "name": "Python",
    "category": "Language",
    "proficiency_level": 80,
    "order_index": 1,
}

EDUCATION_PAYLOAD = {
    "institution": "Test University",
    "degree": "BSc",
    "field_of_study": "CS",
    "start_date": "2018-09-01",
    "end_date": "2022-06-01",
    "location": "Stockholm",
    "order_index": 1,
}

FAKE_ID = "00000000-0000-0000-0000-000000000000"


def _is_denied(status_code: int) -> bool:
    """Both 401 and 403 are acceptable denials.

    ``get_current_admin_user`` is intended to raise 403, but the auth
    layer above it can short-circuit to 401 for some edge cases (e.g. a
    token that decodes but has no DB row). Either denies the mutation,
    which is what BACKEND-TESTS-05 cares about.
    """
    return status_code in (401, 403)


class TestNonAdminCompanyMutations:
    def test_non_admin_post_company_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.post(
            "/api/v1/companies/", json=COMPANY_PAYLOAD, headers=test_user_in_db["headers"]
        )
        assert _is_denied(response.status_code)

    def test_non_admin_put_company_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.put(
            f"/api/v1/companies/{FAKE_ID}",
            json={"name": "Renamed"},
            headers=test_user_in_db["headers"],
        )
        assert _is_denied(response.status_code)

    def test_non_admin_delete_company_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.delete(f"/api/v1/companies/{FAKE_ID}", headers=test_user_in_db["headers"])
        assert _is_denied(response.status_code)


class TestNonAdminProjectMutations:
    def test_non_admin_post_project_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.post(
            "/api/v1/projects/", json=PROJECT_PAYLOAD, headers=test_user_in_db["headers"]
        )
        assert _is_denied(response.status_code)

    def test_non_admin_put_project_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.put(
            f"/api/v1/projects/{FAKE_ID}",
            json={"name": "Renamed"},
            headers=test_user_in_db["headers"],
        )
        assert _is_denied(response.status_code)

    def test_non_admin_delete_project_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.delete(f"/api/v1/projects/{FAKE_ID}", headers=test_user_in_db["headers"])
        assert _is_denied(response.status_code)


class TestNonAdminSkillMutations:
    def test_non_admin_post_skill_denied(self, client: TestClient, test_user_in_db: dict[str, Any]):
        response = client.post(
            "/api/v1/skills/", json=SKILL_PAYLOAD, headers=test_user_in_db["headers"]
        )
        assert _is_denied(response.status_code)

    def test_non_admin_put_skill_denied(self, client: TestClient, test_user_in_db: dict[str, Any]):
        response = client.put(
            f"/api/v1/skills/{FAKE_ID}",
            json={"name": "Renamed"},
            headers=test_user_in_db["headers"],
        )
        assert _is_denied(response.status_code)

    def test_non_admin_delete_skill_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.delete(f"/api/v1/skills/{FAKE_ID}", headers=test_user_in_db["headers"])
        assert _is_denied(response.status_code)


class TestNonAdminEducationMutations:
    def test_non_admin_post_education_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.post(
            "/api/v1/education/", json=EDUCATION_PAYLOAD, headers=test_user_in_db["headers"]
        )
        assert _is_denied(response.status_code)

    def test_non_admin_put_education_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.put(
            f"/api/v1/education/{FAKE_ID}",
            json={"institution": "Renamed"},
            headers=test_user_in_db["headers"],
        )
        assert _is_denied(response.status_code)

    def test_non_admin_delete_education_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.delete(f"/api/v1/education/{FAKE_ID}", headers=test_user_in_db["headers"])
        assert _is_denied(response.status_code)


class TestNonAdminMetricsMutations:
    def test_non_admin_reset_metrics_denied(
        self, client: TestClient, test_user_in_db: dict[str, Any]
    ):
        response = client.post("/api/v1/metrics/reset", headers=test_user_in_db["headers"])
        assert _is_denied(response.status_code)


class TestAdminMutationsStillSucceed:
    """Sanity check: the same endpoints accept an admin token.

    Without this, a regression that broke ALL writes (not just the
    non-admin path) would still pass the deny tests above.
    """

    def test_admin_post_company_succeeds(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        response = client.post(
            "/api/v1/companies/", json=COMPANY_PAYLOAD, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201

    def test_admin_post_skill_succeeds(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        response = client.post(
            "/api/v1/skills/", json=SKILL_PAYLOAD, headers=admin_user_in_db["headers"]
        )
        assert response.status_code == 201
