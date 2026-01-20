"""
Email system models for notifications and password reset.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class EmailStatus(str, PyEnum):
    """Email sending status."""

    PENDING = "PENDING"  # Waiting to be sent
    QUEUED = "QUEUED"  # Added to queue
    SENDING = "SENDING"  # Currently sending
    SENT = "SENT"  # Successfully sent
    FAILED = "FAILED"  # Failed to send
    BOUNCED = "BOUNCED"  # Bounced back


class EmailPriority(str, PyEnum):
    """Email priority levels."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"  # For risk alerts


class EmailType(str, PyEnum):
    """Email types for categorization."""

    PATIENT_INVITATION = "PATIENT_INVITATION"
    PASSWORD_RESET = "PASSWORD_RESET"
    RISK_ALERT = "RISK_ALERT"
    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"
    APPOINTMENT_CANCELLED = "APPOINTMENT_CANCELLED"
    WELCOME = "WELCOME"
    SYSTEM = "SYSTEM"


class EmailTemplate(Base):
    """Email template model for storing reusable email templates."""

    __tablename__ = "email_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, index=True)
    email_type = Column(String(50), nullable=False, index=True)
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=False)
    body_text = Column(Text, nullable=True)  # Plain text fallback
    language = Column(String(10), default="zh", index=True)  # zh, en, etc.
    variables = Column(JSON, nullable=True)  # Template variable descriptions
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sent_emails = relationship("EmailLog", back_populates="template")

    def __repr__(self):
        return f"<EmailTemplate {self.name} ({self.email_type})>"


class EmailLog(Base):
    """Email sending log for tracking all sent emails."""

    __tablename__ = "email_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    template_id = Column(String(36), ForeignKey("email_templates.id"), nullable=True)
    email_type = Column(String(50), nullable=False, index=True)

    # Recipient information
    recipient_email = Column(String(255), nullable=False, index=True)
    recipient_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    recipient_name = Column(String(100), nullable=True)

    # Sender information
    sender_email = Column(String(255), nullable=True)
    sender_name = Column(String(100), nullable=True)

    # Email content
    subject = Column(String(255), nullable=False)
    body_html = Column(Text, nullable=True)
    body_text = Column(Text, nullable=True)

    # Sending status
    status = Column(String(20), default=EmailStatus.PENDING.value, index=True)
    priority = Column(String(20), default=EmailPriority.NORMAL.value)

    # Retry information
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    last_error = Column(Text, nullable=True)

    # Related entity (optional reference)
    related_entity_type = Column(String(50), nullable=True)  # risk_event, appointment, etc.
    related_entity_id = Column(String(36), nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    queued_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Extra data
    extra_data = Column(JSON, nullable=True)  # Additional information

    # Relationships
    template = relationship("EmailTemplate", back_populates="sent_emails")
    recipient = relationship("User", foreign_keys=[recipient_user_id])

    __table_args__ = (
        Index("ix_email_logs_status_priority", "status", "priority"),
        Index("ix_email_logs_created_status", "created_at", "status"),
    )

    def __repr__(self):
        return f"<EmailLog {self.id} to={self.recipient_email} status={self.status}>"


class PasswordResetToken(Base):
    """Password reset token for secure password recovery."""

    __tablename__ = "password_reset_tokens"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token = Column(String(64), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Security audit information
    request_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationship
    user = relationship("User")

    def __repr__(self):
        return f"<PasswordResetToken user_id={self.user_id} used={self.used_at is not None}>"

    @property
    def is_expired(self) -> bool:
        """Check if the token has expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_used(self) -> bool:
        """Check if the token has been used."""
        return self.used_at is not None

    @property
    def is_valid(self) -> bool:
        """Check if the token is still valid (not expired and not used)."""
        return not self.is_expired and not self.is_used
