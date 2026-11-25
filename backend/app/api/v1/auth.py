"""
Authentication API endpoints with GitHub OAuth

Uses database-backed OAuth state storage for multi-instance deployments.
"""

import base64
import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.core.security_events import security_event
from app.database import get_db
from app.middleware import limiter
from app.models.oauth_state import OAuthState
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import RefreshSuccess, RefreshTokenRequest, UserResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

# OAuth state TTL
OAUTH_STATE_TTL_SECONDS = 300  # 5 minutes

# The cookie that ties a login to the browser that started it: the state
# and the PKCE verifier, "<state>.<verifier>", sent only to the callback.
OAUTH_COOKIE = "github_oauth"
OAUTH_COOKIE_PATH = "/api/v1/auth/github"

# Window in which reuse of an already-rotated refresh jti is treated as a
# benign concurrent refresh (multi-tab race) rather than token theft. Long
# enough to cover a slow sibling request, short enough that a genuinely
# stolen-and-replayed token still trips the revoke-all sweep.
REFRESH_ROTATION_GRACE_SECONDS = 30

# The 401 detail when a reused refresh token made /auth/refresh revoke the
# user's live sessions. The frontend (src/api/client.ts) matches it and the
# admin login page says that all sessions were revoked.
SESSIONS_REVOKED_DETAIL = "Refresh token reused; all sessions revoked"

# Absolute session lifetime. Every rotation issues a refresh token with a
# fresh REFRESH_TOKEN_EXPIRE_DAYS, so without this cap an active session
# (or a stolen one kept warm) renewed forever without a GitHub sign-in.
SESSION_MAX_AGE = timedelta(days=30)

# PERF-10: shared httpx.AsyncClient for the OAuth code-exchange + user-info
# round-trips to github.com. Each `async with httpx.AsyncClient()` in the
# request path re-runs TCP + TLS handshakes (~150-250 ms total over the
# transatlantic link). A single module-level client reuses the connection
# pool, so the second request inside a callback (user-info after token
# exchange) reuses the same TLS session and the OAuth round-trip ends up
# ~200 ms faster on the median. We close it on app shutdown via the
# lifespan hook in main.py.
OAUTH_TIMEOUT = httpx.Timeout(timeout=10.0, pool=5.0)
_oauth_client: httpx.AsyncClient | None = None


def get_oauth_client() -> httpx.AsyncClient:
    """Return the shared OAuth httpx client, lazily creating it on first call.

    Module-level singleton via `global` is the standard pattern for a
    process-lifetime resource; ruff's PLW0603 complaint is correct for
    business logic but not for lazy-init of an I/O client.
    """
    global _oauth_client  # noqa: PLW0603
    if _oauth_client is None or _oauth_client.is_closed:
        _oauth_client = httpx.AsyncClient(
            timeout=OAUTH_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
        )
    return _oauth_client


async def close_oauth_client() -> None:
    """Close the shared OAuth client. Called from app lifespan shutdown."""
    global _oauth_client  # noqa: PLW0603
    if _oauth_client is not None and not _oauth_client.is_closed:
        await _oauth_client.aclose()
        _oauth_client = None


def _auth_cookie_kwargs() -> dict:
    """Common attributes for the auth cookies.

    Post-INFRA-003: frontend (dashti.se) and backend (api.dashti.se) share
    eTLD+1, so SameSite=Lax is sufficient — the browser treats fetches
    between the two as same-site and sends the cookies. Secure stays
    env-conditional because dev/test runs over plain HTTP, where Secure=True
    would cause the browser to drop the cookie outright.

    Note: cookies created with these attributes must be *deleted* with the
    same attributes (Secure, SameSite, HttpOnly) or recent Chromium and
    Firefox reject the deletion. Reuse this helper on both set_cookie and
    delete_cookie call sites to keep them in lock-step.
    """
    is_production = settings.ENVIRONMENT == "production"
    return {
        "httponly": True,
        "secure": is_production,
        "samesite": "lax",
    }


async def create_oauth_state(db: AsyncSession) -> str:
    """Create and store a new single-use OAuth state for CSRF protection"""
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=OAUTH_STATE_TTL_SECONDS)

    oauth_state = OAuthState(state=state, expires_at=expires_at)
    db.add(oauth_state)
    await db.commit()

    return state


