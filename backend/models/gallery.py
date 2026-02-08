from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone

class GalleryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    image_url: str
    category: str  # "éclairage", "volets", "sécurité", "vidéosurveillance", etc.
    tags: List[str] = []
    location: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
