from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.conversation import ConversationType

ALLOWED_IMAGE_MEDIA_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
MAX_IMAGE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB per image (base64 encoded ≈ 6.67 MB)
MAX_IMAGES_PER_MESSAGE = 4


class ChatImage(BaseModel):
    """A base64-encoded image attached to a chat message."""

    media_type: str = Field(..., description="MIME type, e.g. image/jpeg")
    data: str = Field(..., description="Base64-encoded image data")

    @field_validator("media_type")
    @classmethod
    def validate_media_type(cls, v: str) -> str:
        if v not in ALLOWED_IMAGE_MEDIA_TYPES:
            raise ValueError(f"Unsupported image type: {v}. Allowed: {', '.join(ALLOWED_IMAGE_MEDIA_TYPES)}")
        return v

    @field_validator("data")
    @classmethod
    def validate_data_size(cls, v: str) -> str:
        # base64 string length ≈ 4/3 * raw bytes
        estimated_bytes = len(v) * 3 / 4
        if estimated_bytes > MAX_IMAGE_SIZE_BYTES:
            raise ValueError(f"Image too large. Maximum size is {MAX_IMAGE_SIZE_BYTES // (1024 * 1024)} MB")
        return v


class MessageItem(BaseModel):
    """Schema for a single message in conversation."""

    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    risk_level: Optional[str] = None


class ChatRequest(BaseModel):
    """Schema for chat request."""

    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    images: Optional[List[ChatImage]] = Field(None, description="Attached images (max 4)")

    @field_validator("images")
    @classmethod
    def validate_images_count(cls, v: Optional[List[ChatImage]]) -> Optional[List[ChatImage]]:
        if v and len(v) > MAX_IMAGES_PER_MESSAGE:
            raise ValueError(f"Maximum {MAX_IMAGES_PER_MESSAGE} images per message")
        return v


class ChatResponse(BaseModel):
    """Schema for chat response."""

    reply: str
    conversation_id: str
    risk_alert: bool = False


class ConversationResponse(BaseModel):
    """Schema for conversation response."""

    id: str
    patient_id: str
    conv_type: ConversationType
    messages: List[MessageItem]
    summary: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConversationListItem(BaseModel):
    """Schema for conversation list item."""

    id: str
    conv_type: ConversationType
    message_count: int
    last_message_preview: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
