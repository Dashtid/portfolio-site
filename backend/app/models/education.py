from sqlalchemy import Boolean, Column, Date, Integer, String, Text

from app.database import Base


class Education(Base):
    __tablename__ = "education"

    # DB-09: PRIMARY KEY already implies an index; the explicit index=True
    # was a duplicate. Dropped.
    id = Column(Integer, primary_key=True)
    institution = Column(String(200), nullable=False)
    degree = Column(String(200), nullable=False)
    field_of_study = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    location = Column(String(200))
    description = Column(Text)
    logo_url = Column(String(500))  # Institution logo
    # DB-02: indexed because the public listing and detail pages split on
    # is_certification (degrees vs. certifications); a small index pays off
    # even at low cardinality given how often this column is filtered on.
    is_certification = Column(Boolean, default=False, index=True)
    certificate_number = Column(String(100))
    certificate_url = Column(String(500))  # URL to certificate/credential
    order_index = Column(
        Integer, default=0, index=True
    )  # For custom sorting (renamed from 'order' for consistency)
