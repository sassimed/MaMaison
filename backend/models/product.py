from pydantic import BaseModel, Field
from typing import List, Optional
import uuid

class Product(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    brand: Optional[str] = None  # Product brand (Tuya, Leelen, Sonoff, etc.)
    technology: str = "WiFi"  # WiFi, Zigbee, WiFi/Zigbee, Z-Wave, Bluetooth
    category: str  # Dynamic category from categories collection
    image_url: Optional[str] = None
    gallery_images: List[str] = []  # Additional product images
    youtube_url: Optional[str] = None  # YouTube video URL
    manual_url: Optional[str] = None  # User manual PDF download
    datasheet_url: Optional[str] = None  # Technical datasheet PDF download
    compatibility: List[str] = []  # Compatible systems
    usage: Optional[str] = None  # Usage description
    price: Optional[float] = None
    featured: bool = False
    stock_quantity: int = 0  # Stock quantity for inventory management
