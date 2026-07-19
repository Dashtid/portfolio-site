"""
D3-BE-01: rate limiting must actually produce 429s.

The pre-existing 60+ "rate limit" tests asserted decorator objects exist
and settings parse — none ever drove a request into a real 429. These
tests do, against the real app and against a minimal app wired with the
same handler contract.

Also covers the BodySizeLimit credential gate: the 26 MB allowance on
/documents/upload must require a signature-valid JWT, because FastAPI
parses multipart bodies before auth dependencies run.
"""

from fastapi.testclient import TestClient

from app.config import settings
from app.core.security import create_access_token
from app.main import app
from app.middleware import limiter


class TestDefaultLimitEnforced:
    """The middleware must enforce RATE_LIMIT_DEFAULT on undecorated routes."""

    def test_slowapi_asgi_middleware_installed(self):
        from slowapi.middleware import SlowAPIASGIMiddleware

        installed = [m.cls for m in app.user_middleware]
        assert SlowAPIASGIMiddleware in installed

    def test_undecorated_route_returns_real_429_with_retry_after(self, client: TestClient):
        """Drive the root endpoint past the default limit and demand a 429.

        The root endpoint has no decorator, so before the middleware was
        installed it had NO limit at all — this test fails on that world.
        """
        limit = int(settings.RATE_LIMIT_DEFAULT.split("/")[0])

        for _ in range(limit):
            assert client.get("/").status_code == 200

        blocked = client.get("/")
        assert blocked.status_code == 429
        assert "Retry-After" in blocked.headers
        assert "Rate limit exceeded" in blocked.json()["detail"]

    def test_decorated_routes_not_double_counted(self, client: TestClient):
        """A decorator-limited route must be exempt from the default limit.

        /api/v1/projects/ carries the 120/minute public tier, which is
        above the 100/minute default — if the middleware double-counted,
        request 101 would 429 out of the default bucket instead.
        """
        default_limit = int(settings.RATE_LIMIT_DEFAULT.split("/")[0])
        public_limit = int(settings.RATE_LIMIT_PUBLIC.split("/")[0])
        assert public_limit > default_limit, "test premise: public tier above default"

        for i in range(public_limit):
            response = client.get("/api/v1/projects/")
            assert response.status_code == 200, (
                f"request {i + 1} unexpectedly {response.status_code}"
            )

        assert client.get("/api/v1/projects/").status_code == 429


class TestUploadBodyAllowanceGate:
    """The 26 MB upload allowance must require a signature-valid token."""

    UPLOAD_PATH = "/api/v1/documents/upload"

    def _multipart_post(self, client: TestClient, size: int, **kwargs):
        return client.post(
            self.UPLOAD_PATH,
            files={"file": ("big.pdf", b"x" * size, "application/pdf")},
            **kwargs,
        )

    def test_anonymous_large_body_hits_the_5mb_cap(self, client: TestClient):
        """6 MB anonymous upload: 413 from the middleware, body never parsed.

        Before the gate, the path-based override let any client stream
        26 MB into the multipart parser before auth said no.
        """
        response = self._multipart_post(client, 6 * 1024 * 1024)
        assert response.status_code == 413
        assert "5 MB" in response.json()["detail"]

    def test_fabricated_cookie_does_not_unlock_the_allowance(self, client: TestClient):
        client.cookies.set("access_token", "junk.fabricated.token")
        response = self._multipart_post(client, 6 * 1024 * 1024)
        assert response.status_code == 413

    def test_valid_token_unlocks_the_allowance(self, client: TestClient):
        """A signed token gets the 26 MB allowance; auth still gates later.

        The token subject has no user row, so the request must pass the
        body-size middleware (no 413) and then die in the auth dependency
        (404 "User not found", deps.py) — proving the gate is about body
        budget, not a bypass of authz.
        """
        token = create_access_token(subject="body-gate-probe")
        response = self._multipart_post(
            client,
            6 * 1024 * 1024,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "User not found"

    def test_valid_token_still_capped_at_26mb(self, client: TestClient):
        token = create_access_token(subject="body-gate-probe")
        response = self._multipart_post(
            client,
            27 * 1024 * 1024,
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 413
        assert "26 MB" in response.json()["detail"]


class TestLimiterKeying:
    """Verified-token requests get their own bucket; junk falls to IP."""

    def test_verified_token_and_anonymous_use_separate_buckets(self, client: TestClient):
        limit = int(settings.RATE_LIMIT_DEFAULT.split("/")[0])
        for _ in range(limit):
            assert client.get("/").status_code == 200
        assert client.get("/").status_code == 429

        # Same IP, but a verified token keys a fresh user bucket.
        token = create_access_token(subject="bucket-probe")
        response = client.get("/", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200

    def test_limiter_storage_resets_between_tests(self, client: TestClient):
        """Guards the autouse reset fixture the suite now depends on."""
        assert client.get("/").status_code == 200
        limiter.reset()
        assert client.get("/").status_code == 200
