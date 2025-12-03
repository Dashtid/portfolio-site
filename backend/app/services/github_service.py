"""
GitHub API service for fetching live project statistics
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        # Add token if available
        if hasattr(settings, "GITHUB_TOKEN") and settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    async def get_user_info(self, username: str) -> dict[str, Any]:
        """Get GitHub user information."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/users/{username}", headers=self.headers
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
            except httpx.HTTPError as e:
                logger.error(f"Error fetching user info for {username}: {e}")
                return {}

    async def get_user_repos(self, username: str, per_page: int = 100) -> list[dict]:
        """Get all public repositories for a user."""
        repos = []
        page = 1

        async with httpx.AsyncClient() as client:
            while True:
                try:
                    response = await client.get(
                        f"{self.base_url}/users/{username}/repos",
                        headers=self.headers,
                        params={
                            "per_page": per_page,
                            "page": page,
                            "sort": "updated",
                            "direction": "desc",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()

                    if not data:
                        break

                    repos.extend(data)

                    # Check if there are more pages
                    if len(data) < per_page:
                        break

                    page += 1

                except httpx.HTTPError as e:
                    logger.error(f"Error fetching repos for {username}: {e}")
                    break

        return repos

    async def get_repo_details(self, owner: str, repo: str) -> dict[str, Any]:
        """Get detailed information about a specific repository."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}", headers=self.headers
                )
                response.raise_for_status()
                result: dict[str, Any] = response.json()
                return result
            except httpx.HTTPError as e:
                logger.error(f"Error fetching repo {owner}/{repo}: {e}")
                return {}

    async def get_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Get language statistics for a repository."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/languages", headers=self.headers
                )
                response.raise_for_status()
                result: dict[str, int] = response.json()
                return result
            except httpx.HTTPError as e:
                logger.error(f"Error fetching languages for {owner}/{repo}: {e}")
                return {}

    async def get_repo_commits(self, owner: str, repo: str, since: datetime | None = None) -> int:
        """Get commit count for a repository."""
        if not since:
            since = datetime.now() - timedelta(days=365)  # Default to last year

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/repos/{owner}/{repo}/commits",
                    headers=self.headers,
                    params={"since": since.isoformat(), "per_page": 1},
                )
                response.raise_for_status()

                # Get total count from Link header
                link_header = response.headers.get("Link", "")
                if link_header:
                    # Parse the last page number from Link header
                    match = re.search(r'page=(\d+)>; rel="last"', link_header)
                    if match:
                        return int(match.group(1))

                # If no pagination, count the returned items
                return len(response.json())

            except httpx.HTTPError as e:
                logger.error(f"Error fetching commits for {owner}/{repo}: {e}")
                return 0

    async def get_portfolio_stats(self, username: str) -> dict[str, Any]:
        """Get aggregated statistics for portfolio display."""
        user_info = await self.get_user_info(username)
        repos = await self.get_user_repos(username)

        # Filter out forked repositories
        owned_repos = [r for r in repos if not r.get("fork", False)]

        # Calculate statistics
        total_stars = sum(r.get("stargazers_count", 0) for r in owned_repos)
        total_forks = sum(r.get("forks_count", 0) for r in owned_repos)
        total_watchers = sum(r.get("watchers_count", 0) for r in owned_repos)

        # Get language statistics
        languages: dict[str, int] = {}
        for repo in owned_repos[:10]:  # Limit to top 10 repos to avoid rate limiting
            repo_langs = await self.get_repo_languages(username, repo["name"])
            for lang, bytes_count in repo_langs.items():
                languages[lang] = languages.get(lang, 0) + bytes_count

        # Sort languages by usage
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "username": username,
            "avatar_url": user_info.get("avatar_url"),
            "bio": user_info.get("bio"),
            "public_repos": user_info.get("public_repos", 0),
            "followers": user_info.get("followers", 0),
            "following": user_info.get("following", 0),
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_watchers": total_watchers,
            "top_languages": [
                {"name": lang, "percentage": round(bytes_count / sum(languages.values()) * 100, 1)}
                for lang, bytes_count in top_languages
            ],
            "recent_repos": [
                {
                    "name": r["name"],
                    "description": r.get("description"),
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "language": r.get("language"),
                    "updated_at": r.get("updated_at"),
                    "html_url": r.get("html_url"),
                }
                for r in owned_repos[:6]  # Top 6 recent repos
            ],
        }

    async def get_project_stats(self, owner: str, repo: str) -> dict[str, Any]:
        """Get detailed statistics for a specific project."""
        repo_details = await self.get_repo_details(owner, repo)
        languages = await self.get_repo_languages(owner, repo)
        commit_count = await self.get_repo_commits(owner, repo)

        return {
            "name": repo_details.get("name"),
            "full_name": repo_details.get("full_name"),
            "description": repo_details.get("description"),
            "stars": repo_details.get("stargazers_count", 0),
            "forks": repo_details.get("forks_count", 0),
            "watchers": repo_details.get("watchers_count", 0),
            "open_issues": repo_details.get("open_issues_count", 0),
            "created_at": repo_details.get("created_at"),
            "updated_at": repo_details.get("updated_at"),
            "size": repo_details.get("size", 0),
            "commit_count": commit_count,
            "languages": languages,
            "topics": repo_details.get("topics", []),
            "homepage": repo_details.get("homepage"),
            "html_url": repo_details.get("html_url"),
        }


# Singleton instance
github_service = GitHubService()
