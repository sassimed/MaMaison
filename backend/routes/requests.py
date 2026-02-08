from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.service_request import ServiceRequest, ServiceRequestCreate, ServiceRequestUpdate, RequestStatus
from models.user import User
from utils.dependencies import get_db, get_current_user
from datetime import datetime, timezone
from typing import List, Optional

router = APIRouter(prefix="/requests", tags=["Service Requests"])


@router.post("", response_model=ServiceRequest, status_code=status.HTTP_201_CREATED)
async def create_request(
    request_data: ServiceRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new service request"""
    request = ServiceRequest(
        user_id=current_user.id,
        user_name=current_user.full_name,
        user_email=current_user.email,
        **request_data.model_dump()
    )
    
    # Convert to dict and serialize datetime
    doc = request.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    await db.service_requests.insert_one(doc)
    
    return request


@router.get("", response_model=List[ServiceRequest])
async def get_my_requests(
    status_filter: Optional[RequestStatus] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get current user's service requests"""
    query = {"user_id": current_user.id}
    if status_filter:
        query["status"] = status_filter.value
    
    requests = await db.service_requests.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Convert datetime strings
    for req in requests:
        if isinstance(req.get('created_at'), str):
            req['created_at'] = datetime.fromisoformat(req['created_at'])
        if isinstance(req.get('updated_at'), str):
            req['updated_at'] = datetime.fromisoformat(req['updated_at'])
    
    return requests


@router.get("/{request_id}", response_model=ServiceRequest)
async def get_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a specific service request"""
    request = await db.service_requests.find_one(
        {"id": request_id, "user_id": current_user.id},
        {"_id": 0}
    )
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée"
        )
    
    # Convert datetime strings
    if isinstance(request.get('created_at'), str):
        request['created_at'] = datetime.fromisoformat(request['created_at'])
    if isinstance(request.get('updated_at'), str):
        request['updated_at'] = datetime.fromisoformat(request['updated_at'])
    
    return ServiceRequest(**request)


@router.delete("/{request_id}")
async def cancel_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Cancel a service request (only if pending)"""
    request = await db.service_requests.find_one(
        {"id": request_id, "user_id": current_user.id},
        {"_id": 0}
    )
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Demande non trouvée"
        )
    
    if request['status'] != RequestStatus.PENDING.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Seules les demandes en attente peuvent être annulées"
        )
    
    await db.service_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": RequestStatus.CANCELLED.value,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Demande annulée"}
