from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.appointment import Appointment, AppointmentCreate, AppointmentStatus
from utils.dependencies import get_db, get_current_user
from models.user import User
from typing import List, Optional

router = APIRouter(prefix="/appointments", tags=["Appointments"])

@router.post("", response_model=Appointment, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    appointment_data: AppointmentCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new appointment (public)"""
    appointment = Appointment(**appointment_data.model_dump())
    
    # Convert to dict and serialize datetime
    doc = appointment.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.appointments.insert_one(doc)
    return appointment

@router.get("/my-appointments", response_model=List[Appointment])
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get current user's appointments"""
    appointments = await db.appointments.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).to_list(100)
    
    # Convert datetime strings
    for apt in appointments:
        if isinstance(apt.get('created_at'), str):
            from datetime import datetime
            apt['created_at'] = datetime.fromisoformat(apt['created_at'])
    
    return appointments
