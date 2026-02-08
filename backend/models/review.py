from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, timezone
import uuid


class ReviewBase(BaseModel):
    """Base model for reviews"""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewCreate(ReviewBase):
    """Model for creating a review"""
    target_type: Literal["product", "professional"] = Field(..., description="Type of target being reviewed")
    target_id: str = Field(..., description="ID of the product or professional")


class ReviewResponse(ReviewBase):
    """Model for review response"""
    id: str
    target_type: str
    target_id: str
    user_id: str
    user_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ReviewStats(BaseModel):
    """Statistics for reviews"""
    average_rating: float = 0.0
    total_reviews: int = 0
    rating_distribution: dict = Field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0})


class ProfessionalStats(BaseModel):
    """Statistics for a professional"""
    average_rating: float = 0.0
    total_reviews: int = 0
    intervention_count: int = 0  # Number of completed annonces
    rating_distribution: dict = Field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0})


class ProductStats(BaseModel):
    """Statistics for a product"""
    average_rating: float = 0.0
    total_reviews: int = 0
    sales_count: int = 0  # Number of times sold
    rating_distribution: dict = Field(default_factory=lambda: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0})


def create_review_dict(
    target_type: str,
    target_id: str,
    user_id: str,
    user_name: str,
    rating: int,
    comment: Optional[str] = None
) -> dict:
    """Create a review dictionary for MongoDB"""
    return {
        "id": str(uuid.uuid4()),
        "target_type": target_type,
        "target_id": target_id,
        "user_id": user_id,
        "user_name": user_name,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.now(timezone.utc)
    }
