from datetime import date

from pydantic import BaseModel


class EducationBase(BaseModel):
    institution: str
    degree: str
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = None
    description: str | None = None
    logo_url: str | None = None
    is_certification: bool = False
    certificate_number: str | None = None
    order: int = 0


class EducationCreate(EducationBase):
    pass


class EducationUpdate(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = None
    description: str | None = None
    logo_url: str | None = None
    is_certification: bool | None = None
    certificate_number: str | None = None
    order: int | None = None


class Education(EducationBase):
    id: int

    class Config:
        from_attributes = True
