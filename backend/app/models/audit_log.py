import json
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AuditLog(Base):
    """Audit log model for tracking user actions."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(36), nullable=True)
    details_json = Column(Text, nullable=True)  # JSON string for SQLite
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    @property
    def details(self):
        return json.loads(self.details_json) if self.details_json else None

    @details.setter
    def details(self, value):
        self.details_json = json.dumps(value) if value else None

    def __repr__(self):
        return f"<AuditLog {self.action} by {self.user_id}>"
