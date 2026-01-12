"""Schemas for patient-doctor connection requests."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field

from app.models.connection_request import ConnectionStatus


class ConnectionRequestCreate(BaseModel):
    """Schema for creating a connection request (doctor sends to patient)."""
    patient_email: EmailStr = Field(..., description="Email of the patient to connect with")
    message: Optional[str] = Field(None, max_length=500, description="Optional message to the patient")


class ConnectionRequestResponse(BaseModel):
    """Schema for connection request response (doctor's view)."""
    id: str
    doctor_id: str
    patient_id: str
    patient_name: str
    patient_email: str
    status: ConnectionStatus
    message: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    responded_at: Optional[datetime]

    class Config:
        from_attributes = True


class PatientConnectionRequestView(BaseModel):
    """Schema for connection request (patient's view)."""
    id: str
    doctor_id: str
    doctor_name: str
    doctor_specialty: Optional[str]
    message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DoctorPublicInfo(BaseModel):
    """Public information about a doctor (visible to patients)."""
    id: str
    full_name: str
    specialty: Optional[str]
    # Note: email NOT included for privacy

    class Config:
        from_attributes = True


class ConnectionRequestStatusResponse(BaseModel):
    """Response for connection request status changes."""
    status: str
    request_id: str
    message: Optional[str] = None
