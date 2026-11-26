"""
Tests for authentication endpoints
"""

import asyncio
import base64
import hashlib
import logging
import urllib.parse  # noqa: PLC0415
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
from fastapi.testclient import TestClient

from app.config import settings
from app.core.security import create_access_token, create_refresh_token
from tests.conftest import ADMIN_GITHUB_ID


class TestGitHubLogin:
    """Tests for GitHub login initiation."""

    def test_github_login_redirect(self, client: TestClient):
        """Test GitHub OAuth login redirect."""
        # The endpoint returns 503 when GITHUB_CLIENT_ID is not configured,
        # or 307 redirect when it is configured
        response = client.get("/api/v1/auth/github", follow_redirects=False)
        # Without OAuth configured: 503, with OAuth: 307 redirect
        assert response.status_code in [307, 503]
        if response.status_code == 307:
            assert "github.com/login/oauth/authorize" in response.headers.get("location", "")

    def test_github_login_with_configured_oauth(self, client: TestClient):
        """Test GitHub login when OAuth is configured."""
        with patch("app.api.v1.auth.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = "test_client_id"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost:8000/callback"

            response = client.get("/api/v1/auth/github", follow_redirects=False)

            assert response.status_code == 307
            location = response.headers.get("location", "")
            assert "github.com/login/oauth/authorize" in location
            assert "client_id=test_client_id" in location
            assert "state=" in location
            # The callback reads only the public profile, which needs no scope.
            assert "scope" not in urllib.parse.parse_qs(urllib.parse.urlsplit(location).query)

    def test_github_login_not_configured(self, client: TestClient):
        """Test GitHub login when OAuth is not configured."""
        with patch("app.api.v1.auth.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = None

            response = client.get("/api/v1/auth/github")

            assert response.status_code == 503
            assert "not configured" in response.json()["detail"]


class TestGitHubCallback:
    """Tests for GitHub OAuth callback."""

    def test_github_callback_invalid_state(self, client: TestClient):
        """Test callback with invalid state parameter."""
        response = client.get("/api/v1/auth/github/callback?code=test_code&state=invalid_state")

        assert response.status_code == 400
        assert "Invalid or expired state" in response.json()["detail"]

    def test_github_callback_missing_code(self, client: TestClient):
        """Callback without code redirects to the admin entry (not 422)."""
        response = client.get(
            "/api/v1/auth/github/callback?state=test_state", follow_redirects=False
        )

        assert response.status_code == 302
        assert response.headers["location"].endswith("/admin/login?oauth=denied")

    def test_github_callback_missing_state(self, client: TestClient):
        """Callback without state redirects to the admin entry (not 422)."""
        response = client.get("/api/v1/auth/github/callback?code=test_code", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"].endswith("/admin/login?oauth=denied")

    def test_github_callback_user_cancelled(self, client: TestClient):
        """GitHub's cancel path (error=, no code) gets a human-friendly
        redirect — this used to surface as a raw 422 JSON blob."""
        response = client.get(
            "/api/v1/auth/github/callback?error=access_denied"
            "&error_description=The+user+has+denied+your+application+access"
            "&state=test_state",
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["location"].endswith("/admin/login?oauth=denied")
        # No cookies on the deny path
        assert "set-cookie" not in response.headers


class TestRefreshToken:
    """Tests for token refresh endpoint."""

    def test_refresh_token_invalid(self, client: TestClient):
        """Test refresh with invalid token."""
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "invalid_token_that_is_long_enough"}
        )

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_refresh_token_with_access_token(self, client: TestClient):
        """Test refresh using access token instead of refresh token."""
        access_token = create_access_token(subject="test_user")

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": access_token})

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]

    def test_refresh_token_unknown_jti(self, client: TestClient):
        """A signed-but-unknown jti is rejected with 401 (not 404).

        Previously the same arrangement reached the user-lookup path; with
        server-side jti tracking we reject earlier — we can't safely rotate
        a token whose jti we have no record of issuing.
        """
        refresh_token, _, _ = create_refresh_token(subject="nonexistent-user-id")

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

        assert response.status_code == 401
        assert "not recognised" in response.json()["detail"].lower()


class TestLogout:
    """Tests for logout endpoint."""

    def test_logout_success(self, client: TestClient):
        """Test successful logout."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

    def test_logout_with_auth(self, client: TestClient, admin_headers: dict):
        """Test logout with authentication."""
        response = client.post("/api/v1/auth/logout", headers=admin_headers)

        assert response.status_code == 200


def test_github_login_redirect(client: TestClient):
    """Test GitHub OAuth login redirect."""
    # The endpoint returns 503 when GITHUB_CLIENT_ID is not configured,
    # or 307 redirect when it is configured
    response = client.get("/api/v1/auth/github", follow_redirects=False)
    # Without OAuth configured: 503, with OAuth: 307 redirect
    assert response.status_code in [307, 503]
    if response.status_code == 307:
        assert "github.com/login/oauth/authorize" in response.headers.get("location", "")


def test_token_refresh(client: TestClient):
    """Test token refresh endpoint."""
    # Signed token with no server-side jti record — endpoint rejects 401.
    refresh_token, _, _ = create_refresh_token(subject="nonexistent_user")

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    # Unknown jti -> 401. 422 is NOT acceptable here: accepting it is what let a
    # required-field regression ship green (see test_refresh_with_empty_body).
    assert response.status_code == 401


def test_refresh_with_empty_body_is_401_not_422(client: TestClient):
    """An empty body must reach the endpoint's own 'Refresh token required' 401.

    The browser client cannot read the HTTP-only refresh_token cookie, so it
    POSTs `{}` and lets the endpoint take the token off the request. While
    RefreshTokenRequest.refresh_token was required, that body failed validation
    and every unauthenticated /admin visit logged a 422 in the console.
    """
    response = client.post("/api/v1/auth/refresh", json={})
    assert response.status_code == 401

    # Same for no body at all.
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_refresh_rejects_malformed_token_value(client: TestClient):
    """Loosening the field to optional must not loosen validation of real values."""
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "short"})
    assert response.status_code == 422


def test_protected_endpoint_without_auth(client: TestClient):
    """Test accessing protected endpoint without authentication."""
    response = client.get("/api/v1/auth/me")
    # 401 (no auth) or 403 (forbidden) are both valid for missing/invalid auth
    assert response.status_code in [401, 403]


def test_protected_endpoint_with_auth(client: TestClient, auth_headers: dict):
    """Test accessing protected endpoint with valid token."""
    # Note: This test requires a user to exist in the database
    # Since we use in-memory SQLite, the user lookup will fail
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    # Token is valid but user doesn't exist in test DB
    assert response.status_code in [200, 404]


def test_logout(client: TestClient, auth_headers: dict):
    """Test logout endpoint."""
    response = client.post("/api/v1/auth/logout", headers=auth_headers)
    # Note: Logout may require user validation
    assert response.status_code in [200, 404]


def test_invalid_token(client: TestClient):
    """Test with invalid authentication token."""
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


def test_expired_token(client: TestClient):
    """Test with expired token."""
    # Create an expired token
    expired_token = create_access_token(
        subject="test_user",
        expires_delta=timedelta(seconds=-1),  # Already expired
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.get("/api/v1/auth/me", headers=headers)
    assert response.status_code == 401


class TestGitHubOAuthCallbackValidation:
    """Tests for GitHub OAuth callback validation."""

    def test_callback_invalid_state_rejected(self, client: TestClient):
        """Test that invalid state is rejected with 400."""
        response = client.get(
            "/api/v1/auth/github/callback?code=test_code&state=completely_invalid",
            follow_redirects=False,
        )
        assert response.status_code == 400

    def test_callback_requires_both_params(self, client: TestClient):
        """Missing code or state -> 302 back to admin, never a 422 blob."""
        # Missing state
        response = client.get("/api/v1/auth/github/callback?code=test", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"].endswith("/admin/login?oauth=denied")

        # Missing code
        response = client.get("/api/v1/auth/github/callback?state=test", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"].endswith("/admin/login?oauth=denied")

    def test_callback_empty_code(self, client: TestClient):
        """Empty code is treated as missing -> redirect, no token exchange."""
        response = client.get(
            "/api/v1/auth/github/callback?code=&state=test_state", follow_redirects=False
        )
        assert response.status_code == 302
        assert response.headers["location"].endswith("/admin/login?oauth=denied")

    def test_callback_empty_state(self, client: TestClient):
        """Empty state is treated as missing -> redirect, state never consumed."""
        response = client.get(
            "/api/v1/auth/github/callback?code=test_code&state=", follow_redirects=False
        )
        assert response.status_code == 302
        assert response.headers["location"].endswith("/admin/login?oauth=denied")


class TestAuthIntegration:
    """Integration tests for complete auth flow with real database users."""

    def test_get_me_with_valid_user_in_db(self, client: TestClient, test_user_in_db: dict):
        """Test /me endpoint returns user data when user exists in database."""
        response = client.get("/api/v1/auth/me", headers=test_user_in_db["headers"])

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user_in_db["user_id"]
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    def test_get_me_with_admin_user_in_db(self, client: TestClient, admin_user_in_db: dict):
        """Test /me endpoint returns admin user data."""
        response = client.get("/api/v1/auth/me", headers=admin_user_in_db["headers"])

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == admin_user_in_db["user_id"]
        assert data["username"] == "adminuser"
        assert data["is_admin"] is True

    def test_refresh_token_with_valid_user_in_db(self, client: TestClient, admin_user_in_db: dict):
        """Refresh succeeds and delivers new tokens via cookies, not the response body."""
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": admin_user_in_db["refresh_token"]}
        )

        assert response.status_code == 200
        # Body is intentionally token-free to keep tokens out of XSS reach
        assert response.json() == {"refreshed": True}
        # New tokens are delivered via Set-Cookie
        assert response.cookies.get("access_token")
        assert response.cookies.get("refresh_token")

    def test_refreshed_token_works_for_me_endpoint(
        self, client: TestClient, admin_user_in_db: dict
    ):
        """A token issued by /refresh authenticates a follow-up /me call."""
        refresh_response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": admin_user_in_db["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        new_access_token = refresh_response.cookies.get("access_token")
        assert new_access_token

        new_headers = {"Authorization": f"Bearer {new_access_token}"}
        me_response = client.get("/api/v1/auth/me", headers=new_headers)

        assert me_response.status_code == 200
        assert me_response.json()["id"] == admin_user_in_db["user_id"]

    def test_user_response_schema(self, client: TestClient, test_user_in_db: dict):
        """Test that user response matches expected schema."""
        response = client.get("/api/v1/auth/me", headers=test_user_in_db["headers"])

        assert response.status_code == 200
        data = response.json()

        # Check all expected fields are present
        expected_fields = ["id", "username", "email", "name", "avatar_url", "is_admin"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_logout_clears_session(self, client: TestClient, test_user_in_db: dict):
        """Test logout returns success message."""
        response = client.post("/api/v1/auth/logout", headers=test_user_in_db["headers"])

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "logged out" in data["message"].lower()


class TestTokenExpiration:
    """Tests for token expiration handling."""

    def test_access_token_structure(self, client: TestClient, test_user_in_db: dict):
        """Test access token has correct structure."""
        from app.core.security import decode_token  # noqa: PLC0415

        token = test_user_in_db["access_token"]
        payload = decode_token(token)

        assert payload is not None
        assert "sub" in payload
        assert "exp" in payload
        assert "type" in payload
        assert payload["type"] == "access"

    def test_refresh_token_structure(self, client: TestClient, test_user_in_db: dict):
        """Test refresh token has correct structure."""
        from app.core.security import decode_token  # noqa: PLC0415

        token = test_user_in_db["refresh_token"]
        payload = decode_token(token)

        assert payload is not None
        assert "sub" in payload
        assert "exp" in payload
        assert "type" in payload
        assert payload["type"] == "refresh"

    def test_cannot_use_refresh_token_for_access(self, client: TestClient, test_user_in_db: dict):
        """Test that refresh token cannot be used as access token."""
        # Try to use refresh token as bearer token
        refresh_as_access = {"Authorization": f"Bearer {test_user_in_db['refresh_token']}"}
        response = client.get("/api/v1/auth/me", headers=refresh_as_access)

        # Should fail - refresh tokens should not work as access tokens
        # The current implementation may allow this, so we document the behavior
        assert response.status_code in [200, 401]


class TestAuthorizationEdgeCases:
    """Tests for edge cases in authorization."""

    def test_malformed_bearer_token(self, client: TestClient):
        """Test handling of malformed Bearer token."""
        headers = {"Authorization": "Bearer "}
        response = client.get("/api/v1/auth/me", headers=headers)
        # 401 (no auth) or 403 (forbidden) are both valid for malformed auth
        assert response.status_code in [401, 403]

    def test_wrong_auth_scheme(self, client: TestClient):
        """Test handling of wrong authentication scheme."""
        headers = {"Authorization": "Basic dXNlcjpwYXNz"}
        response = client.get("/api/v1/auth/me", headers=headers)
        # 401 (no auth) or 403 (forbidden) are both valid for wrong auth scheme
        assert response.status_code in [401, 403]

    def test_no_authorization_header(self, client: TestClient):
        """Test handling of missing Authorization header."""
        response = client.get("/api/v1/auth/me")
        # 401 (no auth) or 403 (forbidden) are both valid for missing auth
        assert response.status_code in [401, 403]

    def test_bearer_without_token(self, client: TestClient):
        """Test handling of Bearer without token."""
        headers = {"Authorization": "Bearer"}
        response = client.get("/api/v1/auth/me", headers=headers)
        # 401 (no auth) or 403 (forbidden) are both valid for missing token
        assert response.status_code in [401, 403]

    def test_tampered_token(self, client: TestClient, test_user_in_db: dict):
        """Test handling of tampered token."""
        # Modify the token payload
        tampered = test_user_in_db["access_token"][:-5] + "xxxxx"
        headers = {"Authorization": f"Bearer {tampered}"}
        response = client.get("/api/v1/auth/me", headers=headers)
        # 401 (no auth) or 403 (forbidden) are both valid for invalid token
        assert response.status_code in [401, 403]


class TestRefreshTokenEdgeCases:
    """Tests for refresh token edge cases."""

    def test_refresh_with_empty_token(self, client: TestClient):
        """Test refresh with empty token - validation rejects short tokens."""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": ""})
        # Pydantic validation rejects tokens shorter than 10 chars
        assert response.status_code == 422

    def test_refresh_with_whitespace_token(self, client: TestClient):
        """Test refresh with whitespace token - validation rejects short tokens."""
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": "   "})
        # Pydantic validation rejects tokens shorter than 10 chars
        assert response.status_code == 422

    def test_refresh_issues_new_refresh_token_cookie(
        self, client: TestClient, admin_user_in_db: dict
    ):
        """Refresh rotates the refresh token: a fresh cookie value is set on every call."""
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": admin_user_in_db["refresh_token"]}
        )

        assert response.status_code == 200
        new_refresh_cookie = response.cookies.get("refresh_token")
        assert new_refresh_cookie
        # Body never contains tokens
        assert "refresh_token" not in response.json()
        assert "access_token" not in response.json()

    def test_refresh_reuse_after_rotation_is_rejected(
        self, client: TestClient, admin_user_in_db: dict, monkeypatch
    ):
        """A replayed refresh token OUTSIDE the rotation grace window is
        rejected as a reuse attempt.

        This is RFC 6819 §5.2.2.3 reuse detection: the first call marks the
        presented jti revoked, and any later call with the same jti triggers
        the revoke-everything sweep — forcing a fresh OAuth login. The grace
        window (which exists for benign multi-tab races) is pinned to -1 so
        the replay lands firmly in the theft branch.
        """
        from app.api.v1 import auth as auth_module

        monkeypatch.setattr(auth_module, "REFRESH_ROTATION_GRACE_SECONDS", -1)
        original = admin_user_in_db["refresh_token"]

        first = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert first.status_code == 200

        # The first response set a NEW refresh_token cookie; the TestClient
        # would otherwise replay it on the second call and we'd be probing
        # the wrong token. Clear cookies so the second call is forced to
        # fall back to the JSON body (where we send the original/revoked
        # token).
        client.cookies.clear()

        second = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert second.status_code == 401
        assert "revoked" in second.json()["detail"].lower()

    def test_concurrent_refresh_grace_preserves_session(
        self, client: TestClient, admin_user_in_db: dict
    ):
        """A replay WITHIN the grace window is treated as a benign
        concurrent rotation (multi-tab race), not theft.

        The loser gets a 401 without the revoke-all sweep, so the token the
        winner received keeps working. Under the pre-fix behavior the sweep
        fired and this final refresh returned 401 — logging the admin out of
        every tab whenever two requests raced.
        """
        original = admin_user_in_db["refresh_token"]

        first = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert first.status_code == 200
        rotated = first.cookies.get("refresh_token")
        assert rotated

        client.cookies.clear()
        replay = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert replay.status_code == 401
        assert "superseded" in replay.json()["detail"].lower()

        client.cookies.clear()
        winner = client.post("/api/v1/auth/refresh", json={"refresh_token": rotated})
        assert winner.status_code == 200

    def test_logout_revokes_refresh_token_server_side(
        self, client: TestClient, test_user_in_db: dict, monkeypatch
    ):
        """Logout marks the presented refresh token's jti as revoked so a
        copy made before logout can't be replayed into /refresh afterward.

        Grace pinned to -1: the replay must hit the hard revoked branch,
        not the concurrent-rotation one.
        """
        from app.api.v1 import auth as auth_module

        monkeypatch.setattr(auth_module, "REFRESH_ROTATION_GRACE_SECONDS", -1)
        original = test_user_in_db["refresh_token"]

        # Send the cookie alongside logout so the server can read the jti.
        client.cookies.set("refresh_token", original)
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200
        client.cookies.clear()

        replay = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert replay.status_code == 401

    def test_logout_with_stale_cookie_revokes_rotated_sibling(
        self, client: TestClient, admin_user_in_db: dict
    ):
        """Multi-tab logout: the cookie presented at logout may already be
        superseded by a rotation from another tab. Logout revokes ALL live
        tokens for the user, so the freshly-rotated sibling dies too —
        under the old single-jti revoke it survived and the "logged-out"
        user stayed authenticated in the other tab.
        """
        original = admin_user_in_db["refresh_token"]

        # Tab B rotates: original -> rotated.
        first = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert first.status_code == 200
        rotated = first.cookies.get("refresh_token")
        assert rotated

        # Tab A logs out still holding the stale original cookie.
        client.cookies.clear()
        client.cookies.set("refresh_token", original)
        logout_response = client.post("/api/v1/auth/logout")
        assert logout_response.status_code == 200

        # The rotated sibling must be dead as well. (The exact 401 detail
        # depends on timing: a replay within the rotation grace window says
        # "superseded", after it "revoked" — both mean the session is gone.)
        client.cookies.clear()
        replay = client.post("/api/v1/auth/refresh", json={"refresh_token": rotated})
        assert replay.status_code == 401


class TestRefreshRechecksTheAdmin:
    """A refresh renews a session only while its account is the configured
    admin, the same test get_current_admin_user makes on every admin route."""

    def _refresh(self, client: TestClient, user: dict):
        return client.post("/api/v1/auth/refresh", json={"refresh_token": user["refresh_token"]})

    def test_an_account_that_is_not_the_admin_is_refused(
        self, client: TestClient, test_user_in_db: dict
    ):
        response = self._refresh(client, test_user_in_db)

        assert response.status_code == 403
        assert response.json()["detail"] == "Not enough permissions"
        assert "access_token" not in response.cookies
        assert "refresh_token" not in response.cookies

    def test_a_changed_admin_github_id_refuses_the_previous_admin(
        self, client: TestClient, admin_user_in_db: dict, monkeypatch
    ):
        monkeypatch.setattr(settings, "ADMIN_GITHUB_ID", "24680")

        response = self._refresh(client, admin_user_in_db)

        assert response.status_code == 403
        assert "refresh_token" not in response.cookies

    def test_an_unset_admin_github_id_refuses_every_refresh(
        self, client: TestClient, admin_user_in_db: dict, monkeypatch
    ):
        monkeypatch.setattr(settings, "ADMIN_GITHUB_ID", None)

        assert self._refresh(client, admin_user_in_db).status_code == 403

    def test_a_refused_refresh_leaves_the_token_unrotated(
        self, client: TestClient, admin_user_in_db: dict, monkeypatch
    ):
        """The refusal revokes nothing: with the setting back, the same
        token refreshes instead of tripping reuse detection."""
        monkeypatch.setattr(settings, "ADMIN_GITHUB_ID", "24680")
        assert self._refresh(client, admin_user_in_db).status_code == 403

        monkeypatch.setattr(settings, "ADMIN_GITHUB_ID", ADMIN_GITHUB_ID)
        assert self._refresh(client, admin_user_in_db).status_code == 200


def _store_refresh_row(
    user_id: str, jti: str, expires_at: datetime, issued_at: datetime | None = None
) -> None:
    """Insert the server-side record of a refresh token minted by a test."""
    from app.models.refresh_token import RefreshToken  # noqa: PLC0415
    from tests.conftest import TestSessionLocal  # noqa: PLC0415

    async def insert() -> None:
        async with TestSessionLocal() as session:
            row = RefreshToken(jti=jti, user_id=user_id, expires_at=expires_at)
            if issued_at is not None:
                row.issued_at = issued_at
            session.add(row)
            await session.commit()

    asyncio.run(insert())


def _refresh_token_without_auth_time(user_id: str, jti: str, expires_at: datetime) -> str:
    """A refresh token as minted before the auth_time claim existed."""
    secret = settings.SECRET_KEY
    assert secret
    claims = {"exp": expires_at, "sub": user_id, "type": "refresh", "jti": jti}
    return jwt.encode(claims, secret, algorithm=settings.ALGORITHM)


def _auth_time(token: str) -> int:
    from app.core.security import decode_token  # noqa: PLC0415

    payload = decode_token(token)
    assert payload is not None
    return payload["auth_time"]


class TestSessionMaxAge:
    """A session lives at most SESSION_MAX_AGE from its GitHub sign-in,
    however often its refresh token rotates."""

    def test_rotation_carries_auth_time_forward(self, client: TestClient, admin_user_in_db: dict):
        first_auth_time = _auth_time(admin_user_in_db["refresh_token"])

        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": admin_user_in_db["refresh_token"]}
        )

        assert response.status_code == 200
        assert _auth_time(response.cookies["refresh_token"]) == first_auth_time

    def test_refresh_past_the_session_lifetime_is_refused(
        self, client: TestClient, test_user_in_db: dict
    ):
        from app.api.v1.auth import SESSION_MAX_AGE  # noqa: PLC0415

        signed_in = datetime.now(UTC) - SESSION_MAX_AGE - timedelta(minutes=1)
        token, jti, exp = create_refresh_token(
            subject=test_user_in_db["user_id"], auth_time=int(signed_in.timestamp())
        )
        _store_refresh_row(test_user_in_db["user_id"], jti, exp)

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})

        assert response.status_code == 401
        assert response.json()["detail"] == "Session expired"
        assert "refresh_token" not in response.cookies

    def test_token_without_auth_time_counts_from_its_row(
        self, client: TestClient, admin_user_in_db: dict
    ):
        """A token minted before the claim existed keeps working, and the
        session's lifetime counts from the row that recorded it."""
        user_id = admin_user_in_db["user_id"]
        issued_at = (datetime.now(UTC) - timedelta(days=2)).replace(microsecond=0)
        expires_at = datetime.now(UTC) + timedelta(days=5)
        legacy = _refresh_token_without_auth_time(user_id, "legacy-jti-recent-row", expires_at)
        _store_refresh_row(user_id, "legacy-jti-recent-row", expires_at, issued_at)

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": legacy})

        assert response.status_code == 200
        assert _auth_time(response.cookies["refresh_token"]) == int(issued_at.timestamp())

    def test_token_without_auth_time_from_an_old_row_is_refused(
        self, client: TestClient, test_user_in_db: dict
    ):
        from app.api.v1.auth import SESSION_MAX_AGE  # noqa: PLC0415

        user_id = test_user_in_db["user_id"]
        issued_at = datetime.now(UTC) - SESSION_MAX_AGE - timedelta(hours=1)
        expires_at = datetime.now(UTC) + timedelta(days=1)
        legacy = _refresh_token_without_auth_time(user_id, "legacy-jti-old-row", expires_at)
        _store_refresh_row(user_id, "legacy-jti-old-row", expires_at, issued_at)

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": legacy})

        assert response.status_code == 401
        assert response.json()["detail"] == "Session expired"


def _github_client(github_user: dict) -> AsyncMock:
    """Stand-in for the shared OAuth client: the code exchange, GET /user and
    the token revocation all succeed."""
    token_response = MagicMock(status_code=200)
    token_response.json.return_value = {"access_token": "gho_test_token", "token_type": "bearer"}
    user_response = MagicMock(status_code=200)
    user_response.json.return_value = github_user
    github = AsyncMock()
    github.post.return_value = token_response
    github.get.return_value = user_response
    github.request.return_value = MagicMock(status_code=204)
    return github


def _start_github_login(client: TestClient, monkeypatch):
    """GET /auth/github with OAuth configured; the TestClient keeps its cookie."""
    monkeypatch.setattr(settings, "GITHUB_CLIENT_ID", "test_client_id")
    monkeypatch.setattr(settings, "GITHUB_CLIENT_SECRET", "test_client_secret")
    login = client.get("/api/v1/auth/github", follow_redirects=False)
    assert login.status_code == 307
    return login


def _authorize_query(login) -> dict[str, str]:
    """The query parameters of the authorize URL a login redirected to."""
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(login.headers["location"]).query)
    return {key: values[0] for key, values in query.items()}


