from datetime import date, datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


from app.models.assessment import AssessmentType, SeverityLevel
from app.models.risk_event import RiskLevel, RiskType


class CheckinCreate(BaseModel):
    """Schema for creating a daily check-in."""
    mood_score: int = Field(..., ge=0, le=10)
    sleep_hours: float = Field(..., ge=0, le=24)
    sleep_quality: int = Field(..., ge=1, le=5)
    medication_taken: bool
    notes: Optional[str] = Field(None, max_length=1000)


class CheckinResponse(BaseModel):
    """Schema for check-in response."""
    id: str
    patient_id: str
    checkin_date: date
    mood_score: Optional[int]
    sleep_hours: Optional[float]
    sleep_quality: Optional[int]
    medication_taken: Optional[bool]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AssessmentCreate(BaseModel):
    """Schema for creating an assessment."""
    assessment_type: AssessmentType
    responses: Dict[str, int]  # {"q1": 2, "q2": 1, ...}


class AssessmentResponse(BaseModel):
    """Schema for assessment response."""
    id: str
    patient_id: str
    assessment_type: AssessmentType
    total_score: int
    severity: Optional[SeverityLevel]
    risk_flags: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


class PatientOverview(BaseModel):
    """Schema for patient overview in doctor's view."""
    patient_id: str
    patient_name: str
    recent_mood_avg: Optional[float]
    latest_phq9: Optional[int]
    latest_gad7: Optional[int]
    unreviewed_risks: int


class RiskEventResponse(BaseModel):
    """Schema for risk event response."""
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    conversation_id: Optional[str]
    risk_level: RiskLevel
    risk_type: Optional[RiskType]
    trigger_text: Optional[str]
    ai_confidence: Optional[float]
    doctor_reviewed: bool
    doctor_notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PatientTimelineItem(BaseModel):
    """Schema for patient timeline item."""
    type: str  # "checkin", "assessment", "risk_event"
    date: datetime
    data: Dict[str, Any]


class PatientTimeline(BaseModel):
    """Schema for patient timeline."""
    patient_id: str
    patient_name: str
    items: List[PatientTimelineItem]


# ========== Doctor AI Chat Schemas ==========

class DoctorAIChatRequest(BaseModel):
    """Schema for doctor AI chat request."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None  # Continue existing conversation


class DoctorAIChatResponse(BaseModel):
    """Schema for doctor AI chat response."""
    response: str
    conversation_id: str
    patient_name: str


class DoctorConversationMessage(BaseModel):
    """Schema for a single message in doctor conversation."""
    role: str  # "user" or "assistant"
    content: str


class DoctorConversationResponse(BaseModel):
    """Schema for doctor conversation response."""
    id: str
    doctor_id: str
    patient_id: str
    patient_name: Optional[str] = None
    messages: List[DoctorConversationMessage]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DoctorConversationListItem(BaseModel):
    """Schema for doctor conversation list item."""
    id: str
    patient_id: str
    patient_name: Optional[str] = None
    message_count: int
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime
