"""
Skill Pydantic schemas
"""

from datetime import datetime

from pydantic import BaseModel, Field


class SkillBase(BaseModel):
    name: str
    category: str | None = None  # 'language', 'framework', 'tool', 'database'
    proficiency: int | None = Field(None, ge=1, le=5)  # 1-5 scale
    years_experience: float | None = Field(None, ge=0)
    order_index: int | None = 0


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    proficiency: int | None = Field(None, ge=1, le=5)
    years_experience: float | None = Field(None, ge=0)
    order_index: int | None = None


class SkillResponse(SkillBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
