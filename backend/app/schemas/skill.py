"""
Skill Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None  # 'language', 'framework', 'tool', 'database'
    proficiency: Optional[int] = Field(None, ge=1, le=5)  # 1-5 scale
    years_experience: Optional[float] = Field(None, ge=0)
    order_index: Optional[int] = 0


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    proficiency: Optional[int] = Field(None, ge=1, le=5)
    years_experience: Optional[float] = Field(None, ge=0)
    order_index: Optional[int] = None


class SkillResponse(SkillBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True