from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import User, UserUpdate, CompanyInfo, Address
from utils.dependencies import get_db, get_current_user
from datetime import datetime, timezone

router = APIRouter(prefix="/user", tags=["User Profile"])


@router.get("/profile", response_model=User)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user


@router.put("/profile", response_model=User)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update current user's profile"""
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if not update_dict:
        return current_user
    
    # Handle company_info for professionals
    if update_data.company_info:
        update_dict['company_info'] = update_data.company_info.model_dump()
    
    # Handle address_details
    if update_data.address_details:
        update_dict['address_details'] = update_data.address_details.model_dump()
    
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": update_dict}
    )
    
    # Fetch updated user
    user_doc = await db.users.find_one({"id": current_user.id}, {"_id": 0})
    
    # Convert datetime strings
    if isinstance(user_doc.get('created_at'), str):
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    if isinstance(user_doc.get('updated_at'), str):
        user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
    
    return User(**user_doc)


@router.put("/company-info")
async def update_company_info(
    company_info: CompanyInfo,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update company info (for professionals)"""
    if current_user.role != "PROFESSIONNEL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les professionnels peuvent gérer les infos entreprise"
        )
    
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$set": {
                "company_info": company_info.model_dump(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    return {"message": "Informations entreprise mises à jour"}


@router.post("/company-info/sites")
async def add_site(
    site: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add a site (for professionals with multi-site management)"""
    if current_user.role != "PROFESSIONNEL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les professionnels peuvent gérer les sites"
        )
    
    # Validate site data
    if not site.get('name') or not site.get('address'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le nom et l'adresse du site sont requis"
        )
    
    site['id'] = str(datetime.now(timezone.utc).timestamp()).replace('.', '')
    
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$push": {"company_info.sites": site},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Site ajouté", "site": site}


@router.delete("/company-info/sites/{site_id}")
async def remove_site(
    site_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Remove a site"""
    if current_user.role != "PROFESSIONNEL":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seuls les professionnels peuvent gérer les sites"
        )
    
    await db.users.update_one(
        {"id": current_user.id},
        {
            "$pull": {"company_info.sites": {"id": site_id}},
            "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
        }
    )
    
    return {"message": "Site supprimé"}
