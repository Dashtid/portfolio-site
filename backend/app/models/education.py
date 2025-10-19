from sqlalchemy import Column, Integer, String, Date, Text, Boolean
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
    is_certification = Column(Boolean, default=False)
    certificate_number = Column(String(100))
    order = Column(Integer, default=0)  # For custom sorting