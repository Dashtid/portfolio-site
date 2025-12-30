"""
GitHub API endpoints for fetching live statistics
"""

import logging
from typing import Annotated, TypedDict

import httpx
from fastapi import APIRouter, HTTPException, Path, Query

from app.config import settings
from app.services.github_service import github_service

logger = logging.getLogger(__name__)
router = APIRouter()


class LanguageStat(TypedDict):
    """Type definition for language statistics."""

    name: str
    bytes: int
    percentage: float


# GitHub username/repo validation patterns
# GitHub usernames: 1-39 chars, alphanumeric and hyphens, cannot start/end with hyphen
GITHUB_USERNAME_PATTERN = r"^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,37}[a-zA-Z0-9])?$"
# GitHub repo names: 1-100 chars, alphanumeric, hyphens, underscores, dots
GITHUB_REPO_PATTERN = r"^[a-zA-Z0-9._-]{1,100}$"

# Type aliases for validated path parameters
GitHubUsername = Annotated[
    str,
    Path(
        min_length=1,
        max_length=39,
        pattern=GITHUB_USERNAME_PATTERN,
        description="GitHub username (1-39 chars, alphanumeric and hyphens)",
    ),
]
GitHubRepoName = Annotated[
    str,
    Path(
        min_length=1,
        max_length=100,
        pattern=GITHUB_REPO_PATTERN,
        description="GitHub repository name (1-100 chars, alphanumeric, hyphens, underscores, dots)",
    ),
]


@router.get("/stats/{username}")
async def get_github_stats(username: GitHubUsername):
    """
    Get GitHub statistics for a user.

    Returns aggregated stats including repos, stars, languages, etc.
    """
    try:
        stats = await github_service.get_portfolio_stats(username)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.exception(f"Error fetching GitHub stats for {username}: {e}")
        # Use generic message in production to avoid leaking implementation details
        detail = str(e) if settings.DEBUG else "Failed to fetch GitHub statistics"
        raise HTTPException(status_code=500, detail=detail) from e
    else:
        return stats


@router.get("/project/{owner}/{repo}")
async def get_project_stats(owner: GitHubUsername, repo: GitHubRepoName):
    """
    Get detailed statistics for a specific GitHub project.

    Returns project details including stars, forks, languages, commit count, etc.
    """
    try:
        stats = await github_service.get_project_stats(owner, repo)
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.exception(f"Error fetching project stats for {owner}/{repo}: {e}")
        # Use generic message in production to avoid leaking implementation details
        detail = str(e) if settings.DEBUG else "Failed to fetch project statistics"
        raise HTTPException(status_code=500, detail=detail) from e
    else:
        return stats


@router.get("/repos/{username}")
async def get_user_repos(
    username: GitHubUsername,
    limit: int | None = Query(10, le=50, description="Maximum number of repos to return"),
):
    """
    Get list of repositories for a user.

    Returns list of repos sorted by last updated.
    """
    try:
        repos = await github_service.get_user_repos(username)
        # Return only requested number of repos
        result = repos[:limit]
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.exception(f"Error fetching repos for {username}: {e}")
        # Use generic message in production to avoid leaking implementation details
        detail = str(e) if settings.DEBUG else "Failed to fetch repositories"
        raise HTTPException(status_code=500, detail=detail) from e
    else:
        return result


@router.get("/languages/{owner}/{repo}")
async def get_repo_languages(owner: GitHubUsername, repo: GitHubRepoName):
    """
    Get language statistics for a specific repository.

    Returns dictionary of languages and their byte counts.
    """
    try:
        languages = await github_service.get_repo_languages(owner, repo)
        total_bytes = sum(languages.values())

        # Convert to percentages
        language_stats: list[LanguageStat] = [
            {
                "name": lang,
                "bytes": bytes_count,
                "percentage": round(bytes_count / total_bytes * 100, 2) if total_bytes > 0 else 0,
            }
            for lang, bytes_count in languages.items()
        ]

        result = {
            "total_bytes": total_bytes,
            "languages": sorted(language_stats, key=lambda x: x["bytes"], reverse=True),
        }
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        logger.exception(f"Error fetching languages for {owner}/{repo}: {e}")
        # Use generic message in production to avoid leaking implementation details
        detail = str(e) if settings.DEBUG else "Failed to fetch repository languages"
        raise HTTPException(status_code=500, detail=detail) from e
    else:
        return result
