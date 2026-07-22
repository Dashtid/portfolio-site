"""
Tests for the admin-only CV profile + export endpoints
(Campaign 2026-08 Sprint 2).

The public site is the CV; this feature is admin-only and its payload carries
the owner's private contact, so authorization is the first thing asserted.
Export data is assembled from the same companies/education/skills the public
homepage renders — seeded here through the real admin CRUD endpoints.
"""

from typing import Any

from fastapi.testclient import TestClient

PROFILE_URL = "/api/v1/admin/cv/profile"
EXPORT_URL = "/api/v1/admin/cv/export"


def _seed_cv_sources(client: TestClient, headers: dict[str, str]) -> None:
    """Create one company, two education rows (degree + cert), two skills."""
    client.post(
        "/api/v1/companies/",
        headers=headers,
        json={
            "name": "Hermes Medical Solutions",
            "title": "QA/RA & Security Specialist",
            "location": "Stockholm, Sweden",
            "start_date": "2024-05-01",
            "end_date": None,
            "order_index": 1,
            "responsibilities": ["Threat modeling", "SBOM-based SCA"],
            "outcomes": ["Cut vulnerability triage time"],
        },
    )
    client.post(
        "/api/v1/education/",
        headers=headers,
        json={
            "institution": "KTH Royal Institute of Technology",
            "degree": "M.Sc.",
            "field_of_study": "Biomedical Engineering",
            "start_date": "2018-08-01",
            "end_date": "2021-06-01",
            "is_certification": False,
            "order_index": 1,
        },
    )
    client.post(
        "/api/v1/education/",
        headers=headers,
        json={
            "institution": "CompTIA",
            "degree": "Security+",
            "start_date": "2024-01-01",
            "end_date": "2026-01-31",
            "is_certification": True,
            "certificate_url": "https://www.credly.com/badges/example/public_url",
            "order_index": 2,
        },
    )
    client.post(
        "/api/v1/skills/",
        headers=headers,
        json={"name": "Python", "category": "Technical", "order_index": 1},
    )
    client.post(
        "/api/v1/skills/",
        headers=headers,
        json={"name": "Threat Modeling", "category": "Security", "order_index": 2},
    )


class TestCvProfileEndpoint:
    def test_profile_requires_admin(self, client: TestClient, test_user_in_db: dict[str, Any]):
        """A non-admin token never sees the profile (which carries contact)."""
        response = client.get(PROFILE_URL, headers=test_user_in_db["headers"])
        assert response.status_code in (401, 403)

    def test_profile_unauthenticated_rejected(self, client: TestClient):
        assert client.get(PROFILE_URL).status_code in (401, 403)
        assert client.put(PROFILE_URL, json={}).status_code in (401, 403)

    def test_admin_gets_singleton_with_blank_contact(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """First GET creates the singleton; private contact is blank by default."""
        response = client.get(PROFILE_URL, headers=admin_user_in_db["headers"])
        assert response.status_code == 200
        body = response.json()
        assert "id" in body
        assert body["email"] == ""
        assert body["phone"] == ""
        assert body["personnummer"] == ""

    def test_update_profile_persists(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """PUT applies a partial update and the singleton persists it."""
        headers = admin_user_in_db["headers"]
        response = client.put(
            PROFILE_URL,
            headers=headers,
            json={
                "name": "David Dashti",
                "summary": "Product security engineer.",
                "email": "me@example.com",
                "phone": "+46 70 000 00 00",
                "languages": [{"language": "Swedish", "fluency": "Native"}],
            },
        )
        assert response.status_code == 200
        assert response.json()["email"] == "me@example.com"

        # Same singleton on the next request (no duplicate rows).
        again = client.get(PROFILE_URL, headers=headers).json()
        assert again["summary"] == "Product security engineer."
        assert again["languages"] == [{"language": "Swedish", "fluency": "Native"}]

    def test_update_ignores_explicit_null(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """An explicit JSON null means 'leave unchanged' — never a 500.

        Columns are NOT NULL; writing None would raise on commit. The handler
        skips null-valued fields instead.
        """
        headers = admin_user_in_db["headers"]
        client.put(PROFILE_URL, headers=headers, json={"summary": "Kept."})
        response = client.put(PROFILE_URL, headers=headers, json={"summary": None, "email": None})
        assert response.status_code == 200
        body = response.json()
        assert body["summary"] == "Kept."  # the null did not overwrite it


class TestCvExportEndpoint:
    def test_export_requires_admin(self, client: TestClient, test_user_in_db: dict[str, Any]):
        response = client.get(EXPORT_URL, headers=test_user_in_db["headers"])
        assert response.status_code in (401, 403)

    def test_export_unauthenticated_rejected(self, client: TestClient):
        assert client.get(EXPORT_URL).status_code in (401, 403)

    def test_export_assembles_from_db(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        """Export builds a JSON Resume from profile + companies + education + skills."""
        headers = admin_user_in_db["headers"]
        _seed_cv_sources(client, headers)
        client.put(
            PROFILE_URL,
            headers=headers,
            json={
                "name": "David Dashti",
                "label": "Product & Application Security Engineer",
                "email": "me@example.com",
                "linkedin_url": "https://www.linkedin.com/in/david-dashti/",
                "github_url": "https://github.com/Dashtid",
                "languages": [{"language": "Swedish", "fluency": "Native"}],
            },
        )

        response = client.get(EXPORT_URL, headers=headers)
        assert response.status_code == 200
        cv = response.json()

        # basics from the profile, including private contact (admin-only).
        assert cv["basics"]["name"] == "David Dashti"
        assert cv["basics"]["email"] == "me@example.com"
        assert {p["network"] for p in cv["basics"]["profiles"]} == {"LinkedIn", "GitHub"}
        # personnummer is off by default -> key absent entirely.
        assert "personalNumber" not in cv["basics"]

        # work from companies; highlights = responsibilities + outcomes; open-ended.
        assert len(cv["work"]) == 1
        assert cv["work"][0]["name"] == "Hermes Medical Solutions"
        assert cv["work"][0]["endDate"] == ""
        assert cv["work"][0]["highlights"] == [
            "Threat modeling",
            "SBOM-based SCA",
            "Cut vulnerability triage time",
        ]

        # education vs certificate split on is_certification.
        assert [e["institution"] for e in cv["education"]] == ["KTH Royal Institute of Technology"]
        assert [c["name"] for c in cv["certificates"]] == ["Security+"]
        assert cv["certificates"][0]["issuer"] == "CompTIA"

        # flat skills grouped by category, preserving order.
        groups = {g["name"]: g["keywords"] for g in cv["skills"]}
        assert groups["Technical"] == ["Python"]
        assert groups["Security"] == ["Threat Modeling"]

        assert cv["languages"] == [{"language": "Swedish", "fluency": "Native"}]

    def test_export_includes_personnummer_only_when_set(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        headers = admin_user_in_db["headers"]
        client.put(PROFILE_URL, headers=headers, json={"personnummer": "900101-0000"})
        cv = client.get(EXPORT_URL, headers=headers).json()
        assert cv["basics"]["personalNumber"] == "900101-0000"
