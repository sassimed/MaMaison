from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid


class CategoryCreate(BaseModel):
    """Create a new category"""
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None


class CategoryUpdate(BaseModel):
    """Update a category"""
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None


class Category(BaseModel):
    """Category model"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    image_url: Optional[str] = None
    product_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
