"""
Document Schemas

Pydantic schemas for document API validation and serialization.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema with common fields"""

    title: str = Field(..., description="Document title")
    description: str | None = Field(None, description="Brief description")
    document_type: str = Field(..., description="Type: thesis, paper, report, etc.")
    file_path: str = Field(..., description="Relative path to file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_url: str = Field(..., description="Public download URL")
    published_date: str | None = Field(None, description="Publication date (ISO format)")


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

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
