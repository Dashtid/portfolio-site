"""
Skill/Technology model
"""

import uuid

from sqlalchemy import Column, DateTime, Float, Integer, String, func

from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    category = Column(String(50))  # 'language', 'framework', 'tool', 'database', etc.
    proficiency = Column(Integer)  # 1-5 scale
    years_experience = Column(Float)
    order_index = Column(Integer, default=0, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "proficiency": self.proficiency,
            "years_experience": self.years_experience,
            "order_index": self.order_index,
        }
