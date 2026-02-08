from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.dependencies import get_db
from typing import List

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("")
async def get_categories(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all categories (public)"""
    categories = await db.categories.find({}, {"_id": 0}).to_list(100)
    
    # Get product count for each category
    for cat in categories:
        cat['product_count'] = await db.products.count_documents({"category": cat['name']})
    
    return categories
