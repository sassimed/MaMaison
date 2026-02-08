from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from enum import Enum


class MessageType(str, Enum):
    USER_TO_ADMIN = "user_to_admin"
    ADMIN_TO_USER = "admin_to_user"


class MessageCreate(BaseModel):
    """Create a new message"""
    subject: str
    content: str
    related_request_id: Optional[str] = None  # Link to a service request


class MessageReply(BaseModel):
    """Reply to a message"""
    content: str


class Message(BaseModel):
    """Message model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    sender_name: str
    sender_role: str
    recipient_id: Optional[str] = None  # None = to admin team
    subject: str
    content: str
    message_type: MessageType
    related_request_id: Optional[str] = None
    is_read: bool = False
    parent_id: Optional[str] = None  # For replies
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Conversation(BaseModel):
    """Conversation thread"""
    id: str
    subject: str
    user_id: str
    user_name: str
    last_message_at: datetime
    unread_count: int = 0
    is_closed: bool = False