async def validate_and_consume_state(db: AsyncSession, state: str) -> bool:
    """Validate OAuth state and remove it (single-use).

    The check + delete is performed as a single atomic DELETE...RETURNING so
    two concurrent callbacks with the same state can never both succeed: at
    most one DELETE's WHERE clause matches a non-expired row, and that
    caller consumes it. The other gets no row back.

    The callback calls this only once the state matches the browser's
    OAUTH_COOKIE, so a request from another browser never consumes the
    real login's row.
    """
    now = datetime.now(UTC)
    stmt = (
        delete(OAuthState)
        .where(OAuthState.state == state, OAuthState.expires_at > now)
        .returning(OAuthState.state)
    )
    consumed = (await db.execute(stmt)).first()
    await db.commit()
    return consumed is not None


def _pkce_challenge(verifier: str) -> str:
    """The S256 code_challenge for a PKCE code_verifier (RFC 7636 section 4.2)."""
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


@router.get("/github")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def github_login(request: Request, db: DbSession):
    """Initiate GitHub OAuth flow"""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub OAuth not configured"
        )

    # Note: Expired states are cleaned up by background task in main.py (every 5 minutes)
    # Removing duplicate cleanup here to prevent race conditions

    # Generate state for CSRF protection with TTL (database-backed)
    state = await create_oauth_state(db)
    # PKCE: GitHub redeems the code only together with this verifier, which
    # stays in the browser's HttpOnly cookie until the callback sends it.
    verifier = secrets.token_urlsafe(64)

    # Build GitHub authorization URL. No scope: the callback reads only the
    # public profile from GET /user, which a token without scopes can do.
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"state={state}&"
        f"code_challenge={_pkce_challenge(verifier)}&"
        f"code_challenge_method=S256"
    )

    response = RedirectResponse(url=github_auth_url)
    # SameSite=Lax, never Strict: GitHub's redirect back to the callback is a
    # cross-site top-level navigation, which carries Lax cookies only.
    response.set_cookie(
        key=OAUTH_COOKIE,
        value=f"{state}.{verifier}",
        max_age=OAUTH_STATE_TTL_SECONDS,
        path=OAUTH_COOKIE_PATH,
        **_auth_cookie_kwargs(),
    )
    return response


def _cookie_verifier(request: Request, state: str) -> str | None:
    """The PKCE verifier from OAUTH_COOKIE when the cookie carries `state`, else None."""
    cookie_state, _, verifier = request.cookies.get(OAUTH_COOKIE, "").partition(".")
    if verifier and secrets.compare_digest(cookie_state.encode(), state.encode()):
        return verifier
    return None


def _oauth_denied_redirect(error: str | None) -> RedirectResponse:
    """Back to the login page when the OAuth dance ends without a code.

    Targets /admin/login directly: /admin is auth-gated, so the router
    guard would bounce an unauthenticated (cancelled) user to the login
    page anyway — and DROP the query string in the named-route redirect.
    AdminLogin reads ?oauth=denied and shows a "sign-in was cancelled"
    notice.
    """
    logger.info("OAuth callback without code (error=%s); redirecting to login", error)
    return RedirectResponse(
        url=f"{settings.FRONTEND_URL}/admin/login?oauth=denied",
        status_code=status.HTTP_302_FOUND,
    )


async def _fetch_github_user(code: str, code_verifier: str) -> Any:
    """Exchange the authorization code for a token and return GET /user's JSON.

    Reading GET /user is the token's only use, so the token is revoked right
    after, whatever the outcome: an OAuth app's token is valid until revoked.
    """
    # The shared module-level client reuses its TLS session for these calls.
    client = get_oauth_client()
    github_access_token: str | None = None
    try:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
                "code_verifier": code_verifier,
            },
            headers={"Accept": "application/json"},
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get access token from GitHub",
            )

        token_data = token_response.json()

        if "error" in token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to authenticate with GitHub",
            )

        github_access_token = token_data.get("access_token")

        user_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {github_access_token}",
                "Accept": "application/json",
            },
        )

        if user_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info from GitHub",
            )

        github_user = user_response.json()
    except httpx.TimeoutException as err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="GitHub service is not responding. Please try again later.",
        ) from err
    except httpx.RequestError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to communicate with authentication service. Please try again.",
        ) from err
    finally:
        if github_access_token:
            await _revoke_github_token(client, github_access_token)
    return github_user


