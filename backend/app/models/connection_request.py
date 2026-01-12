"""Patient connection request model for doctor-patient relationships."""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Index
from sqlalchemy.orm import relationship

from app.database import Base


class ConnectionStatus(str, PyEnum):
    """Status of a patient connection request."""
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PatientConnectionRequest(Base):
    """
    Represents a connection request from a doctor to a patient.

    Doctors can send connection requests to patients by email.
    Patients can accept or reject requests.
    Only one PENDING request can exist per doctor-patient pair.
    """
    __tablename__ = "patient_connection_requests"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    doctor_id = Column(
        String(36),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    patient_id = Column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status = Column(
        Enum(ConnectionStatus),
        default=ConnectionStatus.PENDING,
        nullable=False,
        index=True
    )
    message = Column(Text, nullable=True)  # Optional message from doctor to patient
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    responded_at = Column(DateTime, nullable=True)  # When patient accepted/rejected

    # Relationships
    doctor = relationship("Doctor", backref="connection_requests_sent")
    patient = relationship("Patient", backref="connection_requests_received")

    # Indexes
    __table_args__ = (
        # Index for finding pending requests efficiently
        Index('idx_pending_requests', 'doctor_id', 'patient_id', 'status'),
    )

    def __repr__(self):
        return f"<PatientConnectionRequest {self.id} doctor={self.doctor_id} patient={self.patient_id} status={self.status}>"
