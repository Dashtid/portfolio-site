"""
Skill Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    name: str
    category: str | None = None  # 'language', 'framework', 'tool', 'database'
    proficiency: int | None = Field(None, ge=0, le=100)  # 0-100 percentage scale
    years_experience: float | None = Field(None, ge=0)
    order_index: int | None = 0


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    proficiency: int | None = Field(None, ge=0, le=100)
    years_experience: float | None = Field(None, ge=0)
    order_index: int | None = None


class SkillResponse(SkillBase):
    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