async def _revoke_github_token(client: httpx.AsyncClient, access_token: str) -> None:
    """Revoke a GitHub token with DELETE /applications/{client_id}/token.

    GitHub authenticates the call with the app's client id and secret. A
    failure is logged and the login goes on: the token is never stored.
    """
    try:
        response = await client.request(
            "DELETE",
            f"https://api.github.com/applications/{settings.GITHUB_CLIENT_ID}/token",
            auth=(settings.GITHUB_CLIENT_ID or "", settings.GITHUB_CLIENT_SECRET or ""),
            json={"access_token": access_token},
            headers={"Accept": "application/vnd.github+json"},
        )
    except httpx.HTTPError as err:
        logger.warning("GitHub token revocation failed: %s", type(err).__name__)
        return
    if response.status_code != 204:
        logger.warning("GitHub token revocation answered HTTP %s", response.status_code)


@router.get("/github/callback")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def github_callback(
    request: Request,
    db: DbSession,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    """Handle GitHub OAuth callback"""
    # Cancelling GitHub's authorization screen calls back with error=
    # (e.g. access_denied) and NO code — when code/state were required
    # params that surfaced as a raw 422 JSON blob. Send the human back to
    # the admin entry instead; the unused state row expires on its own.
    if error or not code or not state:
        return _oauth_denied_redirect(error)

    # The state must match this browser's OAUTH_COOKIE before its row is
    # consumed (single-use, database-backed): a callback from any other
    # browser fails without using up the real login's state.
    verifier = _cookie_verifier(request, state)
    if verifier is None or not await validate_and_consume_state(db, state):
        reason = "unknown_or_expired" if verifier else "not_this_browser"
        security_event(logging.WARNING, "auth.oauth_state_rejected", request, reason=reason)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state parameter"
        )

    try:
        github_user = await _fetch_github_user(code, verifier)
    except HTTPException as exc:
        security_event(
            logging.WARNING,
            "auth.login_failed",
            request,
            status_code=exc.status_code,
            reason=exc.detail,
        )
        raise

    # Check if user is the admin. Fail closed when ADMIN_GITHUB_ID is unset:
    # if we don't know who admin is, we cannot safely grant admin to anyone,
    # so refuse all logins rather than promoting whoever just OAuth'd in.
    github_id = str(github_user.get("id"))

    if not settings.ADMIN_GITHUB_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin authentication is not configured",
        )
    if github_id != settings.ADMIN_GITHUB_ID:
        security_event(
            logging.WARNING,
            "auth.login_refused",
            request,
            github_id=github_id,
            github_login=github_user.get("login"),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the admin can log in"
        )

    # Check if user exists in database
    result = await db.execute(select(User).where(User.github_id == github_id))
    user = result.scalar_one_or_none()

    # Derive is_admin from the gate above rather than hardcoding True — keeps
    # the only path that sets is_admin honest about its source of truth.
    is_admin = github_id == settings.ADMIN_GITHUB_ID

    # Create or update user
    if not user:
        user = User(
            github_id=github_id,
            username=github_user.get("login"),
            email=github_user.get("email"),
            name=github_user.get("name"),
            avatar_url=github_user.get("avatar_url"),
            is_admin=is_admin,
        )
        db.add(user)
    else:
        # Update user info
        user.username = github_user.get("login")
        user.email = github_user.get("email")
        user.name = github_user.get("name")
        user.avatar_url = github_user.get("avatar_url")

    await db.commit()
    await db.refresh(user)

    # Create JWT tokens. The refresh token's jti is persisted server-side
    # so subsequent /refresh calls can rotate atomically with revocation.
    access_token = create_access_token(subject=user.id)
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(subject=user.id)
    db.add(RefreshToken(jti=refresh_jti, user_id=user.id, expires_at=refresh_exp))
    await db.commit()
    security_event(
        logging.INFO,
        "auth.login_success",
        request,
        user_id=user.id,
        github_id=github_id,
        github_login=user.username,
    )

    # Create redirect response with HTTP-only cookies (secure token storage)
    redirect_url = f"{settings.FRONTEND_URL}/admin"
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    cookie_attrs = _auth_cookie_kwargs()

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **cookie_attrs,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",  # Only sent to auth endpoints
        **cookie_attrs,
    )
    response.delete_cookie(key=OAUTH_COOKIE, path=OAUTH_COOKIE_PATH, **cookie_attrs)

    return response


