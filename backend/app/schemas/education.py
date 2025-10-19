from pydantic import BaseModel
from datetime import date
from typing import Optional

class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_certification: bool = False
    certificate_number: Optional[str] = None
    order: int = 0

class EducationCreate(EducationBase):
    pass

class EducationUpdate(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_certification: Optional[bool] = None
    certificate_number: Optional[str] = None
    order: Optional[int] = None

class Education(EducationBase):
    id: int

    class Config:
        from_attributes = True