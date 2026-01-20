"""
Data export models for patient data portability.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base


class ExportStatus(str, Enum):
    """Status of an export request."""

    PENDING = "PENDING"  # 等待处理
    PROCESSING = "PROCESSING"  # 正在处理
    COMPLETED = "COMPLETED"  # 已完成
    FAILED = "FAILED"  # 失败
    EXPIRED = "EXPIRED"  # 已过期
    DOWNLOADED = "DOWNLOADED"  # 已下载


class ExportFormat(str, Enum):
    """Export file format."""

    JSON = "JSON"  # JSON格式
    CSV = "CSV"  # CSV格式（ZIP打包）
    PDF_SUMMARY = "PDF_SUMMARY"  # PDF摘要报告


class DataExportRequest(Base):
    """
    Data export request model.

    Tracks patient data export requests and their status.
    Supports JSON, CSV, and PDF summary formats.
    """

    __tablename__ = "data_export_requests"

    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Requester
    patient_id = Column(
        String(36),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Export configuration
    export_format = Column(String(20), default=ExportFormat.JSON.value, nullable=False)

    # Data selection
    include_profile = Column(Boolean, default=True)
    include_checkins = Column(Boolean, default=True)
    include_assessments = Column(Boolean, default=True)
    include_conversations = Column(Boolean, default=True)
    include_messages = Column(Boolean, default=True)

    # Date range (optional)
    date_from = Column(DateTime, nullable=True)
    date_to = Column(DateTime, nullable=True)

    # Processing status
    status = Column(String(20), default=ExportStatus.PENDING.value, nullable=False, index=True)
    progress_percent = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)

    # File information
    s3_key = Column(String(500), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    file_checksum = Column(String(64), nullable=True)  # SHA-256 hash

    # Download security
    download_token = Column(String(64), unique=True, nullable=True, index=True)
    download_expires_at = Column(DateTime, nullable=True)
    download_count = Column(Integer, default=0)
    max_downloads = Column(Integer, default=3)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processing_started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_downloaded_at = Column(DateTime, nullable=True)

    # Request metadata
    request_ip = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Relationships
    patient = relationship("Patient", backref="export_requests")

    def __repr__(self):
        return f"<DataExportRequest {self.id}: {self.patient_id} - {self.status}>"

    @property
    def is_expired(self) -> bool:
        """Check if the download link has expired."""
        if not self.download_expires_at:
            return True
        return datetime.utcnow() > self.download_expires_at

    @property
    def can_download(self) -> bool:
        """Check if the export can be downloaded."""
        return (
            self.status == ExportStatus.COMPLETED.value
            and not self.is_expired
            and self.download_count < self.max_downloads
            and self.s3_key is not None
        )

    @property
    def is_processing(self) -> bool:
        """Check if export is being processed."""
        return self.status in [
            ExportStatus.PENDING.value,
            ExportStatus.PROCESSING.value,
        ]
