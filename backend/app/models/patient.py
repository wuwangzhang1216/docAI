import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    """Patient profile model."""

    __tablename__ = "patients"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=True)
    phone = Column(String(20), nullable=True)
    emergency_contact = Column(String(100), nullable=True)
    emergency_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(50), nullable=True)
    primary_doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=True)
    consent_signed = Column(Boolean, default=False)
    consent_signed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Extended profile fields
    gender = Column(String(20), nullable=True)
    preferred_language = Column(String(10), nullable=True, default="en")
    address = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)

    # Medical information
    current_medications = Column(Text, nullable=True)
    medical_conditions = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)

    # Mental health context (for doctor's reference)
    therapy_history = Column(Text, nullable=True)
    mental_health_goals = Column(Text, nullable=True)
    support_system = Column(Text, nullable=True)
    triggers_notes = Column(Text, nullable=True)
    coping_strategies = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", back_populates="patient_profile")
    primary_doctor = relationship("Doctor", back_populates="patients")
    checkins = relationship("DailyCheckin", back_populates="patient")
    assessments = relationship("Assessment", back_populates="patient")
    conversations = relationship("Conversation", back_populates="patient")
    risk_events = relationship("RiskEvent", back_populates="patient")
    clinical_notes = relationship("ClinicalNote", back_populates="patient")
    pre_visit_summaries = relationship("PreVisitSummary", back_populates="patient")
    appointments = relationship("Appointment", back_populates="patient")

    @property
    def full_name(self) -> str:
        """Return the full name by combining first and last name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Patient {self.full_name}>"
