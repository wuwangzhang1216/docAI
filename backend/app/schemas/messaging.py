"""
Schemas for doctor-patient messaging.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.messaging import MessageType


# ==================== Attachment Schemas ====================

class AttachmentResponse(BaseModel):
    """Schema for attachment response."""
    id: str
    file_name: str
    file_type: str
    file_size: int
    url: str  # Presigned URL
    thumbnail_url: Optional[str] = None

    class Config:
        from_attributes = True


class AttachmentUploadResponse(BaseModel):
    """Schema for attachment upload response."""
    id: str
    file_name: str
    file_type: str
    file_size: int
    s3_key: str
    thumbnail_s3_key: Optional[str] = None


# ==================== Message Schemas ====================

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: Optional[str] = Field(None, max_length=5000)
    message_type: MessageType = MessageType.TEXT
    attachment_ids: Optional[List[str]] = None


class MessageResponse(BaseModel):
    """Schema for a single message."""
    id: str
    thread_id: str
    sender_type: str  # 'DOCTOR' or 'PATIENT'
    sender_id: str
    sender_name: str
    content: Optional[str]
    message_type: MessageType
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    attachments: List[AttachmentResponse] = []

    class Config:
        from_attributes = True


# ==================== Thread Schemas ====================

class ThreadSummary(BaseModel):
    """Schema for thread summary in list view."""
    id: str
    other_party_id: str
    other_party_name: str
    other_party_type: str  # 'DOCTOR' or 'PATIENT'
    last_message_preview: Optional[str]
    last_message_at: Optional[datetime]
    last_message_type: Optional[MessageType] = None
    unread_count: int
    can_send_message: bool  # Whether connection is still active
    created_at: datetime

    class Config:
        from_attributes = True


class ThreadDetail(BaseModel):
    """Schema for thread detail with messages."""
    id: str
    other_party_id: str
    other_party_name: str
    other_party_type: str
    can_send_message: bool
    messages: List[MessageResponse]
    has_more: bool = False  # For pagination
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Unread Count Schemas ====================

class ThreadUnreadCount(BaseModel):
    """Schema for unread count per thread."""
    thread_id: str
    unread_count: int


class UnreadCountResponse(BaseModel):
    """Schema for total unread count response."""
    total_unread: int
    threads: List[ThreadUnreadCount]


# ==================== WebSocket Message Schemas ====================

class WSMessagePayload(BaseModel):
    """Base payload for WebSocket messages."""
    pass


class WSNewMessagePayload(WSMessagePayload):
    """Payload for new message notification."""
    message: MessageResponse


class WSMessageReadPayload(WSMessagePayload):
    """Payload for message read notification."""
    thread_id: str
    reader_type: str  # 'DOCTOR' or 'PATIENT'
    read_at: datetime


class WSUnreadUpdatePayload(WSMessagePayload):
    """Payload for unread count update."""
    total_unread: int


class WSMessage(BaseModel):
    """WebSocket message format."""
    type: str  # 'new_message', 'message_read', 'unread_update', 'pong'
    payload: Optional[dict] = None


# ==================== Request Schemas ====================

class MarkReadRequest(BaseModel):
    """Schema for marking messages as read."""
    pass  # No body needed, just the action


class StartThreadRequest(BaseModel):
    """Schema for starting a thread with a patient."""
    pass  # patient_id comes from path
