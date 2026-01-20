"""
Messaging models for doctor-patient direct communication.
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class MessageType(str, PyEnum):
    """Message type enumeration."""

    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"


class DoctorPatientThread(Base):
    """
    Conversation thread between a doctor and a patient.
    Each doctor-patient pair has exactly one thread.
    """

    __tablename__ = "doctor_patient_threads"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
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

    # Last message timestamp for sorting threads
    last_message_at = Column(DateTime, nullable=True)

    # Unread message counts for each party
    doctor_unread_count = Column(Integer, default=0)
    patient_unread_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    doctor = relationship("Doctor", backref="message_threads")
    patient = relationship("Patient", backref="message_threads")
    messages = relationship(
        "DirectMessage",
        back_populates="thread",
        order_by="DirectMessage.created_at",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Ensure unique thread per doctor-patient pair
        Index("idx_unique_doctor_patient_thread", "doctor_id", "patient_id", unique=True),
    )

    def __repr__(self):
        return f"<DoctorPatientThread doctor={self.doctor_id} patient={self.patient_id}>"


class DirectMessage(Base):
    """
    A single message in a doctor-patient thread.
    """

    __tablename__ = "direct_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    thread_id = Column(
        String(36),
        ForeignKey("doctor_patient_threads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Sender information
    sender_type = Column(String(10), nullable=False)  # 'DOCTOR' or 'PATIENT'
    sender_id = Column(String(36), nullable=False)  # doctor.id or patient.id

    # Message content
    content = Column(Text, nullable=True)  # Text content (nullable for IMAGE/FILE only messages)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT, nullable=False)

    # Read status
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    thread = relationship("DoctorPatientThread", back_populates="messages")
    attachments = relationship("MessageAttachment", back_populates="message", cascade="all, delete-orphan")

    __table_args__ = (
        # Index for efficient message retrieval within a thread
        Index("idx_thread_messages_time", "thread_id", "created_at"),
    )

    def __repr__(self):
        return f"<DirectMessage {self.id} from {self.sender_type}>"


class MessageAttachment(Base):
    """
    File attachment for a message (image or document).
    """

    __tablename__ = "message_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(
        String(36),
        ForeignKey("direct_messages.id", ondelete="CASCADE"),
        nullable=True,  # Can be null when uploaded before message is sent
        index=True,
    )

    # File metadata
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100), nullable=False)  # MIME type
    file_size = Column(Integer, nullable=False)  # Size in bytes

    # S3 storage keys
    s3_key = Column(String(500), nullable=False)
    thumbnail_s3_key = Column(String(500), nullable=True)  # For images

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    message = relationship("DirectMessage", back_populates="attachments")

    def __repr__(self):
        return f"<MessageAttachment {self.file_name} ({self.file_type})>"