@router.post("/refresh", response_model=RefreshSuccess)
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: DbSession,
    token_request: RefreshTokenRequest | None = None,
):
    """Refresh access token using refresh token with token rotation.

    Accepts refresh token from either:
    - HTTP-only cookie (preferred, set by OAuth callback)
    - Request body (for non-browser API clients / tests)

    New tokens are always returned as HTTP-only cookies. The response body
    is intentionally token-free so an XSS payload that calls this endpoint
    cannot extract the rotated credentials.
    """
    # Try cookie first, then request body
    refresh_token_value = request.cookies.get("refresh_token")
    if not refresh_token_value and token_request:
        refresh_token_value = token_request.refresh_token

    if not refresh_token_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token required"
        )

    # Decode refresh token
    payload = decode_token(refresh_token_value)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    user_id = payload.get("sub")
    presented_jti = payload.get("jti")

    if not presented_jti:
        # Token was minted before the jti rollout, or signed by something
        # that doesn't include the claim. Refuse — we can't safely rotate.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing jti"
        )

    # Look up the server-side record for this jti FIRST. An unknown jti is
    # the strongest signal of a forged or stale token — refuse before
    # spending a DB round-trip on the user lookup.
    stored = (
        await db.execute(select(RefreshToken).where(RefreshToken.jti == presented_jti))
    ).scalar_one_or_none()

    if stored is None:
        # Unknown jti — either we never issued it or it was already deleted.
        # In production this shouldn't happen; the safe move is reject.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token not recognised"
        )

    if stored.user_id != user_id:
        # Cross-user replay attempt: jti is real but bound to a different
        # user. Revoke everything they hold as a defensive sweep and reject.
        revoked_count = await _revoke_all_for_user(db, user_id)
        security_event(
            logging.ERROR,
            "auth.refresh_cross_user",
            request,
            presented_sub=user_id,
            jti_owner=stored.user_id,
            jti_prefix=presented_jti[:8],
            revoked_count=revoked_count,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token mismatch"
        )

    now = datetime.now(UTC)

    if stored.is_revoked():
        revoked_at = stored.revoked_at
        if revoked_at is not None and revoked_at.tzinfo is None:
            # SQLite returns naive datetimes; reattach UTC (same treatment
            # as RefreshToken.is_expired).
            revoked_at = revoked_at.replace(tzinfo=UTC)
        since_rotation = (now - revoked_at).total_seconds() if revoked_at else None
        if since_rotation is not None and since_rotation <= REFRESH_ROTATION_GRACE_SECONDS:
            # Benign concurrent rotation, not theft: a sibling request
            # (second tab, double-fired 401 interceptor) rotated this jti
            # moments ago and the fresh cookie is already in the shared
            # browser jar — the client only needs to retry. Nuking every
            # session here is what logged the admin out of all tabs.
            security_event(logging.INFO, "auth.refresh_superseded", request, user_id=user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh superseded by a concurrent request",
            )
        # Reuse detection (RFC 6819 §5.2.2.3): a token rotated longer ago
        # than any legitimate race could explain is a stolen-token replay.
        # Revoke ALL of this user's outstanding refresh tokens, forcing a
        # fresh OAuth login.
        revoked_count = await _revoke_all_for_user(db, user_id)
        # With no live session left (a logout on another device revoked
        # them all), the replay ended nothing: a warning, not an error.
        security_event(
            logging.ERROR if revoked_count else logging.WARNING,
            "auth.refresh_reuse_detected",
            request,
            user_id=user_id,
            jti_prefix=presented_jti[:8],
            seconds_since_rotation=since_rotation,
            revoked_count=revoked_count,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=SESSIONS_REVOKED_DETAIL if revoked_count else "Refresh token revoked",
        )

    if stored.is_expired(now):
        # Stale-but-never-rotated token: a browser returning after the
        # expiry window. Not a replay signal — reject without the sweep.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired"
        )

    auth_time = _session_auth_time(request, payload, stored, now)

    # Get user from database. We deliberately check after the jti check so
    # we can't be probed for user existence by replaying old jti values.
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Happy path: claim the rotation ATOMICALLY. Only one concurrent
    # request can flip revoked_at from NULL; the read-then-write this
    # replaces let two requests both pass the checks above and race the
    # rotation. The loser is treated like the in-grace case, not a thief.
    claim = await db.execute(
        update(RefreshToken)
        .where(RefreshToken.jti == presented_jti, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=now)
    )
    if claim.rowcount == 0:  # type: ignore[attr-defined]
        security_event(logging.INFO, "auth.refresh_superseded", request, user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh superseded by a concurrent request",
        )

    access_token = create_access_token(subject=user.id)
    new_refresh_token, new_jti, new_exp = create_refresh_token(subject=user.id, auth_time=auth_time)
    db.add(RefreshToken(jti=new_jti, user_id=user.id, expires_at=new_exp))
    await db.commit()

    cookie_attrs = _auth_cookie_kwargs()

    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
        **cookie_attrs,
    )
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",
        **cookie_attrs,
    )

    return RefreshSuccess()


