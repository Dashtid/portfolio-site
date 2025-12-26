from sqlalchemy import Boolean, Column, Date, Integer, String, Text

from app.database import Base


class Education(Base):
    __tablename__ = "education"

    id = Column(Integer, primary_key=True, index=True)
    institution = Column(String(200), nullable=False)
    degree = Column(String(200), nullable=False)
    field_of_study = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    location = Column(String(200))
    description = Column(Text)
    logo_url = Column(String(500))  # Institution logo
    is_certification = Column(Boolean, default=False)
    certificate_number = Column(String(100))
    certificate_url = Column(String(500))  # URL to certificate/credential
    order = Column(Integer, default=0, index=True)  # For custom sorting
