"""
Data export schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from enum import Enum

from pydantic import BaseModel, Field


class ExportFormatEnum(str, Enum):
    """Export format options."""
    JSON = "JSON"
    CSV = "CSV"
    PDF_SUMMARY = "PDF_SUMMARY"


class ExportStatusEnum(str, Enum):
    """Export status values."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    EXPIRED = "EXPIRED"
    DOWNLOADED = "DOWNLOADED"


# ============================================
# Request Schemas
# ============================================

class ExportRequestCreate(BaseModel):
    """Schema for creating a data export request."""
    export_format: ExportFormatEnum = ExportFormatEnum.JSON

    # Data selection (all default to True)
    include_profile: bool = True
    include_checkins: bool = True
    include_assessments: bool = True
    include_conversations: bool = True
    include_messages: bool = True

    # Optional date range
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# ============================================
# Response Schemas
# ============================================

class ExportRequestResponse(BaseModel):
    """Full export request response."""
    id: str
    patient_id: str
    export_format: str
    status: str

    include_profile: bool
    include_checkins: bool
    include_assessments: bool
    include_conversations: bool
    include_messages: bool

    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None

    progress_percent: int
    error_message: Optional[str] = None

    file_size_bytes: Optional[int] = None
    download_count: int
    max_downloads: int
    download_token: Optional[str] = None

    can_download: bool
    is_expired: bool
    is_processing: bool

    created_at: datetime
    processing_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    download_expires_at: Optional[datetime] = None
    last_downloaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExportRequestListItem(BaseModel):
    """Simplified export request for list views."""
    id: str
    export_format: str
    status: str
    progress_percent: int
    file_size_bytes: Optional[int] = None
    download_token: Optional[str] = None
    can_download: bool
    is_expired: bool
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ExportDownloadResponse(BaseModel):
    """Response with download URL."""
    download_url: str
    expires_at: datetime
    file_name: str
    file_size_bytes: int
    remaining_downloads: int


class ExportProgressResponse(BaseModel):
    """Progress update during export processing."""
    id: str
    status: str
    progress_percent: int
    error_message: Optional[str] = None
