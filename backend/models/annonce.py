from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid


class AnnonceStatus(str, Enum):
    EN_ATTENTE = "EN_ATTENTE"  # Waiting for admin validation
    PUBLIEE = "PUBLIEE"  # Published and visible to professionals
    REFUSEE = "REFUSEE"  # Rejected by admin
    CLOTUREE = "CLOTUREE"  # Closed by client
    ATTRIBUEE = "ATTRIBUEE"  # Assigned to a professional


class AnnonceCategory(str, Enum):
    CAMERA = "Installation Caméra"
    ALARME = "Système d'Alarme"
    DOMOTIQUE = "Domotique"
    ECLAIRAGE = "Éclairage Connecté"
    SERRURE = "Serrure Connectée"
    RESEAU = "Réseau WiFi/Câblage"
    AUTRE = "Autre"


class AnnonceResponse(BaseModel):
    """Response from a professional to an announcement"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    professional_id: str
    professional_name: str
    professional_email: str
    professional_phone: Optional[str] = None
    message: str
    price_estimate: Optional[float] = None  # Estimated price in DT
    availability: Optional[str] = None  # When they can do the work
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Annonce(BaseModel):
    """Announcement model for client service requests"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Client info
    client_id: str
    client_name: str
    client_email: str
    client_phone: Optional[str] = None
    
    # Announcement details
    title: str
    description: str
    category: str = AnnonceCategory.AUTRE.value
    
    # Location
    city: str
    address: Optional[str] = None
    
    # Status
    status: str = AnnonceStatus.EN_ATTENTE.value
    admin_notes: Optional[str] = None  # Notes from admin (rejection reason, etc.)
    
    # Responses from professionals
    responses: List[AnnonceResponse] = []
    selected_response_id: Optional[str] = None  # ID of the selected professional
    
    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None  # When admin approved
    closed_at: Optional[datetime] = None


class AnnonceCreate(BaseModel):
    """Schema for creating an announcement"""
    title: str
    description: str
    category: str = AnnonceCategory.AUTRE.value
    city: str
    address: Optional[str] = None


class AnnonceResponseCreate(BaseModel):
    """Schema for a professional responding to an announcement"""
    message: str
    price_estimate: Optional[float] = None
    availability: Optional[str] = None
