"""
Document Schemas

Pydantic schemas for document API validation and serialization.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DocumentBase(BaseModel):
    """Base document schema with common fields"""
    title: str = Field(..., description="Document title")
    description: Optional[str] = Field(None, description="Brief description")
    document_type: str = Field(..., description="Type: thesis, paper, report, etc.")
    file_path: str = Field(..., description="Relative path to file")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_url: str = Field(..., description="Public download URL")
    published_date: Optional[str] = Field(None, description="Publication date (ISO format)")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document"""
    id: str = Field(..., description="Unique identifier (UUID)")


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document"""
    title: Optional[str] = None
    description: Optional[str] = None
    document_type: Optional[str] = None
    file_path: Optional[str] = None
    file_size: Optional[int] = Field(None, gt=0)
    file_url: Optional[str] = None
    published_date: Optional[str] = None


class DocumentResponse(DocumentBase):
    """Schema for document API responses"""
    id: str
    created_at: datetime

    class Config:
        from_attributes = True  # Pydantic v2 (was orm_mode in v1)
