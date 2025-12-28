import re
from datetime import date

from pydantic import BaseModel, Field, field_validator

# Pattern for safe URLs: http(s)://, relative paths, or empty
SAFE_URL_PATTERN = re.compile(r"^(https?://|/[^/]|$)")


def validate_safe_url(v: str | None) -> str | None:
    """Validate URL is safe (HTTP(S) or relative path, no XSS vectors)."""
    if v is None or v == "":
        return v
    if not SAFE_URL_PATTERN.match(v):
        raise ValueError("URL must be an HTTP(S) URL or relative path starting with /")
    return v


class EducationBase(BaseModel):
    institution: str = Field(..., min_length=1, max_length=200)
    degree: str = Field(..., min_length=1, max_length=200)
    field_of_study: str | None = Field(None, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=2000)
    logo_url: str | None = None
    is_certification: bool = False
    certificate_number: str | None = Field(None, max_length=100)
    certificate_url: str | None = None
    order_index: int = Field(0, ge=0)  # Must be non-negative

    @field_validator("logo_url", "certificate_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v)


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = Field(None, min_length=1, max_length=200)
    degree: str | None = Field(None, min_length=1, max_length=200)
    field_of_study: str | None = Field(None, max_length=200)
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = Field(None, max_length=200)
    description: str | None = Field(None, max_length=2000)
    logo_url: str | None = None
    is_certification: bool | None = None
    certificate_number: str | None = Field(None, max_length=100)
    certificate_url: str | None = None
    order_index: int | None = Field(None, ge=0)  # Must be non-negative

    @field_validator("logo_url", "certificate_url", mode="before")
    @classmethod
    def validate_urls(cls, v: str | None) -> str | None:
        """Validate all URL fields are safe."""
        return validate_safe_url(v)


class Education(EducationBase):
    id: int

    model_config = {"from_attributes": True}
