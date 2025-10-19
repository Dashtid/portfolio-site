"""
GitHub API endpoints for fetching live statistics
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.services.github_service import github_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/stats/{username}")
async def get_github_stats(username: str):
    """
    Get GitHub statistics for a user.

    Returns aggregated stats including repos, stars, languages, etc.
    """
    try:
        stats = await github_service.get_portfolio_stats(username)
        return stats
    except Exception as e:
        logger.error(f"Error fetching GitHub stats for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project/{owner}/{repo}")
async def get_project_stats(owner: str, repo: str):
    """
    Get detailed statistics for a specific GitHub project.

    Returns project details including stars, forks, languages, commit count, etc.
    """
    try:
        stats = await github_service.get_project_stats(owner, repo)
        return stats
    except Exception as e:
        logger.error(f"Error fetching project stats for {owner}/{repo}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repos/{username}")
async def get_user_repos(
    username: str,
    limit: Optional[int] = Query(10, le=50, description="Maximum number of repos to return")
):
    """
    Get list of repositories for a user.

    Returns list of repos sorted by last updated.
    """
    try:
        repos = await github_service.get_user_repos(username)
        # Return only requested number of repos
        return repos[:limit]
    except Exception as e:
        logger.error(f"Error fetching repos for {username}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/languages/{owner}/{repo}")
async def get_repo_languages(owner: str, repo: str):
    """
    Get language statistics for a specific repository.

    Returns dictionary of languages and their byte counts.
    """
    try:
        languages = await github_service.get_repo_languages(owner, repo)
        total_bytes = sum(languages.values())

        # Convert to percentages
        language_stats = [
            {
                "name": lang,
                "bytes": bytes_count,
                "percentage": round(bytes_count / total_bytes * 100, 2) if total_bytes > 0 else 0
            }
            for lang, bytes_count in languages.items()
        ]

        return {
            "total_bytes": total_bytes,
            "languages": sorted(language_stats, key=lambda x: x["bytes"], reverse=True)
        }
    except Exception as e:
        logger.error(f"Error fetching languages for {owner}/{repo}: {e}")
        raise HTTPException(status_code=500, detail=str(e))