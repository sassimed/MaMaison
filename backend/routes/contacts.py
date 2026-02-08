from fastapi import APIRouter, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.contact import Contact, ContactCreate
from utils.dependencies import get_db

router = APIRouter(prefix="/contacts", tags=["Contacts"])

@router.post("", response_model=Contact, status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: ContactCreate,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Submit a contact form (public)"""
    contact = Contact(**contact_data.model_dump())
    
    # Convert to dict and serialize datetime
    doc = contact.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.contacts.insert_one(doc)
    return contact
