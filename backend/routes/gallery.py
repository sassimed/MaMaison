from fastapi import APIRouter, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.gallery import GalleryItem
from utils.dependencies import get_db
from typing import List, Optional

router = APIRouter(prefix="/gallery", tags=["Gallery"])

@router.get("", response_model=List[GalleryItem])
async def get_gallery_items(
    category: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all gallery items with optional category filter"""
    query = {}
    if category:
        query["category"] = category
    
    items = await db.gallery.find(query, {"_id": 0}).to_list(100)
    
    # Convert datetime to ISO string
    for item in items:
        if isinstance(item.get('created_at'), str):
            from datetime import datetime
            item['created_at'] = datetime.fromisoformat(item['created_at'])
    
    return items
