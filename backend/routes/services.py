from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.service import Service
from utils.dependencies import get_db
from typing import List

router = APIRouter(prefix="/services", tags=["Services"])

@router.get("", response_model=List[Service])
async def get_services(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get all services"""
    services = await db.services.find({}, {"_id": 0}).to_list(100)
    return services

@router.get("/{slug}", response_model=Service)
async def get_service_by_slug(slug: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Get a specific service by slug"""
    service = await db.services.find_one({"slug": slug}, {"_id": 0})
    if not service:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Service not found")
    return service
