import uuid
import json
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Enum, DateTime, ForeignKey, SmallInteger, Text
from sqlalchemy.orm import relationship

from app.database import Base


class AssessmentType(str, PyEnum):
    """Assessment type enumeration.

    Includes standard scales and trauma-specific scales for political trauma survivors.
    """
    PHQ9 = "PHQ9"      # Patient Health Questionnaire-9 (Depression)
    GAD7 = "GAD7"      # Generalized Anxiety Disorder-7 (Anxiety)
    PSS = "PSS"        # Perceived Stress Scale
    ISI = "ISI"        # Insomnia Severity Index
    PCL5 = "PCL5"      # PTSD Checklist for DSM-5 (Trauma-specific)


class SeverityLevel(str, PyEnum):
    """Severity level enumeration."""
    MINIMAL = "MINIMAL"
    MILD = "MILD"
    MODERATE = "MODERATE"
    MODERATELY_SEVERE = "MODERATELY_SEVERE"
    SEVERE = "SEVERE"


class Assessment(Base):
    """Assessment model for storing questionnaire results."""
    __tablename__ = "assessments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_type = Column(Enum(AssessmentType), nullable=False)
    responses_json = Column(Text, nullable=False)  # JSON string for SQLite
    total_score = Column(SmallInteger, nullable=False)
    severity = Column(Enum(SeverityLevel), nullable=True)
    risk_flags_json = Column(Text, nullable=True)  # JSON string for SQLite
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    patient = relationship("Patient", back_populates="assessments")

    @property
    def responses(self):
        return json.loads(self.responses_json) if self.responses_json else {}
    
    @responses.setter
    def responses(self, value):
        self.responses_json = json.dumps(value) if value else None

    @property
    def risk_flags(self):
        return json.loads(self.risk_flags_json) if self.risk_flags_json else None
    
    @risk_flags.setter
    def risk_flags(self, value):
        self.risk_flags_json = json.dumps(value) if value else None

    def __repr__(self):
        return f"<Assessment {self.assessment_type} score={self.total_score}>"