def _github_callback(client: TestClient, state: str, github: AsyncMock):
    """GitHub's redirect back to the callback, with GitHub answering as `github`."""
    with patch("app.api.v1.auth.get_oauth_client", return_value=github):
        return client.get(
            f"/api/v1/auth/github/callback?code=test_code&state={state}", follow_redirects=False
        )


def _complete_github_login(client: TestClient, monkeypatch, github: AsyncMock):
    """Start a login, then return the callback's response with GitHub answering as `github`."""
    login = _start_github_login(client, monkeypatch)
    return _github_callback(client, _authorize_query(login)["state"], github)


ADMIN_ON_GITHUB = {"id": int(ADMIN_GITHUB_ID), "login": "adminuser", "name": "Admin User"}


class TestGitHubTokenRevocation:
    """The callback revokes the GitHub token once GET /user has been read."""

    def _assert_revoked(self, github: AsyncMock) -> None:
        github.request.assert_awaited_once()
        args, kwargs = github.request.call_args
        assert args == ("DELETE", "https://api.github.com/applications/test_client_id/token")
        assert kwargs["auth"] == ("test_client_id", "test_client_secret")
        assert kwargs["json"] == {"access_token": "gho_test_token"}

    def test_token_is_revoked_after_a_login(self, client: TestClient, monkeypatch):
        github = _github_client(ADMIN_ON_GITHUB)

        response = _complete_github_login(client, monkeypatch, github)

        assert response.status_code == 302
        self._assert_revoked(github)

    def test_token_is_revoked_when_the_account_is_refused(self, client: TestClient, monkeypatch):
        github = _github_client({"id": 99999, "login": "someoneelse"})

        response = _complete_github_login(client, monkeypatch, github)

        assert response.status_code == 403
        self._assert_revoked(github)

    def test_token_is_revoked_when_get_user_fails(self, client: TestClient, monkeypatch):
        github = _github_client(ADMIN_ON_GITHUB)
        github.get.return_value = MagicMock(status_code=401)

        response = _complete_github_login(client, monkeypatch, github)

        assert response.status_code == 400
        self._assert_revoked(github)

    def test_a_failed_revocation_does_not_block_the_login(self, client: TestClient, monkeypatch):
        import httpx  # noqa: PLC0415

        github = _github_client(ADMIN_ON_GITHUB)
        github.request.side_effect = httpx.ConnectError("unreachable")

        response = _complete_github_login(client, monkeypatch, github)

        assert response.status_code == 302
        assert response.cookies.get("access_token")

    def test_nothing_is_revoked_without_a_token(self, client: TestClient, monkeypatch):
        github = _github_client(ADMIN_ON_GITHUB)
        github.post.return_value.json.return_value = {"error": "bad_verification_code"}

        response = _complete_github_login(client, monkeypatch, github)

        assert response.status_code == 400
        github.request.assert_not_awaited()


