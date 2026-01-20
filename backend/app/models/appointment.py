"""
Appointment model for scheduling consultations between doctors and patients.
"""

import uuid
from datetime import date, datetime
from enum import Enum

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Index, String, Text, Time
from sqlalchemy.orm import relationship

from app.database import Base


class AppointmentStatus(str, Enum):
    """Status of an appointment."""

    PENDING = "PENDING"  # 待确认
    CONFIRMED = "CONFIRMED"  # 已确认
    COMPLETED = "COMPLETED"  # 已完成
    CANCELLED = "CANCELLED"  # 已取消
    NO_SHOW = "NO_SHOW"  # 爽约


class AppointmentType(str, Enum):
    """Type of appointment."""

    INITIAL = "INITIAL"  # 初诊
    FOLLOW_UP = "FOLLOW_UP"  # 复诊
    EMERGENCY = "EMERGENCY"  # 紧急
    CONSULTATION = "CONSULTATION"  # 咨询


class CancelledBy(str, Enum):
    """Who cancelled the appointment."""

    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"
    SYSTEM = "SYSTEM"


class Appointment(Base):
    """
    Appointment model for scheduling doctor-patient consultations.

    Tracks scheduled appointments, their status, and related metadata.
    """

    __tablename__ = "appointments"

    # Primary key (UUID to match existing models)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Foreign keys (matching existing model ID types)
    doctor_id = Column(
        String(36),
        ForeignKey("doctors.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    patient_id = Column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    pre_visit_summary_id = Column(
        String(36),
        ForeignKey("pre_visit_summaries.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Scheduling
    appointment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    # Appointment details
    appointment_type = Column(String(20), default=AppointmentType.FOLLOW_UP.value, nullable=False)
    status = Column(String(20), default=AppointmentStatus.PENDING.value, nullable=False, index=True)

    # Reason and notes
    reason = Column(Text, nullable=True)  # 预约原因
    notes = Column(Text, nullable=True)  # 医生备注
    patient_notes = Column(Text, nullable=True)  # 患者备注

    # Reminders
    reminder_24h_sent = Column(Boolean, default=False)
    reminder_1h_sent = Column(Boolean, default=False)

    # Cancellation info
    cancelled_by = Column(String(20), nullable=True)
    cancel_reason = Column(Text, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)

    # Completion info
    completed_at = Column(DateTime, nullable=True)
    completion_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")
    pre_visit_summary = relationship("PreVisitSummary", back_populates="appointment")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_appointments_doctor_date", "doctor_id", "appointment_date"),
        Index("ix_appointments_patient_date", "patient_id", "appointment_date"),
        Index("ix_appointments_status_date", "status", "appointment_date"),
    )

    def __repr__(self):
        return f"<Appointment {self.id}: {self.doctor_id}->{self.patient_id} on {self.appointment_date}>"

    @property
    def is_past(self) -> bool:
        """Check if the appointment is in the past."""
        now = datetime.utcnow()
        appointment_datetime = datetime.combine(self.appointment_date, self.end_time)
        return appointment_datetime < now

    @property
    def is_cancellable(self) -> bool:
        """Check if the appointment can be cancelled."""
        return self.status in [AppointmentStatus.PENDING.value, AppointmentStatus.CONFIRMED.value] and not self.is_past

    @property
    def duration_minutes(self) -> int:
        """Get appointment duration in minutes."""
        start_dt = datetime.combine(date.today(), self.start_time)
        end_dt = datetime.combine(date.today(), self.end_time)
        return int((end_dt - start_dt).total_seconds() / 60)
