"""
Project model
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, JSON, func
import uuid
from sqlalchemy.orm import relationship
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    technologies = Column(JSON)  # List of technologies used
    github_url = Column(String(500))
    live_url = Column(String(500))
    image_url = Column(String(500))
    company_id = Column(String, ForeignKey("companies.id", ondelete="CASCADE"))
    featured = Column(Boolean, default=False)
    order_index = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    company = relationship("Company", back_populates="projects")

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "technologies": self.technologies or [],
            "github_url": self.github_url,
            "live_url": self.live_url,
            "image_url": self.image_url,
            "company_id": self.company_id,
            "company": self.company.name if self.company else None,
            "featured": self.featured,
            "order_index": self.order_index
        }