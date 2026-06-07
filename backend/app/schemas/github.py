from pydantic import BaseModel


class LanguageStat(BaseModel):
    name: str
    percentage: float


class FeaturedRepo(BaseModel):
    name: str | None = None
    description: str | None = None
    html_url: str | None = None
    stars: int = 0
    forks: int = 0
    language: str | None = None


class GitHubStats(BaseModel):
    username: str
    avatar_url: str | None = None
    bio: str | None = None
    public_repos: int = 0
    followers: int = 0
    following: int = 0
    total_stars: int = 0
    total_forks: int = 0
    total_watchers: int = 0
    top_languages: list[LanguageStat] = []
    featured_repos: list[FeaturedRepo] = []
