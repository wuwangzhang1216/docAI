"""
Schemas for report generation.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.generated_report import ReportType


class ReportGenerateRequest(BaseModel):
    """Schema for report generation request."""
    include_risk_events: bool = Field(default=True, description="Include risk alerts in report")
    include_checkin_trend: bool = Field(default=True, description="Include recent check-in trends")
    days_for_trend: int = Field(default=7, ge=1, le=30, description="Number of days for trend analysis")


class ReportResponse(BaseModel):
    """Schema for report response."""
    report_id: str
    patient_id: str
    report_type: ReportType
    pdf_url: str
    expires_at: datetime
    generated_at: datetime

    class Config:
        from_attributes = True


class ReportListItem(BaseModel):
    """Schema for report list item."""
    report_id: str
    patient_id: str
    patient_name: Optional[str] = None
    report_type: ReportType
    generated_at: datetime

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for report list response."""
    reports: List[ReportListItem]
    total: int
