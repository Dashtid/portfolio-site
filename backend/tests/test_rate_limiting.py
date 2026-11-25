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

import pytest
from fastapi.testclient import TestClient
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

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

    def test_undecorated_included_route_enforces_default_limit(self, client: TestClient):
        """Same 429 demand, but through an include_router route.

        fastapi 0.137+ registers included routers as _IncludedRouter
        entries without .endpoint; slowapi's middleware then resolves no
        handler and _should_exempt(None) silently EXEMPTS every /api/v1
        route from the default limit while '/' (a direct app route, which
        stays flattened) keeps working — so the test above cannot catch
        it. This regression drove the fastapi<0.137 cap in pyproject.toml
        and must fail again if the cap is lifted without a slowapi fix.
        """
        limit = int(settings.RATE_LIMIT_DEFAULT.split("/")[0])

        for i in range(limit):
            response = client.get("/api/v1/health")
            assert response.status_code == 200, (
                f"request {i + 1} unexpectedly {response.status_code}"
            )

        assert client.get("/api/v1/health").status_code == 429

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


class TestDecoratedLimitsCountFailedRequests:
    """A decorated route's limit is checked before its body is read.

    The decorator alone checks inside the endpoint, after FastAPI has
    parsed the body and solved the dependencies, so 422s and 401s were
    never counted.
    """

    JSON = {"Content-Type": "application/json"}

    def test_invalid_beacons_use_up_the_public_tier(self, client: TestClient):
        limit = int(settings.RATE_LIMIT_PUBLIC.split("/")[0])
        beacon = "/api/v1/analytics/track/pageview"

        for i in range(limit):
            response = client.post(beacon, json={"page_path": "/" + "x" * 3000})
            assert response.status_code == 422, f"request {i + 1}: {response.status_code}"

        blocked = client.post(beacon, json={"page_path": "/"})
        assert blocked.status_code == 429
        assert "Retry-After" in blocked.headers

    def test_refresh_over_its_limit_is_refused_before_the_parse(self, client: TestClient):
        """Malformed JSON is a 422 while under 5/minute and a 429 past it."""
        limit = int(settings.RATE_LIMIT_AUTH.split("/")[0])

        for _ in range(limit):
            response = client.post("/api/v1/auth/refresh", content=b"{", headers=self.JSON)
            assert response.status_code == 422

        blocked = client.post("/api/v1/auth/refresh", content=b"{", headers=self.JSON)
        assert blocked.status_code == 429

    def test_unauthenticated_reads_use_up_the_api_tier(self, client: TestClient):
        limit = int(settings.RATE_LIMIT_API.split("/")[0])

        for _ in range(limit):
            assert client.get("/api/v1/auth/me").status_code == 401

        assert client.get("/api/v1/auth/me").status_code == 429


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


class TestForwardedForCannotPickTheBucket:
    """A client-sent X-Forwarded-For entry must not choose the limiter key.

    Six callbacks from fly-proxy's address, each with a fresh leftmost
    X-Forwarded-For entry and the same Fly-Client-IP: the 5/minute auth
    tier must answer the sixth with 429.
    """

    CALLBACK = "/api/v1/auth/github/callback"  # no query: returns before any DB work

    def _statuses(self, asgi_app) -> list[int]:
        proxied = TestClient(asgi_app, client=("172.16.1.114", 40000))
        return [
            proxied.get(
                self.CALLBACK,
                headers={
                    "X-Forwarded-For": f"203.0.113.{i}, 198.51.100.7",
                    "Fly-Client-IP": "198.51.100.7",
                },
                follow_redirects=False,
            ).status_code
            for i in range(6)
        ]

    def test_behind_uvicorn_trusting_every_proxy(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ):
        """The old CMD (--forwarded-allow-ips '*') rotated the key per request."""
        monkeypatch.setenv("FLY_APP_NAME", "portfolio-test")
        wrapped = ProxyHeadersMiddleware(app, trusted_hosts="*")
        assert self._statuses(wrapped) == [302] * 5 + [429]

    def test_without_proxy_headers(self, client: TestClient):
        assert self._statuses(app) == [302] * 5 + [429]


def test_ipv6_addresses_in_one_64_share_the_auth_bucket(client: TestClient):
    """Rotating the interface half of an IPv6 address does not reset the limit."""
    statuses = [
        TestClient(app, client=(f"2001:db8:1:2::{i:x}", 40000))
        .get("/api/v1/auth/github/callback", follow_redirects=False)
        .status_code
        for i in range(1, 7)
    ]
    assert statuses == [302] * 5 + [429]
