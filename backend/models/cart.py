from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, default=1)

class Cart(BaseModel):
    user_id: str
    items: List[CartItem] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CartItemAdd(BaseModel):
    product_id: str
    quantity: int = Field(ge=1, default=1)

class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)

class Favorites(BaseModel):
    user_id: str
    product_ids: List[str] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class FavoriteAdd(BaseModel):
    product_id: str

class PurchaseRequestItem(BaseModel):
    product_id: str
    product_name: str
    product_price: Optional[float] = None
    quantity: int

class PurchaseRequest(BaseModel):
    id: Optional[str] = None
    user_id: str
    user_name: str
    user_email: str
    user_phone: Optional[str] = None
    items: List[PurchaseRequestItem]
    total_estimated: Optional[float] = None
    status: str = "EN_ATTENTE"  # EN_ATTENTE, EN_COURS, VALIDEE, REFUSEE
    admin_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PurchaseRequestStatusUpdate(BaseModel):
    status: str
    admin_notes: Optional[str] = None
