"""
Skill Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    category: str | None = Field(None, max_length=50)  # 'language', 'framework', 'tool', 'database'
    proficiency_level: int | None = Field(None, ge=0, le=100)  # 0-100 percentage scale
    years_of_experience: float | None = Field(None, ge=0, le=50)  # Max 50 years
    order_index: int | None = Field(0, ge=0)  # Must be non-negative


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    category: str | None = Field(None, max_length=50)
    proficiency_level: int | None = Field(None, ge=0, le=100)
    years_of_experience: float | None = Field(None, ge=0, le=50)
    order_index: int | None = Field(None, ge=0)


class SkillResponse(SkillBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
