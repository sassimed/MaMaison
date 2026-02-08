from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
from datetime import datetime, timezone
import uuid
from enum import Enum

class UserRole(str, Enum):
    PARTICULIER = "PARTICULIER"
    PROFESSIONNEL = "PROFESSIONNEL"
    ADMIN = "ADMIN"

class Address(BaseModel):
    """Structured address for users"""
    street: Optional[str] = None
    street2: Optional[str] = None  # Complément d'adresse
    postal_code: Optional[str] = None
    city: Optional[str] = None
    country: str = "Tunisie"

class CompanyInfo(BaseModel):
    """Company information for professional users"""
    company_name: Optional[str] = None
    siret: Optional[str] = None
    address: Optional[str] = None
    technical_contact: Optional[str] = None
    website: Optional[str] = None
    sites: List[dict] = []  # [{name: str, address: str}]

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    address: Optional[str] = None  # Legacy simple address field
    address_details: Optional[Address] = None  # New structured address
    role: UserRole = UserRole.PARTICULIER

class UserCreate(UserBase):
    password: str
    company_info: Optional[CompanyInfo] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    address_details: Optional[Address] = None
    company_info: Optional[CompanyInfo] = None

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    is_active: bool = True
    is_email_verified: bool = False
    company_info: Optional[CompanyInfo] = None
    address_details: Optional[Address] = None
    loyalty_points: int = 0  # Points de fidélité
    total_spent: float = 0  # Total dépensé en DT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None
    role: Optional[str] = None
