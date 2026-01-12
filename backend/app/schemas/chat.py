from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


from app.models.conversation import ConversationType
from app.models.risk_event import RiskLevel


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
