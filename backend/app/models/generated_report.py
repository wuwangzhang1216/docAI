"""
Generated report model for tracking PDF reports.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ReportType(str, PyEnum):
    """Report type enumeration."""

    PRE_VISIT_SUMMARY = "PRE_VISIT_SUMMARY"
    PROGRESS_REPORT = "PROGRESS_REPORT"  # Future use


class GeneratedReport(Base):
    """Generated report model for storing report metadata."""

    __tablename__ = "generated_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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
    report_type = Column(Enum(ReportType), nullable=False)
    s3_key = Column(String(255), nullable=False)
    generated_by_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    metadata_json = Column(Text, nullable=True)  # Store generation options
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    patient = relationship("Patient", backref="generated_reports")
    pre_visit_summary = relationship("PreVisitSummary", backref="generated_reports")
    generated_by = relationship("User", backref="generated_reports")

    def __repr__(self):
        return f"<GeneratedReport {self.report_type} for patient={self.patient_id}>"
