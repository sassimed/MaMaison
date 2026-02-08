from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

class AppointmentStatus(str, Enum):
    PENDING = "En attente"
    CONFIRMED = "Confirmé"
    COMPLETED = "Terminé"
    CANCELLED = "Annulé"

class AppointmentCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    service_type: str
    preferred_date: str  # ISO format date
    preferred_time: str
    message: Optional[str] = None

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    full_name: str
    email: EmailStr
    phone: str
    service_type: str
    preferred_date: str
    preferred_time: str
    message: Optional[str] = None
    status: AppointmentStatus = AppointmentStatus.PENDING
    meet_link: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user_id: Optional[str] = None  # If user is logged in
