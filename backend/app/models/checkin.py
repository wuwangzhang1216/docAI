import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Date, DateTime, ForeignKey, SmallInteger, Float, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class DailyCheckin(Base):
    """Daily check-in model for tracking patient mood and health."""
    __tablename__ = "daily_checkins"
    __table_args__ = (
        UniqueConstraint("patient_id", "checkin_date", name="uq_patient_checkin_date"),
    )

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    checkin_date = Column(Date, nullable=False, index=True)
    mood_score = Column(SmallInteger, nullable=True)  # 0-10
    sleep_hours = Column(Float, nullable=True)
    sleep_quality = Column(SmallInteger, nullable=True)  # 1-5
    medication_taken = Column(Boolean, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="checkins")

    def __repr__(self):
        return f"<DailyCheckin {self.checkin_date} mood={self.mood_score}>"