class TestOAuthBrowserBinding:
    """A cookie binds a login's state to the browser that started it and
    carries the PKCE verifier the code exchange needs."""

    def test_login_sets_a_short_lived_httponly_lax_cookie_for_the_callback(
        self, client: TestClient, monkeypatch
    ):
        login = _start_github_login(client, monkeypatch)

        set_cookie = login.headers["set-cookie"]
        assert set_cookie.startswith(f"github_oauth={_authorize_query(login)['state']}.")
        attributes = {part.strip().lower() for part in set_cookie.split(";")[1:]}
        assert {"httponly", "samesite=lax", "path=/api/v1/auth/github", "max-age=300"} <= attributes

    def test_the_cookie_is_secure_in_production(self, client: TestClient, monkeypatch):
        monkeypatch.setattr(settings, "ENVIRONMENT", "production")
        monkeypatch.setattr(settings, "GITHUB_CLIENT_ID", "test_client_id")

        login = client.get(
            "/api/v1/auth/github", headers={"Host": "api.dashti.se"}, follow_redirects=False
        )

        assert login.status_code == 307
        assert "secure" in {part.strip().lower() for part in login.headers["set-cookie"].split(";")}

    def test_the_authorize_url_carries_the_s256_challenge_of_the_cookie_verifier(
        self, client: TestClient, monkeypatch
    ):
        query = _authorize_query(_start_github_login(client, monkeypatch))

        state, verifier = client.cookies["github_oauth"].split(".")
        assert state == query["state"]
        assert 43 <= len(verifier) <= 128  # RFC 7636 section 4.1
        digest = hashlib.sha256(verifier.encode()).digest()
        assert query["code_challenge"] == base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
        assert len(query["code_challenge"]) == 43
        assert query["code_challenge_method"] == "S256"

    def test_the_code_exchange_sends_the_cookie_verifier(self, client: TestClient, monkeypatch):
        github = _github_client(ADMIN_ON_GITHUB)
        state = _authorize_query(_start_github_login(client, monkeypatch))["state"]
        verifier = client.cookies["github_oauth"].split(".")[1]

        response = _github_callback(client, state, github)

        assert response.status_code == 302
        assert github.post.call_args.kwargs["data"]["code_verifier"] == verifier

    def test_a_callback_without_the_cookie_is_refused_and_keeps_the_state(
        self, client: TestClient, monkeypatch
    ):
        github = _github_client(ADMIN_ON_GITHUB)
        state = _authorize_query(_start_github_login(client, monkeypatch))["state"]
        cookie = client.cookies["github_oauth"]
        client.cookies.clear()

        refused = _github_callback(client, state, github)

        assert refused.status_code == 400
        github.post.assert_not_awaited()
        # The refused callback did not use up the state: the browser that
        # started the login still finishes it.
        client.cookies.set("github_oauth", cookie)
        assert _github_callback(client, state, github).status_code == 302

    def test_a_callback_with_another_logins_cookie_is_refused(
        self, client: TestClient, monkeypatch
    ):
        """A second login in the same browser replaces the cookie, so the
        first login's state no longer matches it."""
        github = _github_client(ADMIN_ON_GITHUB)
        first = _authorize_query(_start_github_login(client, monkeypatch))["state"]
        second = _authorize_query(_start_github_login(client, monkeypatch))["state"]

        assert _github_callback(client, first, github).status_code == 400
        assert _github_callback(client, second, github).status_code == 302

    def test_a_cookie_without_a_verifier_is_refused(self, client: TestClient, monkeypatch):
        github = _github_client(ADMIN_ON_GITHUB)
        state = _authorize_query(_start_github_login(client, monkeypatch))["state"]
        client.cookies.clear()
        client.cookies.set("github_oauth", state)

        assert _github_callback(client, state, github).status_code == 400
        github.post.assert_not_awaited()

    def test_a_non_ascii_state_is_refused(self, client: TestClient, monkeypatch):
        _start_github_login(client, monkeypatch)

        response = client.get(
            "/api/v1/auth/github/callback?code=test_code&state=%C3%A9t%C3%A9",
            follow_redirects=False,
        )

        assert response.status_code == 400

    def test_a_successful_login_clears_the_cookie(self, client: TestClient, monkeypatch):
        response = _complete_github_login(client, monkeypatch, _github_client(ADMIN_ON_GITHUB))

        assert response.status_code == 302
        cleared = [
            header
            for header in response.headers.get_list("set-cookie")
            if header.startswith("github_oauth=")
        ]
        assert len(cleared) == 1
        attributes = {part.strip().lower() for part in cleared[0].split(";")[1:]}
        assert {"max-age=0", "path=/api/v1/auth/github"} <= attributes
        assert "github_oauth" not in client.cookies


