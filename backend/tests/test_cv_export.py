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

        # work from companies; open-ended. With no cv_highlights set, the export
        # falls back to outcomes ALONE — never responsibilities + outcomes, which
        # are two parallel descriptions of the same role and restate each other.
        assert len(cv["work"]) == 1
        assert cv["work"][0]["name"] == "Hermes Medical Solutions"
        assert cv["work"][0]["endDate"] == ""
        assert cv["work"][0]["highlights"] == ["Cut vulnerability triage time"]

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


class TestCvOtherSection:
    """Övrigt / logistics items (CV-generator requirements, 2026-08-06).

    B-körkort must render as logistics info at the bottom of the CV and can
    NEVER appear in a certifications section. The structural guarantee is
    that it lives in cv_profile.other_items and is exported under "other" —
    a key the certificates assembly cannot reach.
    """

    ITEM = "B-körkort (category B driving licence)"

    def test_other_items_round_trip(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        headers = admin_user_in_db["headers"]
        response = client.put(PROFILE_URL, headers=headers, json={"other_items": [self.ITEM]})
        assert response.status_code == 200
        assert response.json()["other_items"] == [self.ITEM]

        again = client.get(PROFILE_URL, headers=headers).json()
        assert again["other_items"] == [self.ITEM]

    def test_export_carries_other_never_certificates(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        headers = admin_user_in_db["headers"]
        _seed_cv_sources(client, headers)  # includes a real certificate row
        client.put(PROFILE_URL, headers=headers, json={"other_items": [self.ITEM]})

        cv = client.get(EXPORT_URL, headers=headers).json()
        assert cv["other"] == [self.ITEM]
        # The certificates section carries ONLY is_certification education
        # rows; no logistics string can appear there.
        assert all("körkort" not in c["name"].lower() for c in cv["certificates"])
        assert [c["name"] for c in cv["certificates"]] == ["Security+"]

    def test_blank_other_items_rejected_not_500(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Blank rows 422 at the schema layer — including whitespace-only.

        strip_whitespace runs before min_length, so "   " cannot sneak past
        as a visually blank bullet the way it would with min_length alone.
        """
        headers = admin_user_in_db["headers"]
        for blank in ("", "   "):
            response = client.put(PROFILE_URL, headers=headers, json={"other_items": [blank]})
            assert response.status_code == 422, f"blank item {blank!r} was accepted"


class TestCvHighlightsPrecedence:
    """The CV bullet list must be curated, not the site's two lists concatenated.

    `responsibilities` and `outcomes` describe the same role twice for the
    public detail page. Concatenating them for the CV produced 11 bullets for
    one job where the owner's real CV carries 3.
    """

    def test_cv_highlights_win_over_both_lists(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        headers = admin_user_in_db["headers"]
        _seed_cv_sources(client, headers)

        company_id = client.get("/api/v1/companies/", headers=headers).json()[0]["id"]
        curated = ["Curated CV bullet one", "Curated CV bullet two"]
        patch = client.put(
            f"/api/v1/companies/{company_id}",
            headers=headers,
            json={"cv_highlights": curated},
        )
        assert patch.status_code == 200, patch.text

        cv = client.get("/api/v1/admin/cv/export", headers=headers).json()
        assert cv["work"][0]["highlights"] == curated
        # The site's own lists are untouched and must NOT leak into the CV.
        assert "Threat modeling" not in cv["work"][0]["highlights"]
        assert "Cut vulnerability triage time" not in cv["work"][0]["highlights"]

    def test_falls_back_to_outcomes_then_responsibilities(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        headers = admin_user_in_db["headers"]
        _seed_cv_sources(client, headers)
        company_id = client.get("/api/v1/companies/", headers=headers).json()[0]["id"]

        # No cv_highlights -> outcomes alone (never concatenated).
        cv = client.get("/api/v1/admin/cv/export", headers=headers).json()
        assert cv["work"][0]["highlights"] == ["Cut vulnerability triage time"]

        # No outcomes either -> responsibilities.
        client.put(f"/api/v1/companies/{company_id}", headers=headers, json={"outcomes": []})
        cv = client.get("/api/v1/admin/cv/export", headers=headers).json()
        assert cv["work"][0]["highlights"] == ["Threat modeling", "SBOM-based SCA"]


class TestCvCertificateDates:
    def test_certificate_date_is_issue_not_expiry(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """Exporting end_date printed the EXPIRY as if it were the award date."""
        headers = admin_user_in_db["headers"]
        _seed_cv_sources(client, headers)

        cv = client.get("/api/v1/admin/cv/export", headers=headers).json()
        cert = cv["certificates"][0]
        assert cert["date"] == "2024-01", "date must be the issue month (start_date)"
        assert cert["expires"] == "2026-01", "expiry belongs in its own field"

    def test_education_keeps_its_verification_url(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """A completed course kept its certificate_url; the export dropped it."""
        headers = admin_user_in_db["headers"]
        _seed_cv_sources(client, headers)
        client.post(
            "/api/v1/education/",
            headers=headers,
            json={
                "institution": "Företagsuniversitetet",
                "degree": "Cybersecurity Fundamentals (Course)",
                "start_date": "2024-10-01",
                "end_date": "2024-12-31",
                "is_certification": False,
                "certificate_url": "https://example.com/verify/abc",
                "order_index": 3,
            },
        )

        cv = client.get("/api/v1/admin/cv/export", headers=headers).json()
        course = next(e for e in cv["education"] if "Course" in e["studyType"])
        assert course["url"] == "https://example.com/verify/abc"


class TestCvPhoto:
    """The headshot rides in the 401-gated payload, never a public file."""

    _PNG = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )

    def test_photo_round_trips_and_reaches_export(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        headers = admin_user_in_db["headers"]
        assert (
            client.put(
                "/api/v1/admin/cv/profile", headers=headers, json={"photo": self._PNG}
            ).status_code
            == 200
        )

        assert client.get("/api/v1/admin/cv/profile", headers=headers).json()["photo"] == self._PNG
        cv = client.get("/api/v1/admin/cv/export", headers=headers).json()
        assert cv["basics"]["image"] == self._PNG

    def test_absent_photo_omits_the_key(self, client: TestClient, admin_user_in_db: dict[str, Any]):
        headers = admin_user_in_db["headers"]
        cv = client.get("/api/v1/admin/cv/export", headers=headers).json()
        assert "image" not in cv["basics"]

    def test_non_image_data_uri_rejected(
        self, client: TestClient, admin_user_in_db: dict[str, Any]
    ):
        """An <img src> fed an unrestricted data: URI is an injection surface."""
        headers = admin_user_in_db["headers"]
        for bad in (
            "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
            "javascript:alert(1)",
            "https://example.com/photo.jpg",
        ):
            resp = client.put("/api/v1/admin/cv/profile", headers=headers, json={"photo": bad})
            assert resp.status_code == 422, f"{bad!r} should be rejected, got {resp.status_code}"
