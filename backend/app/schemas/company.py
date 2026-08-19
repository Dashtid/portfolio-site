"""
Company Pydantic schemas
"""

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas._validators import validate_safe_url


class CompanyBase(BaseModel):
    name: str
    title: str | None = None
    description: str | None = None
    detailed_description: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    logo_url: str | None = None
    website: str | None = None
    order_index: int | None = 0
    video_url: str | None = None
    video_title: str | None = None
    map_url: str | None = None
    map_title: str | None = None
    responsibilities: list[str] | None = Field(None, max_length=50)  # Max 50 items
    technologies: list[str] | None = Field(None, max_length=100)  # Max 100 items
    outcomes: list[str] | None = Field(None, max_length=50)  # Max 50 items
    # Curated CV bullets — a short selection for the printed CV, kept apart
    # from the two lists above (which describe the role for the public detail
    # page). Longer per-item cap: a CV bullet routinely runs past 200 chars.
    cv_highlights: list[str] | None = Field(None, max_length=10)

    @field_validator("logo_url", "website", "video_url", "map_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v, "URL")

    @field_validator("responsibilities", "technologies", "outcomes", mode="before")
    @classmethod
    def validate_list_items(cls, v: list[str] | None) -> list[str] | None:
        """Validate list items have reasonable length."""
        if v is None:
            return v
        for item in v:
            if len(item) > 200:
                raise ValueError("List item exceeds maximum length of 200 characters")
        return v

    @field_validator("cv_highlights", mode="before")
    @classmethod
    def validate_cv_highlights(cls, v: list[str] | None) -> list[str] | None:
        """CV bullets are full sentences; the 200-char cap above is too tight."""
        if v is None:
            return v
        for item in v:
            if len(item) > 500:
                raise ValueError("CV highlight exceeds maximum length of 500 characters")
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    title: str | None = None
    description: str | None = None
    detailed_description: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    logo_url: str | None = None
    website: str | None = None
    order_index: int | None = None
    video_url: str | None = None
    video_title: str | None = None
    map_url: str | None = None
    map_title: str | None = None
    responsibilities: list[str] | None = Field(None, max_length=50)  # Max 50 items
    technologies: list[str] | None = Field(None, max_length=100)  # Max 100 items
    outcomes: list[str] | None = Field(None, max_length=50)  # Max 50 items
    # Curated CV bullets — a short selection for the printed CV, kept apart
    # from the two lists above (which describe the role for the public detail
    # page). Longer per-item cap: a CV bullet routinely runs past 200 chars.
    cv_highlights: list[str] | None = Field(None, max_length=10)

    @field_validator("logo_url", "website", "video_url", "map_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v, "URL")

    @field_validator("responsibilities", "technologies", "outcomes", mode="before")
    @classmethod
    def validate_list_items(cls, v: list[str] | None) -> list[str] | None:
        """Validate list items have reasonable length."""
        if v is None:
            return v
        for item in v:
            if len(item) > 200:
                raise ValueError("List item exceeds maximum length of 200 characters")
        return v

    @field_validator("cv_highlights", mode="before")
    @classmethod
    def validate_cv_highlights(cls, v: list[str] | None) -> list[str] | None:
        """CV bullets are full sentences; the 200-char cap above is too tight."""
        if v is None:
            return v
        for item in v:
            if len(item) > 500:
                raise ValueError("CV highlight exceeds maximum length of 500 characters")
        return v


class CompanyResponse(CompanyBase):
    id: str
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}
