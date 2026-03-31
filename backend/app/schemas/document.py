"""
Document Schemas

Pydantic schemas for document API validation and serialization.
"""

import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

# Pattern for safe URLs: http(s)://, relative paths, or None
# Blocks javascript:, data:, vbscript: and other XSS vectors
SAFE_URL_PATTERN = re.compile(r"^(https?://|/[^/]|$)")


def validate_safe_url(v: str | None, field_name: str) -> str | None:
    """Validate URL is safe (HTTP(S) or relative path, no XSS vectors)."""
    if v is None or v == "":
        return v
    if not SAFE_URL_PATTERN.match(v):
        raise ValueError(f"{field_name} must be an HTTP(S) URL or relative path starting with /")
    return v


class DocumentBase(BaseModel):
    """Base document schema with common fields"""

    title: str = Field(..., description="Document title")
    description: str | None = Field(None, description="Brief description")
    document_type: str = Field(..., description="Type: thesis, paper, report, etc.")
    file_path: str = Field(..., description="Relative path to file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_url: str = Field(..., description="Public download URL")
    published_date: str | None = Field(None, description="Publication date (ISO format)")
    order_index: int = Field(0, description="Display order (lower = first)")

    @field_validator("file_url")
    @classmethod
    def validate_file_url(cls, v: str) -> str:
        result = validate_safe_url(v, "file_url")
        if result is None:
            raise ValueError("file_url is required")
        return result

    @field_validator("file_path")
    @classmethod
    def validate_file_path(cls, v: str) -> str:
        result = validate_safe_url(v, "file_path")
        if result is None:
            raise ValueError("file_path is required")
        return result


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""

    id: str = Field(..., description="Unique identifier (UUID)")


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document"""

    title: str | None = None
    description: str | None = None
    document_type: str | None = None
    file_path: str | None = None
    file_size: int | None = Field(None, gt=0)
    file_url: str | None = None
    published_date: str | None = None


class DocumentResponse(DocumentBase):
    """Schema for document API responses"""

    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
