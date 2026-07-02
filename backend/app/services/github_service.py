"""
GitHub API service for fetching live project statistics
"""

import asyncio
import logging
import time
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# Timeout configuration for external API calls
DEFAULT_TIMEOUT = httpx.Timeout(timeout=10.0, pool=5.0)

# Rate limit configuration
MAX_RETRIES = 3
BASE_BACKOFF_SECONDS = 1.0

# PERF-04: TTL cache for the public portfolio-stats endpoint. GitHub's API
# rate-limits unauthenticated callers at 60 req/hr and authenticated ones at
# 5000/hr; cache hits also shave the ~3-5 round-trips that
# get_portfolio_stats() makes per call (user-info + repos + per-repo
# languages + pinned). 5 minutes is long enough to absorb a Lighthouse run
# and a normal browse session, short enough that pushed commits show up in
# under 5 min on the public site.
GITHUB_STATS_CACHE_TTL_SECONDS = 300
# A failed fetch (GitHub down/rate-limited) is cached only this long, so an
# outage shows zeros for seconds, not the full 5-minute TTL. When a stale
# good value exists it is served instead for the same window.
GITHUB_STATS_FAILURE_TTL_SECONDS = 30
# Hard deadline for the whole portfolio-stats fan-out. Individual requests
# already retry with backoff (up to ~30s each in the worst case); without
# an outer bound a cold cache miss can hang a visitor's request for the
# sum of every stage's retries.
PORTFOLIO_STATS_DEADLINE_SECONDS = 15.0
# The public endpoint accepts ANY syntactically valid username, so the
# per-username cache and lock dicts must be bounded or an attacker can
# grow them without limit.
STATS_CACHE_MAX_ENTRIES = 32


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
        # PERF-04: per-username portfolio-stats cache.
        #   username -> (cached_value, expires_at_monotonic, fetch_ok)
        # fetch_ok=False marks a failure entry (zeros cached briefly so an
        # outage doesn't hammer GitHub, but recovery is quick).
        # In-process only — Fly runs us as a single replica today; if we
        # ever scale to >1 instance, swap for a shared redis/turso layer.
        self._stats_cache: dict[str, tuple[dict[str, Any], float, bool]] = {}
        # Per-username asyncio.Lock so a stampede of cache-miss requests
        # collapses to a single upstream fetch (the rest await the lock,
        # see the populated cache, and serve from it).
        self._stats_locks: dict[str, asyncio.Lock] = {}

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
            result: dict[str, Any] = response.json()
            return result
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

    async def get_repo_languages(self, owner: str, repo: str) -> dict[str, int]:
        """Get language statistics for a repository."""
        response = await self._request_with_backoff(
            "GET", f"{self.base_url}/repos/{owner}/{repo}/languages"
        )
        if response is None:
            return {}
        try:
            response.raise_for_status()
            result: dict[str, int] = response.json()
            return result
        except httpx.HTTPStatusError as e:
            logger.exception("Error fetching languages for %s/%s: %s", owner, repo, e)
            return {}

    async def get_portfolio_stats(self, username: str) -> dict[str, Any]:
        """Get aggregated statistics for portfolio display.

        PERF-04: cached per-username for GITHUB_STATS_CACHE_TTL_SECONDS.
        On miss, takes a per-username asyncio.Lock so concurrent first-hit
        callers collapse to a single upstream fetch instead of stampeding
        GitHub. The whole fan-out runs under an overall deadline; a failed
        or timed-out fetch serves the last good value when one exists and
        is only cached for GITHUB_STATS_FAILURE_TTL_SECONDS.
        """
        now = time.monotonic()
        cached = self._stats_cache.get(username)
        if cached is not None and cached[1] > now:
            return cached[0]

        # Per-username lock so concurrent cache-miss callers don't stampede.
        lock = self._stats_locks.setdefault(username, asyncio.Lock())
        async with lock:
            # Re-check inside the lock: another coroutine may have already
            # populated the cache while we were waiting.
            cached = self._stats_cache.get(username)
            if cached is not None and cached[1] > time.monotonic():
                return cached[0]

            try:
                async with asyncio.timeout(PORTFOLIO_STATS_DEADLINE_SECONDS):
                    result = await self._fetch_portfolio_stats(username)
            except TimeoutError:
                logger.warning(
                    "GitHub stats fan-out for %s exceeded %.0fs deadline",
                    username,
                    PORTFOLIO_STATS_DEADLINE_SECONDS,
                )
                result = None

            if result is not None and not self._is_fetch_failure(result):
                self._store(username, result, GITHUB_STATS_CACHE_TTL_SECONDS, ok=True)
                return result

            # Fetch failed. Prefer the last known-good value (stale beats
            # zeros on the public site); re-store it briefly so the next
            # requests don't re-hit GitHub mid-outage.
            if cached is not None and cached[2]:
                logger.warning("Serving stale GitHub stats for %s after failed refresh", username)
                self._store(username, cached[0], GITHUB_STATS_FAILURE_TTL_SECONDS, ok=True)
                return cached[0]

            empty = result if result is not None else self._empty_stats(username)
            self._store(username, empty, GITHUB_STATS_FAILURE_TTL_SECONDS, ok=False)
            return empty

    def _store(self, username: str, value: dict[str, Any], ttl: float, *, ok: bool) -> None:
        """Cache a stats entry and keep the cache/lock dicts bounded."""
        self._stats_cache[username] = (value, time.monotonic() + ttl, ok)
        while len(self._stats_cache) > STATS_CACHE_MAX_ENTRIES:
            evictee = min(self._stats_cache, key=lambda k: self._stats_cache[k][1])
            del self._stats_cache[evictee]
            # Drop the evictee's lock too unless a coroutine is mid-fetch
            # with it (those keep their reference; a later request simply
            # creates a fresh lock).
            evicted_lock = self._stats_locks.get(evictee)
            if evicted_lock is not None and not evicted_lock.locked():
                del self._stats_locks[evictee]

    @staticmethod
    def _is_fetch_failure(result: dict[str, Any]) -> bool:
        """Heuristic for "GitHub gave us nothing".

        A real user always has an avatar_url; repos/pinned may legitimately
        be empty. All three empty together means every upstream stage
        failed, so the zeros must not be cached at full TTL.
        """
        return (
            not result.get("avatar_url")
            and not result.get("featured_repos")
            and not result.get("public_repos")
        )

    @staticmethod
    def _empty_stats(username: str) -> dict[str, Any]:
        """Zeroed stats shape (matches GitHubStats schema defaults)."""
        return {
            "username": username,
            "avatar_url": None,
            "bio": None,
            "public_repos": 0,
            "followers": 0,
            "following": 0,
            "total_stars": 0,
            "total_forks": 0,
            "total_watchers": 0,
            "top_languages": [],
            "featured_repos": [],
        }

    async def _fetch_portfolio_stats(self, username: str) -> dict[str, Any]:
        """Underlying GitHub fan-out — only called on cache miss.

        user-info, the repo list, and pinned repos are independent
        upstream calls, so they run concurrently; only the per-repo
        language calls need the repo list first.
        """
        user_info, repos, pinned = await asyncio.gather(
            self.get_user_info(username),
            self.get_user_repos(username),
            self.get_pinned_repos(username),
        )

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
                logger.warning("Error fetching languages: %s", result)
                continue
            for lang, bytes_count in result.items():
                languages[lang] = languages.get(lang, 0) + bytes_count

        # Sort languages by usage
        top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]
        total_bytes = sum(languages.values())

        # Pinned repos (fetched concurrently above) or recent as fallback
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


# Singleton instance
github_service = GitHubService()
