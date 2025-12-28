"""
Dependency injection utilities
"""

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.database import get_db
from app.models.user import User

# Bearer token security scheme (optional - can also use cookies)
security = HTTPBearer(auto_error=False)


def get_token_from_request(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = None,
) -> str | None:
    """Extract token from cookie or Authorization header.

    Priority: Cookie > Authorization header (for seamless OAuth flow)
    """
    # Try cookie first (set by OAuth callback)
    token = request.cookies.get("access_token")
    if token:
        return token

    # Fall back to Authorization header
    if credentials:
        return credentials.credentials

    return None


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> User:
    """Get the current authenticated user from JWT token (cookie or header)"""
    token = get_token_from_request(request, credentials)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Decode token
    payload = decode_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user


async def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:  # noqa: B008
    """Require the current user to be an admin"""
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")

    return current_user
