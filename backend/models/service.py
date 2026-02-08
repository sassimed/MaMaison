from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str  # URL-friendly name
    description: str
    detailed_description: str
    advantages: List[str]
    use_cases: List[str]
    icon: str  # Icon name or emoji
    image_url: Optional[str] = None
    category: str  # "security", "automation", "control"
    featured: bool = False