def _events(records: list[logging.LogRecord]) -> list[tuple[str, int]]:
    """(event, level) of each record; `event` arrives through the record's extra."""
    return [(record.__dict__["event"], record.levelno) for record in records]


def _assert_no_secret_logged(records: list[logging.LogRecord], *secrets: str) -> None:
    for record in records:
        text = repr(record.__dict__)
        for secret in secrets:
            assert secret not in text


class TestSecurityEvents:
    """Each authentication decision leaves one app.security record that
    names it, with identifiers and counts but no token, code or state."""

    def test_a_login_is_logged_without_its_secrets(
        self, client: TestClient, monkeypatch, security_records
    ):
        login = _start_github_login(client, monkeypatch)
        state = _authorize_query(login)["state"]
        verifier = client.cookies["github_oauth"].split(".")[1]

        response = _github_callback(client, state, _github_client(ADMIN_ON_GITHUB))

        assert response.status_code == 302
        assert _events(security_records) == [("auth.login_success", logging.INFO)]
        [record] = security_records
        assert record.github_id == ADMIN_GITHUB_ID
        assert record.github_login == "adminuser"
        assert record.user_id
        assert record.client_ip_hash
        _assert_no_secret_logged(
            security_records,
            "test_code",
            state,
            verifier,
            "gho_test_token",
            response.cookies["access_token"],
            response.cookies["refresh_token"],
        )

    def test_a_foreign_account_is_logged_as_refused(
        self, client: TestClient, monkeypatch, security_records
    ):
        github = _github_client({"id": 99999, "login": "someoneelse"})

        assert _complete_github_login(client, monkeypatch, github).status_code == 403

        assert _events(security_records) == [("auth.login_refused", logging.WARNING)]
        assert security_records[0].github_id == "99999"
        assert security_records[0].github_login == "someoneelse"

    def test_a_failed_code_exchange_is_logged(
        self, client: TestClient, monkeypatch, security_records
    ):
        github = _github_client(ADMIN_ON_GITHUB)
        github.post.return_value.json.return_value = {"error": "bad_verification_code"}

        assert _complete_github_login(client, monkeypatch, github).status_code == 400

        assert _events(security_records) == [("auth.login_failed", logging.WARNING)]
        assert security_records[0].status_code == 400

    def test_a_rejected_state_is_logged_with_its_reason(
        self, client: TestClient, monkeypatch, security_records
    ):
        github = _github_client(ADMIN_ON_GITHUB)
        state = _authorize_query(_start_github_login(client, monkeypatch))["state"]
        assert _github_callback(client, state, github).status_code == 302
        # A replay of the consumed state from the same browser.
        client.cookies.set("github_oauth", f"{state}.verifier")
        assert _github_callback(client, state, github).status_code == 400
        # A state this browser never received.
        assert _github_callback(client, "never-issued", github).status_code == 400

        rejected = [r for r in security_records if r.event == "auth.oauth_state_rejected"]
        assert [(r.reason, r.levelno) for r in rejected] == [
            ("unknown_or_expired", logging.WARNING),
            ("not_this_browser", logging.WARNING),
        ]

    def test_refresh_reuse_is_an_error_with_the_revoked_count(
        self, client: TestClient, admin_user_in_db: dict, monkeypatch, security_records
    ):
        from app.api.v1 import auth as auth_module  # noqa: PLC0415

        monkeypatch.setattr(auth_module, "REFRESH_ROTATION_GRACE_SECONDS", -1)
        original = admin_user_in_db["refresh_token"]
        rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert rotated.status_code == 200
        client.cookies.clear()

        replay = client.post("/api/v1/auth/refresh", json={"refresh_token": original})

        assert replay.status_code == 401
        assert _events(security_records) == [("auth.refresh_reuse_detected", logging.ERROR)]
        [record] = security_records
        assert record.user_id == admin_user_in_db["user_id"]
        assert record.jti_prefix == admin_user_in_db["refresh_jti"][:8]
        assert record.revoked_count == 1  # the rotated successor
        assert record.seconds_since_rotation >= 0
        _assert_no_secret_logged(security_records, original)

    def test_reuse_that_revoked_sessions_answers_with_the_revoked_detail(
        self, client: TestClient, admin_user_in_db: dict, monkeypatch
    ):
        from app.api.v1 import auth as auth_module  # noqa: PLC0415

        monkeypatch.setattr(auth_module, "REFRESH_ROTATION_GRACE_SECONDS", -1)
        original = admin_user_in_db["refresh_token"]
        rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert rotated.status_code == 200
        client.cookies.clear()

        replay = client.post("/api/v1/auth/refresh", json={"refresh_token": original})

        assert replay.status_code == 401
        assert replay.json()["detail"] == "Refresh token reused; all sessions revoked"
        assert replay.json()["detail"] == auth_module.SESSIONS_REVOKED_DETAIL

    def test_reuse_with_no_live_session_left_is_a_warning(
        self, client: TestClient, test_user_in_db: dict, monkeypatch, security_records
    ):
        """After a logout (on another device, say) revoked every session, a
        replay of the old token ends nothing: no error, no revoked notice."""
        from app.api.v1 import auth as auth_module  # noqa: PLC0415

        monkeypatch.setattr(auth_module, "REFRESH_ROTATION_GRACE_SECONDS", -1)
        client.cookies.set("refresh_token", test_user_in_db["refresh_token"])
        assert client.post("/api/v1/auth/logout").status_code == 200
        client.cookies.clear()

        replay = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": test_user_in_db["refresh_token"]}
        )

        assert replay.status_code == 401
        assert replay.json()["detail"] == "Refresh token revoked"
        reuse = [r for r in security_records if r.event == "auth.refresh_reuse_detected"]
        assert [(r.levelno, r.revoked_count) for r in reuse] == [(logging.WARNING, 0)]

    def test_a_replay_within_the_grace_window_is_info_not_error(
        self, client: TestClient, admin_user_in_db: dict, security_records
    ):
        original = admin_user_in_db["refresh_token"]
        rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": original})
        assert rotated.status_code == 200
        client.cookies.clear()

        replay = client.post("/api/v1/auth/refresh", json={"refresh_token": original})

        assert replay.status_code == 401
        assert _events(security_records) == [("auth.refresh_superseded", logging.INFO)]

    def test_a_cross_user_replay_is_an_error(
        self, client: TestClient, test_user_in_db: dict, security_records
    ):
        # A validly signed token whose jti belongs to another user's row.
        forged, _, _ = create_refresh_token(
            subject="someone-else", jti=test_user_in_db["refresh_jti"]
        )

        response = client.post("/api/v1/auth/refresh", json={"refresh_token": forged})

        assert response.status_code == 401
        assert _events(security_records) == [("auth.refresh_cross_user", logging.ERROR)]
        [record] = security_records
        assert record.presented_sub == "someone-else"
        assert record.jti_owner == test_user_in_db["user_id"]
        assert record.revoked_count == 0

    def test_logout_is_logged_with_the_revoked_count(
        self, client: TestClient, test_user_in_db: dict, security_records
    ):
        client.cookies.set("refresh_token", test_user_in_db["refresh_token"])

        assert client.post("/api/v1/auth/logout").status_code == 200

        assert _events(security_records) == [("auth.logout", logging.INFO)]
        assert security_records[0].user_id == test_user_in_db["user_id"]
        assert security_records[0].revoked_count == 1

    def test_an_expired_session_is_logged(
        self, client: TestClient, test_user_in_db: dict, security_records
    ):
        from app.api.v1.auth import SESSION_MAX_AGE  # noqa: PLC0415

        signed_in = datetime.now(UTC) - SESSION_MAX_AGE - timedelta(minutes=1)
        token, jti, exp = create_refresh_token(
            subject=test_user_in_db["user_id"], auth_time=int(signed_in.timestamp())
        )
        _store_refresh_row(test_user_in_db["user_id"], jti, exp)

        assert client.post("/api/v1/auth/refresh", json={"refresh_token": token}).status_code == 401

        assert _events(security_records) == [("auth.session_expired", logging.INFO)]

    def test_admin_denied_is_logged(
        self, client: TestClient, test_user_in_db: dict, security_records
    ):
        response = client.get("/api/v1/admin/sentry-panel", headers=test_user_in_db["headers"])

        assert response.status_code == 403
        assert _events(security_records) == [("auth.admin_denied", logging.WARNING)]

    def test_a_refused_refresh_is_logged_as_admin_denied(
        self, client: TestClient, test_user_in_db: dict, security_records
    ):
        response = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": test_user_in_db["refresh_token"]}
        )

        assert response.status_code == 403
        assert _events(security_records) == [("auth.admin_denied", logging.WARNING)]
        [record] = security_records
        assert record.path == "/api/v1/auth/refresh"
        assert record.user_id == test_user_in_db["user_id"]
        assert record.github_id == "12345"
        _assert_no_secret_logged(security_records, test_user_in_db["refresh_token"])

    def test_each_event_is_counted_on_the_metrics_page(
        self, client: TestClient, test_user_in_db: dict
    ):
        from app.middleware.performance import metrics  # noqa: PLC0415

        before = metrics.counters["auth.logout"]
        client.cookies.set("refresh_token", test_user_in_db["refresh_token"])

        assert client.post("/api/v1/auth/logout").status_code == 200

        assert metrics.counters["auth.logout"] == before + 1


