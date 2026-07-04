"""
Admin-only panels exposed to the admin dashboard.

BACKEND-ADMIN-10 surfaces the operator's Sentry issues URL so the admin
dashboard can deep-link from the metrics panel straight into Sentry. The
DSN itself is never returned — the frontend just needs to know whether
to render the deep-link panel and which URL to point at.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.config import settings
from app.core.deps import get_current_admin_user
from app.models.user import User

router = APIRouter()

AdminUser = Annotated[User, Depends(get_current_admin_user)]


class SentryPanel(BaseModel):
    """Frontend-facing payload for the admin dashboard's Sentry tile.

    ``enabled`` mirrors the backend's ``ERROR_TRACKING_ENABLED`` AND
    whether the SDK was initialised with a DSN. ``issues_url`` is the
    deep-link the admin clicks to land on the issues view; when unset
    the dashboard hides the tile rather than rendering a broken link.
    """

    enabled: bool
    issues_url: str | None = None


@router.get("/sentry-panel", response_model=SentryPanel)
async def get_sentry_panel(current_user: AdminUser) -> SentryPanel:
    """Return the Sentry deep-link configuration for the admin dashboard.

    Admin-only: the DSN URL pattern reveals the org slug, which is mild
    information disclosure if leaked to anonymous visitors.
    """
    _ = current_user  # only the admin gate matters; no per-user data here.
    return SentryPanel(
        enabled=bool(settings.ERROR_TRACKING_ENABLED and settings.SENTRY_DSN),
        issues_url=settings.SENTRY_ISSUES_URL,
    )
