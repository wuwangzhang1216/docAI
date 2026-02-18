import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ClinicalNote(Base):
    """Clinical note model for storing doctor notes and AI drafts."""

    __tablename__ = "clinical_notes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=True, index=True)
    visit_date = Column(Date, nullable=True)
    transcript_url = Column(String(500), nullable=True)
    ai_draft = Column(Text, nullable=True)
    final_note = Column(Text, nullable=True)
    is_reviewed = Column(Boolean, default=False)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="clinical_notes")
    doctor = relationship("Doctor", back_populates="clinical_notes")

    def __repr__(self):
        return f"<ClinicalNote {self.visit_date} reviewed={self.is_reviewed}>"
