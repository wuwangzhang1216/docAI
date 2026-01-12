import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database import Base


class Doctor(Base):
    """Doctor profile model."""
    __tablename__ = "doctors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    license_number = Column(String(50), nullable=True)
    specialty = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Contact information
    phone = Column(String(20), nullable=True)

    # Professional information
    bio = Column(Text, nullable=True)
    years_of_experience = Column(String(10), nullable=True)
    education = Column(Text, nullable=True)
    languages = Column(String(255), nullable=True)

    # Clinic information
    clinic_name = Column(String(200), nullable=True)
    clinic_address = Column(String(255), nullable=True)
    clinic_city = Column(String(100), nullable=True)
    clinic_country = Column(String(100), nullable=True)

    # Availability
    consultation_hours = Column(String(255), nullable=True)

    # Relationships
    user = relationship("User", back_populates="doctor_profile", foreign_keys=[user_id])
    patients = relationship("Patient", back_populates="primary_doctor")
    clinical_notes = relationship("ClinicalNote", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")

    @property
    def full_name(self) -> str:
        """Return the full name by combining first and last name."""
        return f"{self.first_name} {self.last_name}"

    def __repr__(self):
        return f"<Doctor {self.full_name}>"
