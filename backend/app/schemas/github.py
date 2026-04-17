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


class ProjectStats(BaseModel):
    name: str | None = None
    full_name: str | None = None
    description: str | None = None
    stars: int = 0
    forks: int = 0
    watchers: int = 0
    open_issues: int = 0
    created_at: str | None = None
    updated_at: str | None = None
    size: int = 0
    commit_count: int = 0
    languages: dict[str, int] = {}
    topics: list[str] = []
    homepage: str | None = None
    html_url: str | None = None


class RepoSummary(BaseModel):
    name: str | None = None
    full_name: str | None = None
    description: str | None = None
    html_url: str | None = None
    language: str | None = None
    stargazers_count: int = 0
    forks_count: int = 0
    updated_at: str | None = None
    fork: bool = False


class RepoLanguageStat(BaseModel):
    name: str
    bytes: int
    percentage: float


class RepoLanguages(BaseModel):
    total_bytes: int = 0
    languages: list[RepoLanguageStat] = []
