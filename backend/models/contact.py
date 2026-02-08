from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid
from datetime import datetime, timezone

class ContactCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str

class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    subject: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
