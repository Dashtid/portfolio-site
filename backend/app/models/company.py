"""
Company/Experience model
"""

import uuid

from sqlalchemy import JSON, Column, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    title = Column(String(255))
    description = Column(Text)
    detailed_description = Column(Text, nullable=True)  # Extended description for detail page
    location = Column(String(255))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)  # Null means current job
    logo_url = Column(String(500))
    website = Column(String(500))
    order_index = Column(Integer, default=0)

    # Detail page media
    video_url = Column(String(500), nullable=True)  # YouTube embed URL
    video_title = Column(String(255), nullable=True)
    map_url = Column(String(500), nullable=True)  # Google Maps embed URL
    map_title = Column(String(255), nullable=True)

    # Structured data for detail page
    responsibilities = Column(JSON, nullable=True)  # List of responsibilities
    technologies = Column(JSON, nullable=True)  # List of technologies used

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
            "detailed_description": self.detailed_description,
            "location": self.location,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "logo_url": self.logo_url,
            "website": self.website,
            "order_index": self.order_index,
            "video_url": self.video_url,
            "video_title": self.video_title,
            "map_url": self.map_url,
            "map_title": self.map_title,
            "responsibilities": self.responsibilities,
            "technologies": self.technologies,
        }
