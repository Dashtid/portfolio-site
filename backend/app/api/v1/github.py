"""
GitHub API endpoints for fetching live statistics
"""

import logging
from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Path, Request

from app.config import settings
from app.middleware.rate_limit import rate_limit_public
from app.schemas.github import GitHubStats
from app.services.github_service import github_service
from app.services.oss_queries import GITHUB_USERNAME

logger = logging.getLogger(__name__)
router = APIRouter()


# GitHub usernames: 1-39 chars, alphanumeric and hyphens, cannot start/end with hyphen
GITHUB_USERNAME_PATTERN = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$"

GitHubUsername = Annotated[
    str,
    Path(
        min_length=1,
        max_length=39,
        pattern=GITHUB_USERNAME_PATTERN,
        description="GitHub username (1-39 chars, alphanumeric and hyphens)",
    ),
]


@router.get("/stats/{username}", response_model=GitHubStats)
@rate_limit_public
async def get_github_stats(request: Request, username: GitHubUsername):
    """
    Get GitHub statistics for the site owner's account.

    Returns aggregated stats including repos, stars, languages, etc.
    Only GITHUB_USERNAME, the name the frontend requests, is served: any
    other name is a 404 that never reaches GitHub, so callers cannot spend
    the server token's rate limit on accounts of their choosing.
    """
    if username != GITHUB_USERNAME:
        raise HTTPException(status_code=404, detail="Not found")
    try:
        stats = await github_service.get_portfolio_stats(GITHUB_USERNAME)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.exception("Error fetching GitHub stats for %s", username)
        detail = str(e) if settings.DEBUG else "Failed to fetch GitHub statistics"
        raise HTTPException(status_code=500, detail=detail) from e
    else:
        return stats
