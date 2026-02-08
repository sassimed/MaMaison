from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from enum import Enum


class RequestStatus(str, Enum):
    PENDING = "En attente"
    IN_PROGRESS = "En cours"
    COMPLETED = "Terminé"
    CANCELLED = "Annulé"


class RequestPriority(str, Enum):
    LOW = "Basse"
    NORMAL = "Normale"
    HIGH = "Haute"
    URGENT = "Urgente"


class ServiceRequestCreate(BaseModel):
    """Create a new service request"""
    service_type: str
    title: str
    description: str
    priority: RequestPriority = RequestPriority.NORMAL
    preferred_date: Optional[str] = None
    site_address: Optional[str] = None  # For professionals with multiple sites


class ServiceRequestUpdate(BaseModel):
    """Update a service request (admin)"""
    status: Optional[RequestStatus] = None
    priority: Optional[RequestPriority] = None
    admin_notes: Optional[str] = None
    assigned_to: Optional[str] = None


class ServiceRequest(BaseModel):
    """Service request model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_name: str
    user_email: str
    service_type: str
    title: str
    description: str
    priority: RequestPriority = RequestPriority.NORMAL
    status: RequestStatus = RequestStatus.PENDING
    preferred_date: Optional[str] = None
    site_address: Optional[str] = None
    admin_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