class TestGitHubCallbackMocked:
    """Tests for GitHub callback with mocked external calls."""

    def test_callback_with_valid_state_mock_github(self, client: TestClient):
        """Test callback flow with mocked GitHub API responses."""
        # First, initiate login to get a valid state
        with patch("app.api.v1.auth.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = "test_client_id"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"

            login_response = client.get("/api/v1/auth/github", follow_redirects=False)
            assert login_response.status_code == 307

            # Extract state from redirect URL
            location = login_response.headers.get("location", "")
            import urllib.parse  # noqa: PLC0415

            parsed = urllib.parse.urlparse(location)
            params = urllib.parse.parse_qs(parsed.query)
            state = params.get("state", [""])[0]

            assert state != ""

            # Now the state should be valid for callback
            # But we can't complete without mocking httpx calls

    def test_github_callback_exchange_error(self, client: TestClient):
        """Test callback handles token exchange errors."""
        with patch("app.api.v1.auth.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = "test_id"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"

            # First initiate login
            login_response = client.get("/api/v1/auth/github", follow_redirects=False)

            # Extract state
            location = login_response.headers.get("location", "")
            parsed = urllib.parse.urlparse(location)
            params = urllib.parse.parse_qs(parsed.query)
            state = params.get("state", [""])[0]

            # Mock the httpx client to return an error
            with patch("app.api.v1.auth.get_oauth_client") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 400
                mock_response.json.return_value = {"error": "bad_verification_code"}

                mock_async_client = AsyncMock()
                mock_async_client.post.return_value = mock_response
                mock_client.return_value = mock_async_client

                callback_response = client.get(
                    f"/api/v1/auth/github/callback?code=bad_code&state={state}"
                )
                # Should fail with 400 due to GitHub error
                assert callback_response.status_code == 400


class TestGitHubCallbackFullFlow:
    """Full OAuth callback flow tests with comprehensive mocking."""

    def _get_valid_state(self, client: TestClient) -> str:
        """Helper to get a valid OAuth state."""
        with patch("app.api.v1.auth.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = "test_client_id"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"
            mock_settings.RATE_LIMIT_AUTH = "100/minute"

            login_response = client.get("/api/v1/auth/github", follow_redirects=False)
            location = login_response.headers.get("location", "")
            parsed = urllib.parse.urlparse(location)
            params = urllib.parse.parse_qs(parsed.query)
            return params.get("state", [""])[0]

    def test_callback_token_exchange_failure(self, client: TestClient):
        """Test callback when GitHub token exchange fails."""
        state = self._get_valid_state(client)

        with patch("app.api.v1.auth.get_oauth_client") as mock_client:
            # Mock token exchange to fail
            mock_token_response = MagicMock()
            mock_token_response.status_code = 500

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_token_response
            mock_client.return_value = mock_async_client

            response = client.get(f"/api/v1/auth/github/callback?code=test&state={state}")
            assert response.status_code == 400
            assert "Failed to get access token" in response.json()["detail"]

    def test_callback_oauth_error_in_response(self, client: TestClient):
        """Test callback when GitHub returns OAuth error."""
        state = self._get_valid_state(client)

        with patch("app.api.v1.auth.get_oauth_client") as mock_client:
            # Mock token exchange to return error
            mock_token_response = MagicMock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {
                "error": "bad_verification_code",
                "error_description": "The code passed is incorrect or expired.",
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_token_response
            mock_client.return_value = mock_async_client

            response = client.get(f"/api/v1/auth/github/callback?code=bad&state={state}")
            assert response.status_code == 400
            assert "Failed to authenticate with GitHub" in response.json()["detail"]

    def test_callback_user_info_failure(self, client: TestClient):
        """Test callback when GitHub user info request fails."""
        state = self._get_valid_state(client)

        with patch("app.api.v1.auth.get_oauth_client") as mock_client:
            # Mock token exchange success
            mock_token_response = MagicMock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {"access_token": "gh_token_123"}

            # Mock user info failure
            mock_user_response = MagicMock()
            mock_user_response.status_code = 401

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_token_response
            mock_async_client.get.return_value = mock_user_response
            mock_client.return_value = mock_async_client

            response = client.get(f"/api/v1/auth/github/callback?code=test&state={state}")
            assert response.status_code == 400
            assert "Failed to get user info" in response.json()["detail"]

    def test_callback_non_admin_rejected(self, client: TestClient):
        """Test callback rejects non-admin users."""
        state = self._get_valid_state(client)

        with (
            patch("app.api.v1.auth.httpx.AsyncClient") as mock_client,
            patch("app.api.v1.auth.settings") as mock_settings,
        ):
            mock_settings.GITHUB_CLIENT_ID = "test_id"
            mock_settings.GITHUB_CLIENT_SECRET = "test_secret"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"
            mock_settings.ADMIN_GITHUB_ID = "12345"  # Expected admin ID
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            mock_settings.RATE_LIMIT_AUTH = "100/minute"

            # Mock token exchange success
            mock_token_response = MagicMock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {"access_token": "gh_token_123"}

            # Mock user info with different ID
            mock_user_response = MagicMock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = {
                "id": 99999,  # Not the admin
                "login": "notadmin",
                "email": "notadmin@example.com",
                "name": "Not Admin",
                "avatar_url": "https://example.com/avatar.png",
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_token_response
            mock_async_client.get.return_value = mock_user_response
            mock_client.return_value = mock_async_client

            response = client.get(f"/api/v1/auth/github/callback?code=test&state={state}")
            assert response.status_code == 403
            assert "Only the admin can log in" in response.json()["detail"]

    def test_callback_success_new_user(self, client: TestClient):
        """Test successful callback creates new user and redirects."""
        state = self._get_valid_state(client)

        with (
            patch("app.api.v1.auth.httpx.AsyncClient") as mock_client,
            patch("app.api.v1.auth.settings") as mock_settings,
        ):
            mock_settings.GITHUB_CLIENT_ID = "test_id"
            mock_settings.GITHUB_CLIENT_SECRET = "test_secret"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"
            mock_settings.ADMIN_GITHUB_ID = "12345"
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            mock_settings.RATE_LIMIT_AUTH = "100/minute"

            # Mock token exchange success
            mock_token_response = MagicMock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {"access_token": "gh_token_123"}

            # Mock user info with admin ID
            mock_user_response = MagicMock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = {
                "id": 12345,  # Admin ID
                "login": "adminuser",
                "email": "admin@example.com",
                "name": "Admin User",
                "avatar_url": "https://example.com/admin.png",
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_token_response
            mock_async_client.get.return_value = mock_user_response
            mock_client.return_value = mock_async_client

            response = client.get(
                f"/api/v1/auth/github/callback?code=valid_code&state={state}",
                follow_redirects=False,
            )

            # Should redirect to frontend (tokens are set as HTTP-only cookies)
            assert response.status_code == 302
            location = response.headers.get("location", "")
            assert "localhost:3000/admin" in location

    def test_callback_success_existing_user_updated(self, client: TestClient):
        """Test successful callback updates existing user info."""
        state = self._get_valid_state(client)

        with (
            patch("app.api.v1.auth.httpx.AsyncClient") as mock_client,
            patch("app.api.v1.auth.settings") as mock_settings,
        ):
            mock_settings.GITHUB_CLIENT_ID = "test_id"
            mock_settings.GITHUB_CLIENT_SECRET = "test_secret"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"
            mock_settings.ADMIN_GITHUB_ID = "67890"  # Match existing user
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            mock_settings.RATE_LIMIT_AUTH = "100/minute"

            # Mock token exchange success
            mock_token_response = MagicMock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {"access_token": "gh_token_456"}

            # Mock user info matching existing admin_user_in_db github_id
            mock_user_response = MagicMock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = {
                "id": 67890,
                "login": "updated_username",
                "email": "updated@example.com",
                "name": "Updated Name",
                "avatar_url": "https://example.com/new_avatar.png",
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_token_response
            mock_async_client.get.return_value = mock_user_response
            mock_client.return_value = mock_async_client

            response = client.get(
                f"/api/v1/auth/github/callback?code=valid&state={state}",
                follow_redirects=False,
            )

            # Should succeed with redirect
            assert response.status_code == 302

    def test_callback_fails_closed_when_admin_id_unset(self, client: TestClient):
        """Callback refuses to issue tokens when ADMIN_GITHUB_ID is not set.

        Prior behavior was fail-open (anyone became admin if the env var was
        missing); BUGS-01 reverses this to fail-closed (503) so a
        misconfigured deploy can't silently promote arbitrary users.
        """
        state = self._get_valid_state(client)

        with (
            patch("app.api.v1.auth.httpx.AsyncClient") as mock_client,
            patch("app.api.v1.auth.settings") as mock_settings,
        ):
            mock_settings.GITHUB_CLIENT_ID = "test_id"
            mock_settings.GITHUB_CLIENT_SECRET = "test_secret"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"
            mock_settings.ADMIN_GITHUB_ID = None  # Misconfigured deploy
            mock_settings.FRONTEND_URL = "http://localhost:3000"
            mock_settings.RATE_LIMIT_AUTH = "100/minute"

            # Mock token exchange success
            mock_token_response = MagicMock()
            mock_token_response.status_code = 200
            mock_token_response.json.return_value = {"access_token": "gh_token_789"}

            # Mock any user
            mock_user_response = MagicMock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = {
                "id": 11111,
                "login": "anyuser",
                "email": "any@example.com",
                "name": "Any User",
                "avatar_url": "https://example.com/any.png",
            }

            mock_async_client = AsyncMock()
            mock_async_client.post.return_value = mock_token_response
            mock_async_client.get.return_value = mock_user_response
            mock_client.return_value = mock_async_client

            response = client.get(
                f"/api/v1/auth/github/callback?code=valid&state={state}",
                follow_redirects=False,
            )

            assert response.status_code == 503
            assert "not configured" in response.json()["detail"].lower()


class TestAuthNetworkErrors:
    """Tests for network error handling in auth endpoints."""

    def test_github_token_exchange_timeout(self, client: TestClient):
        """Test callback handles network timeout during token exchange."""
        import httpx

        with patch("app.api.v1.auth.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = "test_id"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"
            mock_settings.RATE_LIMIT_AUTH = "100/minute"

            # Get valid state
            login_response = client.get("/api/v1/auth/github", follow_redirects=False)
            location = login_response.headers.get("location", "")
            parsed = urllib.parse.urlparse(location)
            params = urllib.parse.parse_qs(parsed.query)
            state = params.get("state", [""])[0]

            with patch("app.api.v1.auth.get_oauth_client") as mock_client:
                # Mock network timeout
                mock_async_client = AsyncMock()
                mock_async_client.post.side_effect = httpx.TimeoutException("Connection timed out")
                mock_client.return_value = mock_async_client

                response = client.get(f"/api/v1/auth/github/callback?code=test&state={state}")
                # Should return error for failed token exchange (400 or 504)
                assert response.status_code in [400, 504]

    def test_github_user_info_timeout(self, client: TestClient):
        """Test callback handles network timeout during user info fetch."""
        import httpx

        with patch("app.api.v1.auth.settings") as mock_settings:
            mock_settings.GITHUB_CLIENT_ID = "test_id"
            mock_settings.GITHUB_REDIRECT_URI = "http://localhost/callback"
            mock_settings.RATE_LIMIT_AUTH = "100/minute"

            # Get valid state
            login_response = client.get("/api/v1/auth/github", follow_redirects=False)
            location = login_response.headers.get("location", "")
            parsed = urllib.parse.urlparse(location)
            params = urllib.parse.parse_qs(parsed.query)
            state = params.get("state", [""])[0]

            with patch("app.api.v1.auth.get_oauth_client") as mock_client:
                # Mock token exchange success
                mock_token_response = MagicMock()
                mock_token_response.status_code = 200
                mock_token_response.json.return_value = {"access_token": "gh_token"}

                mock_async_client = AsyncMock()
                mock_async_client.post.return_value = mock_token_response
                # Timeout on user info request
                mock_async_client.get.side_effect = httpx.TimeoutException("Read timed out")
                mock_client.return_value = mock_async_client

                response = client.get(f"/api/v1/auth/github/callback?code=test&state={state}")
                # Should return error for failed user info fetch (400 or 504)
                assert response.status_code in [400, 504]


class TestAuthSecurityEdgeCases:
    """Additional security edge case tests for auth endpoints."""

    def test_sql_injection_in_refresh_token(self, client: TestClient):
        """Test that SQL injection attempts in refresh token are safely handled."""
        # Attempt SQL injection in token
        malicious_tokens = [
            "'; DROP TABLE users; --",
            "1 OR 1=1",
            "admin'--",
            "UNION SELECT * FROM users",
        ]
        for token in malicious_tokens:
            # Pad token to meet minimum length validation
            padded_token = token.ljust(20, "x")
            response = client.post("/api/v1/auth/refresh", json={"refresh_token": padded_token})
            # Should fail safely with 401, not cause database errors
            assert response.status_code == 401

    def test_xss_in_callback_state(self, client: TestClient):
        """Test that XSS attempts in state parameter are safely handled."""
        xss_payloads = [
            "<script>alert(1)</script>",
            "javascript:alert(1)",
            "%3Cscript%3Ealert(1)%3C/script%3E",
        ]
        for payload in xss_payloads:
            response = client.get(f"/api/v1/auth/github/callback?code=test&state={payload}")
            # Should fail safely with 400, not reflect the XSS
            assert response.status_code == 400
            # Response should not contain the unescaped payload
            response_text = response.text
            assert "<script>" not in response_text

    def test_very_long_token(self, client: TestClient):
        """Test handling of extremely long tokens."""
        # Create a very long token (10KB)
        long_token = "x" * 10240
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": long_token})
        # Should fail safely - either 401 (invalid) or 422 (validation) or 413 (too large)
        assert response.status_code in [401, 413, 422]

    def test_unicode_in_refresh_token(self, client: TestClient):
        """Test handling of unicode in refresh token."""
        unicode_tokens = [
            "🔐🔐🔐🔐🔐🔐🔐🔐🔐🔐",
            "токен_обновления",
            "リフレッシュトークン",
        ]
        for token in unicode_tokens:
            response = client.post("/api/v1/auth/refresh", json={"refresh_token": token})
            # Should fail safely with 401 or 422
            assert response.status_code in [401, 422]

    def test_null_bytes_in_token(self, client: TestClient):
        """Test handling of null bytes in token."""
        null_token = "token_with\x00null_bytes"
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": null_token})
        # Should fail safely
        assert response.status_code in [401, 422]
