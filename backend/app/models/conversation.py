import uuid
import json
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ConversationType(str, PyEnum):
    """Conversation type enumeration."""
    SUPPORTIVE_CHAT = "SUPPORTIVE_CHAT"
    PRE_VISIT = "PRE_VISIT"


class Conversation(Base):
    """Conversation model for storing chat history."""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    conv_type = Column(Enum(ConversationType), nullable=False)
    messages_json = Column(Text, default="[]")  # JSON string for SQLite
    summary = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="conversations")
    risk_events = relationship("RiskEvent", back_populates="conversation")
    pre_visit_summary = relationship("PreVisitSummary", back_populates="conversation", uselist=False)

    @property
    def messages(self):
        return json.loads(self.messages_json) if self.messages_json else []
    
    @messages.setter
    def messages(self, value):
        self.messages_json = json.dumps(value) if value else "[]"

    def __repr__(self):
        return f"<Conversation {self.conv_type} active={self.is_active}>"
