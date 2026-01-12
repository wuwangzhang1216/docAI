import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship

from app.database import Base


class RiskLevel(str, PyEnum):
    """Risk level enumeration."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskType(str, PyEnum):
    """Risk type enumeration.

    Includes political trauma-specific types for refugees/dissidents.
    """
    SUICIDAL = "SUICIDAL"
    SELF_HARM = "SELF_HARM"
    VIOLENCE = "VIOLENCE"
    PERSECUTION_FEAR = "PERSECUTION_FEAR"  # Political trauma: fear of being found/tracked
    OTHER = "OTHER"


class RiskEvent(Base):
    """Risk event model for tracking detected risks."""
    __tablename__ = "risk_events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    risk_type = Column(Enum(RiskType), nullable=True)
    trigger_text = Column(Text, nullable=True)
    ai_confidence = Column(Float, nullable=True)  # 0.00 - 1.00
    doctor_reviewed = Column(Boolean, default=False, index=True)
    doctor_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    patient = relationship("Patient", back_populates="risk_events")
    conversation = relationship("Conversation", back_populates="risk_events")

    def __repr__(self):
        return f"<RiskEvent {self.risk_level} {self.risk_type}>"
