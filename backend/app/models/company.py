"""
Company/Experience model
"""
from sqlalchemy import Column, String, Text, Date, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    location = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)  # Null means current job
    logo_url = Column(String(500))
    website = Column(String(500))
    order_index = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "logo_url": self.logo_url,
            "website": self.website,
            "order_index": self.order_index
        }