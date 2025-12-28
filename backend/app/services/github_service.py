"""
GitHub API service for fetching live project statistics
"""

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout configuration for external API calls
DEFAULT_TIMEOUT = httpx.Timeout(timeout=10.0, pool=5.0)

# Rate limit configuration
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0


class GitHubService:
    """Service for interacting with GitHub API."""

    def __init__(self):
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        self.timeout = DEFAULT_TIMEOUT
        # Add token if available
        if hasattr(settings, "GITHUB_TOKEN") and settings.GITHUB_TOKEN:
            self.headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        # Shared client for connection pooling (lazily initialized)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create shared AsyncClient for connection pooling."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
        return self._client

    async def close(self) -> None:
        """Close the shared client connection pool."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request_with_backoff(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> httpx.Response | None:
        """Make HTTP request with exponential backoff on rate limit (429)."""
        client = await self._get_client()

        for attempt in range(MAX_RETRIES):
            try:
                response = await client.request(method, url, **kwargs)

                # Handle rate limiting
                if response.status_code == 429:
                    # Parse Retry-After header (seconds or HTTP-date)
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        try:
                            wait_seconds = float(retry_after)
                        except ValueError:
                            # Fallback to exponential backoff
                            wait_seconds = BASE_BACKOFF_SECONDS * (2**attempt)
                    else:
                        wait_seconds = BASE_BACKOFF_SECONDS * (2**attempt)

                    if attempt < MAX_RETRIES - 1:
                        logger.warning(
                            "GitHub rate limited, retrying in %.1fs (attempt %d/%d)",
                            wait_seconds,
                            attempt + 1,
                            MAX_RETRIES,
                        )
                        await asyncio.sleep(wait_seconds)
                        continue

                    logger.error("GitHub rate limit exceeded after %d retries", MAX_RETRIES)
                    return None

                return response

            except httpx.TimeoutException:
                if attempt < MAX_RETRIES - 1:
                    wait_seconds = BASE_BACKOFF_SECONDS * (2**attempt)
                    logger.warning(
                        "GitHub request timeout, retrying in %.1fs (attempt %d/%d)",
                        wait_seconds,
                        attempt + 1,
                        MAX_RETRIES,
                    )
                    await asyncio.sleep(wait_seconds)
                    continue
                logger.error("GitHub request timeout after %d retries", MAX_RETRIES)
                return None

            except httpx.RequestError as e:
                logger.exception("GitHub request error: %s", e)
                return None

        return None

    async def get_user_info(self, username: str) -> dict[str, Any]:
        """Get GitHub user information."""
        response = await self._request_with_backoff("GET", f"{self.base_url}/users/{username}")
        if response is None:
            return {}
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.exception("Error fetching user info for %s: %s", username, e)
            return {}

    async def get_user_repos(
        self, username: str, per_page: int = 100, max_repos: int = 100
    ) -> list[dict]:
        """Get public repositories for a user with a limit to prevent DoS."""
        repos: list[dict] = []
        page = 1

        while True:
            response = await self._request_with_backoff(
                "GET",
                f"{self.base_url}/users/{username}/repos",
                params={
                    "per_page": min(per_page, max_repos - len(repos)),
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                },
            )

            if response is None:
                break

            try:
                response.raise_for_status()
                data = response.json()

                if not data:
                    break

                repos.extend(data)

                # Check if we've reached the max_repos limit
                if len(repos) >= max_repos:
                    break

                # Check if there are more pages
                if len(data) < per_page:
                    break

                page += 1

            except httpx.HTTPStatusError as e:
                logger.exception("Error fetching repos for %s: %s", username, e)
                break

        return repos[:max_repos]  # Ensure we don't exceed the limit

    async def get_repo_details(self, owner: str, repo: str) -> dict[str, Any]:
        """Get detailed information about a specific repository."""
        response = await self._request_with_backoff("GET", f"{self.base_url}/repos/{owner}/{repo}")
        if response is None:
            return {}
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.exception("Error fetching repo %s/%s: %s", owner, repo, e)
            return {}

    async def get_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Get language statistics for a repository."""
        response = await self._request_with_backoff(
            "GET", f"{self.base_url}/repos/{owner}/{repo}/languages"
        )
        if response is None:
            return {}
        try:
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.exception("Error fetching languages for %s/%s: %s", owner, repo, e)
            return {}

    async def get_repo_commits(self, owner: str, repo: str, since: datetime | None = None) -> int:
        """Get commit count for a repository."""
        if not since:
            since = datetime.now() - timedelta(days=365)  # Default to last year

        response = await self._request_with_backoff(
            "GET",
            f"{self.base_url}/repos/{owner}/{repo}/commits",
            params={"since": since.isoformat(), "per_page": 1},
        )

        if response is None:
            return 0

        try:
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

        except httpx.HTTPStatusError as e:
            logger.exception("Error fetching commits for %s/%s: %s", owner, repo, e)
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

        # Get language statistics (parallel requests for better performance)
        languages: dict[str, int] = {}
        repos_to_check = owned_repos[:10]  # Limit to top 10 repos to avoid rate limiting
        language_results = await asyncio.gather(
            *[self.get_repo_languages(username, repo["name"]) for repo in repos_to_check],
            return_exceptions=True,
        )
        for result in language_results:
            if isinstance(result, BaseException):
                logger.warning(f"Error fetching languages: {result}")
                continue
            for lang, bytes_count in result.items():
                languages[lang] = languages.get(lang, 0) + bytes_count

        # Sort languages by usage
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        total_bytes = sum(languages.values())

        # Get pinned repos (or fall back to recent if no pinned)
        pinned = await self.get_pinned_repos(username)
        featured_repos = (
            pinned
            if pinned
            else [
                {
                    "name": r["name"],
                    "description": r.get("description"),
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "language": r.get("language"),
                    "html_url": r.get("html_url"),
                }
                for r in owned_repos[:6]
            ]
        )

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
                {
                    "name": lang,
                    "percentage": round(bytes_count / total_bytes * 100, 1)
                    if total_bytes > 0
                    else 0,
                }
                for lang, bytes_count in top_languages
            ],
            "featured_repos": featured_repos,
        }

    async def get_pinned_repos(self, username: str) -> list[dict]:
        """Get pinned repositories using GitHub GraphQL API."""
        query = """
        query($userName: String!) {
          user(login: $userName) {
            pinnedItems(first: 6, types: REPOSITORY) {
              nodes {
                ... on Repository {
                  name
                  description
                  url
                  stargazerCount
                  forkCount
                  primaryLanguage {
                    name
                  }
                }
              }
            }
          }
        }
        """

        response = await self._request_with_backoff(
            "POST",
            "https://api.github.com/graphql",
            json={"query": query, "variables": {"userName": username}},
        )

        if response is None:
            return []

        try:
            response.raise_for_status()
            data = response.json()

            if "errors" in data:
                logger.warning("GraphQL errors for %s: %s", username, data["errors"])
                return []

            nodes = data.get("data", {}).get("user", {}).get("pinnedItems", {}).get("nodes", [])

            # Transform to match existing repo structure
            return [
                {
                    "name": repo.get("name"),
                    "description": repo.get("description"),
                    "html_url": repo.get("url"),
                    "stars": repo.get("stargazerCount", 0),
                    "forks": repo.get("forkCount", 0),
                    "language": (
                        repo.get("primaryLanguage", {}).get("name")
                        if repo.get("primaryLanguage")
                        else None
                    ),
                }
                for repo in nodes
                if repo  # Filter out null nodes
            ]
        except httpx.HTTPStatusError as e:
            logger.exception("Error fetching pinned repos for %s: %s", username, e)
            return []

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