def _session_auth_time(
    request: Request, payload: dict[str, Any], stored: RefreshToken, now: datetime
) -> int:
    """Return when the presented token's session signed in (Unix seconds).

    Raises 401 once the session is older than SESSION_MAX_AGE. A token
    minted before the auth_time claim existed counts from its own row's
    issued_at: the session is at least that old.
    """
    auth_time = payload.get("auth_time")
    if not isinstance(auth_time, int):
        issued_at = stored.issued_at
        if issued_at.tzinfo is None:
            # SQLite returns naive datetimes; reattach UTC.
            issued_at = issued_at.replace(tzinfo=UTC)
        auth_time = int(issued_at.timestamp())
    if now - datetime.fromtimestamp(auth_time, UTC) > SESSION_MAX_AGE:
        security_event(logging.INFO, "auth.session_expired", request, user_id=stored.user_id)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return auth_time


async def _revoke_all_for_user(db: AsyncSession, user_id: str | None) -> int:
    """Mark every non-revoked refresh-token row for this user as revoked.

    Called from the reuse-detection path and from logout. Rows are marked,
    not deleted, so replay of a revoked-but-unexpired token is still
    detectable; the periodic cleanup task (main.py) purges them once they
    pass expires_at, so any audit surface built on these rows sees at most
    REFRESH_TOKEN_EXPIRE_DAYS of history.

    Returns how many rows it revoked.
    """
    if not user_id:
        return 0
    now = datetime.now(UTC)
    rows = (
        (
            await db.execute(
                select(RefreshToken).where(
                    RefreshToken.user_id == user_id,
                    RefreshToken.revoked_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    for row in rows:
        row.revoked_at = now
    await db.commit()
    return len(rows)


@router.get("/me", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_API)
async def get_current_user_info(request: Request, current_user: CurrentUser):
    """Get current user information"""
    return current_user


@router.post("/logout")
@limiter.limit(settings.RATE_LIMIT_API)
async def logout(request: Request, response: Response, db: DbSession):
    """Logout user by clearing authentication cookies and revoking every
    live refresh-token record for the user.

    Clearing only the cookie would leave the JWT valid until expiry; a
    server-side revoke ensures a copy made before logout can't be replayed
    back into /refresh. The revoke is per-USER, not per-jti: tabs share the
    cookie jar, so the token presented here may already be superseded by a
    rotation from another tab — revoking only the presented jti would leave
    the freshly-rotated sibling valid and the user still logged in.
    """
    # Tolerate decode failure — logout should not be blockable by a
    # malformed/missing cookie.
    user_id = None
    refresh_token_value = request.cookies.get("refresh_token")
    if refresh_token_value:
        payload = decode_token(refresh_token_value)
        if payload and payload.get("type") == "refresh":
            user_id = payload.get("sub")
    revoked_count = await _revoke_all_for_user(db, user_id)
    security_event(
        logging.INFO, "auth.logout", request, user_id=user_id, revoked_count=revoked_count
    )

    cookie_attrs = _auth_cookie_kwargs()

    # The browser only accepts a deletion if the Set-Cookie attributes match
    # the original (Secure, SameSite, HttpOnly) — otherwise the cookie
    # survives. Belt-and-braces: explicit max_age=0 alongside delete_cookie
    # so older browsers that don't honour delete_cookie semantics still
    # expire the cookie.
    for key, path in (("access_token", "/"), ("refresh_token", "/api/v1/auth")):
        response.delete_cookie(key=key, path=path, **cookie_attrs)
        response.set_cookie(key=key, value="", max_age=0, path=path, **cookie_attrs)

    return {"message": "Successfully logged out"}
