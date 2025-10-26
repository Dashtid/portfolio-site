"""
Document Model

Represents academic papers, theses, and other downloadable documents.
"""

from sqlalchemy import Column, String, Integer, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class Document(Base):
    """
    Document model for academic papers and downloadable content.

    Attributes:
        id: Unique identifier (UUID string)
        title: Document title
        description: Brief description of the document
        document_type: Type of document (thesis, paper, report, etc.)
        file_path: Relative path to file in static directory
        file_size: File size in bytes
        file_url: Public URL for downloading the document
        published_date: Date document was published/completed
        created_at: Timestamp when record was created
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    document_type = Column(String, nullable=False)  # thesis, paper, report, etc.
    file_path = Column(String, nullable=False)  # e.g., "documents/bachelor-thesis.pdf"
    file_size = Column(Integer, nullable=False)  # Size in bytes
    file_url = Column(String, nullable=False)  # Public download URL
    published_date = Column(String, nullable=True)  # ISO date string
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Document {self.title} ({self.document_type})>"
