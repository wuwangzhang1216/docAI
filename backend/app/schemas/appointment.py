"""
Appointment schemas for request/response validation.
"""

from datetime import date, datetime, time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class AppointmentStatusEnum(str, Enum):
    """Appointment status enum for API."""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"


class AppointmentTypeEnum(str, Enum):
    """Appointment type enum for API."""

    INITIAL = "INITIAL"
    FOLLOW_UP = "FOLLOW_UP"
    EMERGENCY = "EMERGENCY"
    CONSULTATION = "CONSULTATION"


class CancelledByEnum(str, Enum):
    """Who cancelled the appointment."""

    DOCTOR = "DOCTOR"
    PATIENT = "PATIENT"
    SYSTEM = "SYSTEM"


# ============================================
# Create/Update Schemas
# ============================================


class AppointmentCreate(BaseModel):
    """Schema for creating a new appointment."""

    patient_id: str
    appointment_date: date
    start_time: time
    end_time: time
    appointment_type: AppointmentTypeEnum = AppointmentTypeEnum.FOLLOW_UP
    reason: Optional[str] = None
    notes: Optional[str] = None
    pre_visit_summary_id: Optional[str] = None

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        if "start_time" in info.data and v <= info.data["start_time"]:
            raise ValueError("End time must be after start time")
        return v


class AppointmentUpdate(BaseModel):
    """Schema for updating an appointment."""

    appointment_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    appointment_type: Optional[AppointmentTypeEnum] = None
    reason: Optional[str] = None
    notes: Optional[str] = None
    patient_notes: Optional[str] = None
    pre_visit_summary_id: Optional[str] = None


class AppointmentCancel(BaseModel):
    """Schema for cancelling an appointment."""

    cancel_reason: Optional[str] = None


class AppointmentComplete(BaseModel):
    """Schema for completing an appointment."""

    completion_notes: Optional[str] = None


class PatientNotesUpdate(BaseModel):
    """Schema for patient updating their notes."""

    patient_notes: str = Field(..., max_length=2000)


# ============================================
# Response Schemas
# ============================================


class PatientSummary(BaseModel):
    """Brief patient info for appointment response."""

    id: str
    first_name: str
    last_name: str
    full_name: str

    class Config:
        from_attributes = True


class DoctorSummary(BaseModel):
    """Brief doctor info for appointment response."""

    id: str
    first_name: str
    last_name: str
    full_name: str
    specialty: Optional[str] = None

    class Config:
        from_attributes = True


class AppointmentResponse(BaseModel):
    """Full appointment response schema."""

    id: str
    doctor_id: str
    patient_id: str
    pre_visit_summary_id: Optional[str] = None

    appointment_date: date
    start_time: time
    end_time: time
    duration_minutes: int

    appointment_type: str
    status: str

    reason: Optional[str] = None
    notes: Optional[str] = None
    patient_notes: Optional[str] = None

    reminder_24h_sent: bool
    reminder_1h_sent: bool

    cancelled_by: Optional[str] = None
    cancel_reason: Optional[str] = None
    cancelled_at: Optional[datetime] = None

    completed_at: Optional[datetime] = None
    completion_notes: Optional[str] = None

    is_past: bool
    is_cancellable: bool

    created_at: datetime
    updated_at: datetime

    # Nested objects (optional, included when relationships are loaded)
    patient: Optional[PatientSummary] = None
    doctor: Optional[DoctorSummary] = None

    class Config:
        from_attributes = True


class AppointmentListItem(BaseModel):
    """Simplified appointment for list views."""

    id: str
    patient_id: str
    doctor_id: str
    appointment_date: date
    start_time: time
    end_time: time
    appointment_type: str
    status: str
    reason: Optional[str] = None
    is_past: bool
    is_cancellable: bool

    patient: Optional[PatientSummary] = None
    doctor: Optional[DoctorSummary] = None

    class Config:
        from_attributes = True


# ============================================
# Calendar View Schemas
# ============================================


class CalendarDaySlot(BaseModel):
    """A single appointment slot on a calendar day."""

    id: str
    start_time: time
    end_time: time
    status: str
    appointment_type: str
    patient_name: str
    patient_id: str


class CalendarDay(BaseModel):
    """All appointments for a single day."""

    date: date
    appointments: List[CalendarDaySlot]
    total_count: int


class CalendarMonthView(BaseModel):
    """Calendar view for a month."""

    year: int
    month: int
    days: List[CalendarDay]
    total_appointments: int


class CalendarWeekView(BaseModel):
    """Calendar view for a week."""

    start_date: date
    end_date: date
    days: List[CalendarDay]
    total_appointments: int


# ============================================
# Filter/Query Schemas
# ============================================


class AppointmentFilter(BaseModel):
    """Filter options for appointment queries."""

    status: Optional[AppointmentStatusEnum] = None
    appointment_type: Optional[AppointmentTypeEnum] = None
    patient_id: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


# ============================================
# Statistics Schemas
# ============================================


class AppointmentStats(BaseModel):
    """Appointment statistics for dashboard."""

    total: int
    pending: int
    confirmed: int
    completed: int
    cancelled: int
    no_show: int
    today_count: int
    this_week_count: int
    this_month_count: int
