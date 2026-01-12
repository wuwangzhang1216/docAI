import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class UserType(str, PyEnum):
    """User type enumeration."""
    PATIENT = "PATIENT"
    DOCTOR = "DOCTOR"
    ADMIN = "ADMIN"


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    user_type = Column(Enum(UserType), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Password management - for doctor-created accounts
    password_must_change = Column(Boolean, default=False)
    created_by_doctor_id = Column(String(36), ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    patient_profile = relationship("Patient", back_populates="user", uselist=False)
    doctor_profile = relationship(
        "Doctor",
        back_populates="user",
        uselist=False,
        primaryjoin="User.id == Doctor.user_id",
        foreign_keys="[Doctor.user_id]"
    )
    audit_logs = relationship("AuditLog", back_populates="user")
    created_by_doctor = relationship("Doctor", foreign_keys=[created_by_doctor_id])

    def __repr__(self):
        return f"<User {self.email} ({self.user_type})>"
