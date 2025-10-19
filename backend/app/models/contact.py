"""
Contact form submission model
"""
from sqlalchemy import Column, String, Text, DateTime, func
import uuid
from app.database import Base


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(String(255))
    message = Column(Text, nullable=False)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    status = Column(String(50), default="unread")  # 'unread', 'read', 'replied'

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }