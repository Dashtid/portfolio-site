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


class SkillResponse(BaseModel):
    """PUBLIC skill payload — deliberately WITHOUT proficiency_level/years.

    Nothing on the site renders those numbers (verified by diffing the live
    homepage against its own __INITIAL_STATE__: the skill names appear only
    inside the baked state blob, never in visible markup), yet the public
    endpoint served a 0-100 self-rating for all 19 rows to anyone who curled
    it -- including 'Security Auditing: 95', the joint-highest number on a
    site whose one earned certification is Security+. An unfalsifiable rating
    nobody chose to display is a liability, not proof. The values still exist
    in the DB and stay editable in /admin/skills via SkillAdminResponse; the
    site simply stops publishing them.
    """

    id: str
    name: str
    category: str | None = None
    order_index: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SkillAdminResponse(SkillBase):
    """Full skill payload — admin-authenticated callers only."""

    id: str
    created_at: datetime

    model_config = {"from_attributes": True}
