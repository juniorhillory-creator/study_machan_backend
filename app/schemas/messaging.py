# app/schemas/messaging.py
# Pydantic schemas for chat conversations, messages, and notification alerts.

from typing import Optional
from pydantic import BaseModel, Field


class MessageSendRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)


class MessageItem(BaseModel):
    id: str
    conversation_id: str
    sender_id: str
    content: str
    is_read: bool = False
    created_at: Optional[str] = None


class ConversationSummary(BaseModel):
    id: str
    student_id: str
    tutor_id: str
    participant_name: str
    participant_avatar: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: Optional[str] = None
    unread_count: int = 0


class NotificationItem(BaseModel):
    id: str
    title: str
    description: str
    category: str = "system"
    is_read: bool = False
    created_at: Optional[str] = None
