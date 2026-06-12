"""
Authentication API endpoints with GitHub OAuth

Uses database-backed OAuth state storage for multi-instance deployments.
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.deps import get_current_user
from app.core.ip_utils import get_client_ip
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.database import get_db
from app.middleware import limiter
from app.models.oauth_state import OAuthState
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.auth import RefreshSuccess, RefreshTokenRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])

# Type aliases for dependency injection (FastAPI 2025 best practice)
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]

# OAuth state TTL
OAUTH_STATE_TTL_SECONDS = 300  # 5 minutes

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


async def create_oauth_state(db: AsyncSession, client_ip: str | None = None) -> str:
    """Create and store a new OAuth state bound to client IP for CSRF protection"""
    state = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + timedelta(seconds=OAUTH_STATE_TTL_SECONDS)

    oauth_state = OAuthState(state=state, expires_at=expires_at, client_ip=client_ip)
    db.add(oauth_state)
    await db.commit()

    return state


async def validate_and_consume_state(
    db: AsyncSession, state: str, client_ip: str | None = None
) -> bool:
    """Validate OAuth state, verify IP binding, and remove it (single-use).

    The check + delete is performed as a single atomic DELETE...RETURNING so
    two concurrent callbacks with the same state can never both succeed: at
    most one DELETE's WHERE clause matches a non-expired, IP-bound row, and
    that caller consumes it. The other gets no row back.

    An attacker arriving with a wrong-IP replay attempt does NOT consume the
    legitimate row — the WHERE clause filters by client_ip, so the row stays
    available for the real user. (If we deleted first and checked second,
    the attacker would DoS the legitimate flow.)
    """
    now = datetime.now(UTC)
    ip_match = or_(
        OAuthState.client_ip.is_(None),
        and_(OAuthState.client_ip.isnot(None), OAuthState.client_ip == client_ip),
    )
    stmt = (
        delete(OAuthState)
        .where(
            OAuthState.state == state,
            OAuthState.expires_at > now,
            ip_match,
        )
        .returning(OAuthState.state)
    )
    consumed = (await db.execute(stmt)).first()
    await db.commit()
    return consumed is not None


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

    # Get client IP for state binding (CSRF protection)
    client_ip = get_client_ip(request)

    # Generate state for CSRF protection with TTL and IP binding (database-backed)
    state = await create_oauth_state(db, client_ip=client_ip)

    # Build GitHub authorization URL
    github_auth_url = (
        f"https://github.com/login/oauth/authorize?"
        f"client_id={settings.GITHUB_CLIENT_ID}&"
        f"redirect_uri={settings.GITHUB_REDIRECT_URI}&"
        f"scope=read:user user:email&"
        f"state={state}"
    )

    return RedirectResponse(url=github_auth_url)


@router.get("/github/callback")
@limiter.limit(settings.RATE_LIMIT_AUTH)
async def github_callback(request: Request, code: str, state: str, db: DbSession):
    """Handle GitHub OAuth callback"""
    # Get client IP for state verification
    client_ip = get_client_ip(request)

    # Verify and consume state (single-use, database-backed, IP-bound)
    if not await validate_and_consume_state(db, state, client_ip=client_ip):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired state parameter"
        )

    # Exchange code for access token with proper timeout and error handling.
    # PERF-10: shared module-level client; TLS session reused across the two
    # round-trips in this handler.
    client = get_oauth_client()
    try:
        # Get access token from GitHub
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": settings.GITHUB_REDIRECT_URI,
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

        # Get user info from GitHub
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
        await _revoke_all_for_user(db, user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token mismatch"
        )

    if stored.is_revoked() or stored.is_expired():
        # Reuse detection (RFC 6819 §5.2.2.3): if a previously revoked or
        # expired refresh token shows up, treat it as a stolen-token replay
        # and revoke ALL of this user's outstanding refresh tokens. Forces
        # a fresh OAuth login.
        await _revoke_all_for_user(db, user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked"
        )

    # Get user from database. We deliberately check after the jti check so
    # we can't be probed for user existence by replaying old jti values.
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Happy path: mark the presented jti revoked and mint a new one.
    stored.revoked_at = datetime.now(UTC)

    access_token = create_access_token(subject=user.id)
    new_refresh_token, new_jti, new_exp = create_refresh_token(subject=user.id)
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


async def _revoke_all_for_user(db: AsyncSession, user_id: str | None) -> None:
    """Mark every non-revoked refresh-token row for this user as revoked.

    Called from the reuse-detection path. We don't delete rows — keeping
    them with revoked_at populated lets a future audit trail / sessions
    admin surface what happened.
    """
    if not user_id:
        return
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


@router.get("/me", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_API)
async def get_current_user_info(request: Request, current_user: CurrentUser):
    """Get current user information"""
    return current_user


@router.post("/logout")
@limiter.limit(settings.RATE_LIMIT_API)
async def logout(request: Request, response: Response, db: DbSession):
    """Logout user by clearing authentication cookies and revoking the
    server-side refresh-token record for the presented jti.

    Clearing only the cookie would leave the JWT valid until expiry; a
    server-side revoke ensures a copy made before logout can't be replayed
    back into /refresh.
    """
    # Server-side revoke: decode the presented refresh token (if any) and
    # mark its jti revoked. Tolerate decode failure — logout should not be
    # blockable by a malformed/missing cookie.
    refresh_token_value = request.cookies.get("refresh_token")
    if refresh_token_value:
        payload = decode_token(refresh_token_value)
        if payload and payload.get("type") == "refresh":
            presented_jti = payload.get("jti")
            if presented_jti:
                stored = (
                    await db.execute(select(RefreshToken).where(RefreshToken.jti == presented_jti))
                ).scalar_one_or_none()
                if stored and not stored.is_revoked():
                    stored.revoked_at = datetime.now(UTC)
                    await db.commit()

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
