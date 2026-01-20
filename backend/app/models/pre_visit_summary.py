import json
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, SmallInteger, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class PreVisitSummary(Base):
    """Pre-visit summary model for storing pre-consultation information."""

    __tablename__ = "pre_visit_summaries"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=True)
    scheduled_visit = Column(Date, nullable=True)
    chief_complaint = Column(Text, nullable=True)
    structured_data_json = Column(Text, nullable=True)  # JSON string for SQLite
    phq9_score = Column(SmallInteger, nullable=True)
    gad7_score = Column(SmallInteger, nullable=True)
    doctor_viewed = Column(Boolean, default=False)
    doctor_viewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="pre_visit_summaries")
    conversation = relationship("Conversation", back_populates="pre_visit_summary")
    appointment = relationship("Appointment", back_populates="pre_visit_summary", uselist=False)

    @property
    def structured_data(self):
        return json.loads(self.structured_data_json) if self.structured_data_json else None

    @structured_data.setter
    def structured_data(self, value):
        self.structured_data_json = json.dumps(value) if value else None

    def __repr__(self):
        return f"<PreVisitSummary scheduled={self.scheduled_visit}>"
