from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import asyncio
import uuid

from models.user import User
from models.annonce import Annonce, AnnonceCreate, AnnonceResponse, AnnonceResponseCreate, AnnonceStatus
from utils.dependencies import get_db, get_current_user
from services.moderation_service import moderate_annonce_with_ai, get_rejection_message

router = APIRouter(prefix="/annonces", tags=["Annonces"])

# Tunisian cities grouped by region for proximity matching
TUNISIAN_REGIONS = {
    "Grand Tunis": ["Tunis", "Ariana", "Ben Arous", "Manouba", "La Manouba"],
    "Nord-Est": ["Nabeul", "Zaghouan", "Bizerte"],
    "Nord-Ouest": ["Béja", "Jendouba", "Le Kef", "Siliana"],
    "Centre-Est": ["Sousse", "Monastir", "Mahdia", "Sfax"],
    "Centre-Ouest": ["Kairouan", "Kasserine", "Sidi Bouzid"],
    "Sud-Est": ["Gabès", "Médenine", "Tataouine"],
    "Sud-Ouest": ["Gafsa", "Tozeur", "Kébili"]
}

def get_nearby_cities(city: str) -> List[str]:
    """Get cities in the same region as the given city"""
    city_lower = city.lower()
    for region, cities in TUNISIAN_REGIONS.items():
        if any(c.lower() == city_lower or city_lower in c.lower() for c in cities):
            return cities
    return [city]


class NotifyProfessionalsRequest(BaseModel):
    professional_ids: List[str]


# ==================== CLIENT ROUTES ====================

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_annonce(
    annonce_data: AnnonceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new announcement (clients only)"""
    if current_user.role == "ADMIN":
        raise HTTPException(status_code=400, detail="Les admins ne peuvent pas créer d'annonces")
    
    # Auto-moderate the annonce (rules + AI)
    moderation_result = await moderate_annonce_with_ai(
        title=annonce_data.title,
        description=annonce_data.description,
        category=annonce_data.category
    )
    
    # If moderation fails, reject immediately
    if not moderation_result["approved"]:
        rejection_message = get_rejection_message(moderation_result)
        raise HTTPException(
            status_code=400, 
            detail=rejection_message
        )
    
    # Annonce passed moderation - create with EN_ATTENTE status
    annonce = Annonce(
        client_id=current_user.id,
        client_name=current_user.full_name,
        client_email=current_user.email,
        client_phone=current_user.phone,
        title=annonce_data.title,
        description=annonce_data.description,
        category=annonce_data.category,
        city=annonce_data.city,
        address=annonce_data.address,
        status=AnnonceStatus.EN_ATTENTE.value
    )
    
    await db.annonces.insert_one(annonce.model_dump())
    
    # Get matched professionals immediately
    matched_pros = await get_matched_professionals_for_annonce(
        db, annonce_data.category, annonce_data.city, limit=5
    )
    
    return {
        "message": "Annonce créée avec succès. Elle sera visible après validation par l'admin.",
        "annonce_id": annonce.id,
        "matched_professionals": matched_pros
    }


# Category mapping for matching
CATEGORY_SERVICES_MAP = {
    "Installation Caméra": ["Vidéosurveillance", "Caméra", "Sécurité", "CCTV"],
    "Système d'Alarme": ["Alarme", "Sécurité", "Détection", "Intrusion"],
    "Domotique": ["Domotique", "Smart Home", "Automatisation", "Module"],
    "Éclairage Connecté": ["Éclairage", "Lumière", "LED", "Ampoule"],
    "Serrure Connectée": ["Serrure", "Accès", "Contrôle d'accès"],
    "Réseau WiFi/Câblage": ["Réseau", "WiFi", "Câblage", "Installation"],
    "Autre": []
}


async def get_matched_professionals_for_annonce(
    db: AsyncIOMotorDatabase, 
    category: str, 
    city: str, 
    limit: int = 5
) -> List[dict]:
    """
    Get best matched professionals based on:
    1. Category match (weight: 40%)
    2. Proximity/Zone (weight: 40%)
    3. Rating & Reviews (weight: 20%)
    """
    # Get all active professionals
    all_pros = await db.users.find(
        {
            "role": "PROFESSIONNEL",
            "is_active": True
        },
        {"_id": 0, "hashed_password": 0}
    ).to_list(200)
    
    if not all_pros:
        return []
    
    # Get nearby cities for proximity scoring
    nearby_cities = get_nearby_cities(city)
    
    # Get related service keywords for category matching
    category_keywords = CATEGORY_SERVICES_MAP.get(category, [])
    category_keywords.append(category)  # Include the category itself
    
    scored_pros = []
    
    for pro in all_pros:
        score = 0
        match_reasons = []
        
        # === 1. CATEGORY MATCH (40 points max) ===
        pro_services = pro.get("services", [])
        pro_specialties = pro.get("company_info", {}).get("specialties", [])
        pro_description = pro.get("company_info", {}).get("description", "").lower()
        
        # Check service match
        category_score = 0
        for keyword in category_keywords:
            keyword_lower = keyword.lower()
            # Check in services array
            if any(keyword_lower in str(s).lower() for s in pro_services):
                category_score = 40
                match_reasons.append(f"Spécialisé en {keyword}")
                break
            # Check in specialties
            if any(keyword_lower in str(s).lower() for s in pro_specialties):
                category_score = 35
                match_reasons.append(f"Expert {keyword}")
                break
            # Check in description
            if keyword_lower in pro_description:
                category_score = 25
                match_reasons.append(f"Expérience en {keyword}")
                break
        
        score += category_score
        
        # === 2. PROXIMITY (40 points max) ===
        pro_city = ""
        if pro.get("address_details", {}).get("city"):
            pro_city = pro["address_details"]["city"]
        elif pro.get("company_info", {}).get("address"):
            pro_city = pro["company_info"]["address"]
        elif pro.get("address"):
            pro_city = pro["address"]
        
        proximity_score = 0
        if pro_city:
            pro_city_lower = pro_city.lower()
            if city.lower() in pro_city_lower or pro_city_lower in city.lower():
                proximity_score = 40
                match_reasons.append(f"Dans votre ville ({city})")
            elif any(c.lower() in pro_city_lower for c in nearby_cities):
                proximity_score = 25
                match_reasons.append("Région proche")
            else:
                proximity_score = 5
        
        score += proximity_score
        
        # === 3. RATING & REVIEWS (20 points max) ===
        reviews = await db.reviews.find(
            {"professional_id": pro["id"]},
            {"rating": 1}
        ).to_list(100)
        
        rating_score = 0
        avg_rating = None
        review_count = len(reviews)
        
        if reviews:
            avg_rating = sum(r["rating"] for r in reviews) / len(reviews)
            # Scale: 5 stars = 20 points, 4 stars = 16 points, etc.
            rating_score = (avg_rating / 5) * 20
            if avg_rating >= 4.5:
                match_reasons.append(f"⭐ {avg_rating:.1f}/5 ({review_count} avis)")
            elif avg_rating >= 4.0:
                match_reasons.append(f"⭐ {avg_rating:.1f}/5")
        
        score += rating_score
        
        # Get completed missions count
        completed_missions = await db.annonces.count_documents({
            "responses.professional_id": pro["id"],
            "status": {"$in": ["ATTRIBUEE", "CLOTUREE"]}
        })
        
        if completed_missions > 5:
            match_reasons.append(f"{completed_missions} missions réalisées")
        
        # Add to list if has any relevance
        if score > 0:
            scored_pros.append({
                "id": pro["id"],
                "full_name": pro.get("full_name", ""),
                "email": pro.get("email", ""),
                "phone": pro.get("phone", ""),
                "company_name": pro.get("company_info", {}).get("company_name", ""),
                "company_logo": pro.get("company_info", {}).get("logo_url", ""),
                "city": pro_city,
                "services": pro_services[:3],  # First 3 services
                "average_rating": round(avg_rating, 1) if avg_rating else None,
                "review_count": review_count,
                "completed_missions": completed_missions,
                "match_score": round(score, 1),
                "match_reasons": match_reasons[:3],  # Top 3 reasons
                "is_same_city": proximity_score == 40
            })
    
    # Sort by score (highest first)
    scored_pros.sort(key=lambda x: -x["match_score"])
    
    return scored_pros[:limit]


@router.get("/matched-professionals/{annonce_id}")
async def get_matched_professionals(
    annonce_id: str,
    limit: int = 5,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get best matched professionals for an announcement"""
    # Get the annonce
    annonce = await db.annonces.find_one({"id": annonce_id, "client_id": current_user.id})
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    matched_pros = await get_matched_professionals_for_annonce(
        db, 
        annonce.get("category", ""), 
        annonce.get("city", ""),
        limit=limit
    )
    
    return {
        "professionals": matched_pros,
        "annonce_category": annonce.get("category"),
        "annonce_city": annonce.get("city"),
        "total": len(matched_pros)
    }


class NotifyProfessionalsRequest(BaseModel):
    professional_ids: List[str]


@router.post("/notify-professionals/{annonce_id}")
async def notify_professionals(
    annonce_id: str,
    request: NotifyProfessionalsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Send email, push, and in-app notifications to selected professionals about an announcement
    """
    # Import notification functions here to avoid circular imports
    from routes.notifications import create_notification, send_match_notification_email
    from services.push_service import send_new_annonce_push
    
    # Get the annonce
    annonce = await db.annonces.find_one({"id": annonce_id, "client_id": current_user.id})
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    # Get matched professionals data
    matched_pros = await get_matched_professionals_for_annonce(
        db, annonce.get("category", ""), annonce.get("city", ""), limit=10
    )
    
    # Filter to only selected professionals
    selected_pros = [p for p in matched_pros if p["id"] in request.professional_ids]
    
    if not selected_pros:
        raise HTTPException(status_code=400, detail="Aucun professionnel valide sélectionné")
    
    results = {
        "emails_sent": 0,
        "push_sent": 0,
        "notifications_created": 0,
        "errors": []
    }
    
    # Build the link to the annonce
    annonce_link = f"/annonces/{annonce_id}"
    
    for pro in selected_pros:
        # Prepare email data
        email_data = {
            "pro_name": pro.get("full_name", "Professionnel"),
            "annonce_title": annonce.get("title", "Nouvelle demande"),
            "category": annonce.get("category", ""),
            "city": annonce.get("city", ""),
            "description": annonce.get("description", ""),
            "match_score": pro.get("match_score", 0),
            "match_reasons": pro.get("match_reasons", []),
            "link": annonce_link
        }
        
        # 1. Send Email
        try:
            email_result = await send_match_notification_email(
                to_email=pro.get("email", ""),
                data=email_data
            )
            if email_result.get("status") == "success":
                results["emails_sent"] += 1
        except Exception as e:
            results["errors"].append(f"Email to {pro.get('email')}: {str(e)}")
        
        # 2. Send Push Notification
        try:
            push_result = await send_new_annonce_push(
                db=db,
                professional_id=pro.get("id"),
                annonce_title=annonce.get("title", "Nouvelle demande"),
                city=annonce.get("city", ""),
                match_score=int(pro.get("match_score", 0)),
                annonce_id=annonce_id
            )
            if push_result.get("status") == "success":
                results["push_sent"] += 1
        except Exception as e:
            results["errors"].append(f"Push to {pro.get('id')}: {str(e)}")
        
        # 3. Create in-app notification
        try:
            await create_notification(
                db=db,
                user_id=pro.get("id"),
                title="Nouvelle opportunité de mission !",
                message=f"{annonce.get('title')} - {annonce.get('city')} ({pro.get('match_score', 0)}% compatible)",
                notification_type="match",
                link=annonce_link,
                data={
                    "annonce_id": annonce_id,
                    "category": annonce.get("category"),
                    "city": annonce.get("city"),
                    "match_score": pro.get("match_score")
                }
            )
            results["notifications_created"] += 1
        except Exception as e:
            results["errors"].append(f"Notification for {pro.get('id')}: {str(e)}")
    
    return {
        "status": "success",
        "message": f"Notifications envoyées à {len(selected_pros)} professionnel(s)",
        "details": results
    }


@router.get("/nearby-professionals/{annonce_id}")
async def get_nearby_professionals(
    annonce_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get professionals near the announcement location (minimum 10)"""
    # Get the annonce
    annonce = await db.annonces.find_one({"id": annonce_id, "client_id": current_user.id})
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    city = annonce.get("city", "")
    nearby_cities = get_nearby_cities(city)
    
    # First, get professionals in the same city
    same_city_pros = await db.users.find(
        {
            "role": "PROFESSIONNEL",
            "is_active": True,
            "is_email_verified": True,
            "$or": [
                {"address_details.city": {"$regex": city, "$options": "i"}},
                {"address": {"$regex": city, "$options": "i"}},
                {"company_info.address": {"$regex": city, "$options": "i"}}
            ]
        },
        {"_id": 0, "hashed_password": 0}
    ).to_list(50)
    
    # Then get professionals in nearby cities
    nearby_pros = []
    if len(same_city_pros) < 10:
        nearby_query = {
            "role": "PROFESSIONNEL",
            "is_active": True,
            "is_email_verified": True
        }
        # Exclude same city professionals already found
        same_city_ids = [p["id"] for p in same_city_pros]
        if same_city_ids:
            nearby_query["id"] = {"$nin": same_city_ids}
        
        # Search in nearby cities
        city_patterns = [{"$or": [
            {"address_details.city": {"$regex": c, "$options": "i"}},
            {"address": {"$regex": c, "$options": "i"}},
            {"company_info.address": {"$regex": c, "$options": "i"}}
        ]} for c in nearby_cities if c.lower() != city.lower()]
        
        if city_patterns:
            nearby_query["$or"] = city_patterns
            nearby_pros = await db.users.find(
                nearby_query,
                {"_id": 0, "hashed_password": 0}
            ).to_list(50 - len(same_city_pros))
    
    # If still not enough, get any professionals
    all_pros = same_city_pros + nearby_pros
    if len(all_pros) < 10:
        existing_ids = [p["id"] for p in all_pros]
        additional_pros = await db.users.find(
            {
                "role": "PROFESSIONNEL",
                "is_active": True,
                "is_email_verified": True,
                "id": {"$nin": existing_ids} if existing_ids else {"$exists": True}
            },
            {"_id": 0, "hashed_password": 0}
        ).limit(10 - len(all_pros)).to_list(10 - len(all_pros))
        all_pros.extend(additional_pros)
    
    # Get ratings for each professional
    for pro in all_pros:
        # Calculate average rating from reviews
        reviews = await db.reviews.find(
            {"professional_id": pro["id"]},
            {"rating": 1}
        ).to_list(100)
        
        if reviews:
            pro["average_rating"] = sum(r["rating"] for r in reviews) / len(reviews)
            pro["review_count"] = len(reviews)
        else:
            pro["average_rating"] = None
            pro["review_count"] = 0
        
        # Check if in same city
        pro_city = ""
        if pro.get("address_details", {}).get("city"):
            pro_city = pro["address_details"]["city"]
        elif pro.get("company_info", {}).get("address"):
            pro_city = pro["company_info"]["address"]
        elif pro.get("address"):
            pro_city = pro["address"]
        
        pro["is_same_city"] = city.lower() in pro_city.lower() if pro_city else False
    
    # Sort: same city first, then by rating
    all_pros.sort(key=lambda x: (
        not x.get("is_same_city", False),
        -(x.get("average_rating") or 0)
    ))
    
    return {
        "professionals": all_pros,
        "annonce_city": city,
        "total": len(all_pros)
    }


@router.post("/notify-professionals/{annonce_id}")
async def notify_professionals(
    annonce_id: str,
    request: NotifyProfessionalsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Notify selected professionals about the announcement"""
    if len(request.professional_ids) > 5:
        raise HTTPException(status_code=400, detail="Vous ne pouvez notifier que 5 professionnels maximum")
    
    # Get the annonce
    annonce = await db.annonces.find_one({"id": annonce_id, "client_id": current_user.id})
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    # Get professionals
    professionals = await db.users.find(
        {"id": {"$in": request.professional_ids}, "role": "PROFESSIONNEL"},
        {"_id": 0}
    ).to_list(5)
    
    # Send notifications
    notified = []
    for pro in professionals:
        try:
            await send_annonce_notification_to_pro(
                to_email=pro["email"],
                pro_name=pro["full_name"],
                client_name=current_user.full_name,
                annonce_title=annonce["title"],
                annonce_id=annonce_id,
                city=annonce.get("city", ""),
                category=annonce.get("category", "")
            )
            notified.append(pro["id"])
        except Exception as e:
            print(f"Failed to notify {pro['email']}: {e}")
    
    # Save notified professionals in the annonce
    await db.annonces.update_one(
        {"id": annonce_id},
        {
            "$set": {
                "notified_professionals": request.professional_ids,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {
        "message": f"{len(notified)} professionnel(s) notifié(s) avec succès",
        "notified_count": len(notified)
    }


@router.get("/professional/{pro_id}/profile")
async def get_professional_profile(
    pro_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get a professional's public profile"""
    pro = await db.users.find_one(
        {"id": pro_id, "role": "PROFESSIONNEL"},
        {"_id": 0, "hashed_password": 0, "is_email_verified": 0}
    )
    
    if not pro:
        raise HTTPException(status_code=404, detail="Professionnel non trouvé")
    
    # Get reviews
    reviews = await db.reviews.find(
        {"professional_id": pro_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(20)
    
    # Calculate stats
    if reviews:
        pro["average_rating"] = sum(r["rating"] for r in reviews) / len(reviews)
        pro["review_count"] = len(reviews)
    else:
        pro["average_rating"] = None
        pro["review_count"] = 0
    
    # Get completed missions count
    completed_missions = await db.annonces.count_documents({
        "selected_response_id": {"$exists": True},
        "responses.professional_id": pro_id,
        "status": {"$in": ["ATTRIBUEE", "CLOTUREE"]}
    })
    pro["completed_missions"] = completed_missions
    
    pro["reviews"] = reviews
    
    return pro


@router.get("/my-annonces")
async def get_my_annonces(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all announcements created by the current user"""
    annonces = await db.annonces.find(
        {"client_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    return annonces


@router.get("/my-annonces/{annonce_id}")
async def get_my_annonce_detail(
    annonce_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get details of a specific announcement including responses"""
    annonce = await db.annonces.find_one(
        {"id": annonce_id, "client_id": current_user.id},
        {"_id": 0}
    )
    
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    return annonce


@router.post("/my-annonces/{annonce_id}/select-response/{response_id}")
async def select_professional(
    annonce_id: str,
    response_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Select a professional's response for the announcement"""
    annonce = await db.annonces.find_one({"id": annonce_id, "client_id": current_user.id})
    
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    if annonce["status"] not in [AnnonceStatus.PUBLIEE.value]:
        raise HTTPException(status_code=400, detail="Cette annonce ne peut plus être modifiée")
    
    # Verify the response exists
    response_exists = any(r["id"] == response_id for r in annonce.get("responses", []))
    if not response_exists:
        raise HTTPException(status_code=404, detail="Réponse non trouvée")
    
    await db.annonces.update_one(
        {"id": annonce_id},
        {
            "$set": {
                "selected_response_id": response_id,
                "status": AnnonceStatus.ATTRIBUEE.value,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Professionnel sélectionné avec succès"}


@router.post("/my-annonces/{annonce_id}/close")
async def close_annonce(
    annonce_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Close an announcement"""
    annonce = await db.annonces.find_one({"id": annonce_id, "client_id": current_user.id})
    
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    await db.annonces.update_one(
        {"id": annonce_id},
        {
            "$set": {
                "status": AnnonceStatus.CLOTUREE.value,
                "closed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Annonce clôturée avec succès"}


# ==================== PROFESSIONAL ROUTES ====================

@router.get("/public")
async def get_public_annonces(
    city: Optional[str] = None,
    category: Optional[str] = None,
    sort: Optional[str] = "recent",  # recent, oldest
    cursor: Optional[str] = None,  # Cursor-based pagination: "timestamp_id"
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get all published announcements with cursor-based pagination (for professionals).
    
    Cursor format: "ISO_TIMESTAMP|ID" (e.g., "2025-02-05T15:00:00|abc123")
    This ensures stable pagination even when new announcements are added.
    """
    if current_user.role not in ["PROFESSIONNEL", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux professionnels")
    
    query = {"status": AnnonceStatus.PUBLIEE.value}
    
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if category:
        query["category"] = category
    
    # Determine sort direction
    sort_direction = -1 if sort == "recent" else 1
    sort_field = "published_at"
    
    # Apply cursor for stable pagination
    if cursor:
        try:
            cursor_parts = cursor.split("|")
            cursor_timestamp = cursor_parts[0]
            cursor_id = cursor_parts[1] if len(cursor_parts) > 1 else ""
            
            from datetime import datetime
            cursor_dt = datetime.fromisoformat(cursor_timestamp.replace('Z', '+00:00'))
            
            # Cursor condition: get items AFTER the cursor position
            if sort_direction == -1:  # Descending (recent first)
                query["$or"] = [
                    {sort_field: {"$lt": cursor_dt}},
                    {sort_field: cursor_dt, "id": {"$lt": cursor_id}}
                ]
            else:  # Ascending (oldest first)
                query["$or"] = [
                    {sort_field: {"$gt": cursor_dt}},
                    {sort_field: cursor_dt, "id": {"$gt": cursor_id}}
                ]
        except Exception as e:
            # Invalid cursor, ignore and start from beginning
            pass
    
    # Get total count (without cursor for accurate total)
    base_query = {"status": AnnonceStatus.PUBLIEE.value}
    if city:
        base_query["city"] = {"$regex": city, "$options": "i"}
    if category:
        base_query["category"] = category
    total = await db.annonces.count_documents(base_query)
    
    # Fetch items with stable sort: sort_field + id for tie-breaking
    annonces = await db.annonces.find(
        query,
        {"_id": 0, "responses": 0}
    ).sort([
        (sort_field, sort_direction),
        ("id", sort_direction)
    ]).limit(limit + 1).to_list(limit + 1)  # Fetch one extra to check hasMore
    
    # Determine if there are more items
    has_more = len(annonces) > limit
    if has_more:
        annonces = annonces[:limit]  # Remove the extra item
    
    # Check if professional already responded to each annonce
    for annonce in annonces:
        full_annonce = await db.annonces.find_one({"id": annonce["id"]})
        annonce["already_responded"] = any(
            r["professional_id"] == current_user.id 
            for r in full_annonce.get("responses", [])
        )
    
    # Build next cursor from the last item
    next_cursor = None
    if annonces and has_more:
        last_item = annonces[-1]
        last_timestamp = last_item.get(sort_field) or last_item.get("created_at")
        if last_timestamp:
            if hasattr(last_timestamp, 'isoformat'):
                next_cursor = f"{last_timestamp.isoformat()}|{last_item['id']}"
            else:
                next_cursor = f"{last_timestamp}|{last_item['id']}"
    
    return {
        "items": annonces,
        "pagination": {
            "cursor": cursor,
            "next_cursor": next_cursor,
            "limit": limit,
            "total": total,
            "has_more": has_more
        }
    }


@router.get("/public/new-count")
async def get_new_annonces_count(
    since_cursor: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Check how many new announcements have been added since the cursor"""
    if current_user.role not in ["PROFESSIONNEL", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux professionnels")
    
    if not since_cursor:
        return {"new_count": 0}
    
    query = {"status": AnnonceStatus.PUBLIEE.value}
    
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if category:
        query["category"] = category
    
    try:
        cursor_parts = since_cursor.split("|")
        cursor_timestamp = cursor_parts[0]
        from datetime import datetime
        cursor_dt = datetime.fromisoformat(cursor_timestamp.replace('Z', '+00:00'))
        
        # Count items newer than cursor
        query["published_at"] = {"$gt": cursor_dt}
        new_count = await db.annonces.count_documents(query)
        
        return {"new_count": new_count}
    except:
        return {"new_count": 0}


@router.get("/public/cities")
async def get_cities(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get list of cities with published announcements"""
    cities = await db.annonces.distinct(
        "city",
        {"status": AnnonceStatus.PUBLIEE.value}
    )
    cities.sort()
    return cities


# ==================== SEO/PUBLIC BROWSE ROUTES (No Auth Required) ====================

@router.get("/browse")
async def browse_annonces(
    city: Optional[str] = None,
    category: Optional[str] = None,
    cursor: Optional[str] = None,
    limit: int = 12,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Public route to browse published announcements (no auth required).
    Used for SEO and public access.
    Returns limited info (no contact details).
    """
    query = {"status": AnnonceStatus.PUBLIEE.value}
    
    if city:
        query["city"] = {"$regex": city, "$options": "i"}
    if category:
        query["category"] = category
    
    # Count total
    total = await db.annonces.count_documents(query)
    
    # Build cursor query for pagination
    if cursor:
        try:
            cursor_date, cursor_id = cursor.split("|")
            cursor_date = datetime.fromisoformat(cursor_date)
            query["$or"] = [
                {"published_at": {"$lt": cursor_date}},
                {"published_at": cursor_date, "id": {"$lt": cursor_id}}
            ]
        except:
            pass
    
    # Fetch annonces with limited fields (no contact info)
    annonces = await db.annonces.find(
        query,
        {
            "_id": 0,
            "id": 1,
            "title": 1,
            "description": 1,
            "category": 1,
            "city": 1,
            "published_at": 1,
            "created_at": 1
        }
    ).sort([("published_at", -1), ("id", -1)]).limit(limit + 1).to_list(limit + 1)
    
    # Check if there are more results
    has_more = len(annonces) > limit
    if has_more:
        annonces = annonces[:limit]
    
    # Build next cursor
    next_cursor = None
    if annonces and has_more:
        last = annonces[-1]
        pub_date = last.get("published_at") or last.get("created_at")
        if pub_date:
            # Handle both datetime objects and ISO strings
            if isinstance(pub_date, str):
                next_cursor = f"{pub_date}|{last['id']}"
            else:
                next_cursor = f"{pub_date.isoformat()}|{last['id']}"
    
    return {
        "annonces": annonces,
        "pagination": {
            "total": total,
            "has_more": has_more,
            "next_cursor": next_cursor,
            "limit": limit
        }
    }


@router.get("/browse/cities")
async def get_browse_cities(
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get list of cities (no auth required)"""
    cities = await db.annonces.distinct(
        "city",
        {"status": AnnonceStatus.PUBLIEE.value}
    )
    cities.sort()
    return cities


@router.get("/browse/{annonce_id}")
async def get_browse_annonce_detail(
    annonce_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Get public details of an announcement (no auth required).
    Returns limited info for SEO purposes.
    """
    annonce = await db.annonces.find_one(
        {"id": annonce_id, "status": AnnonceStatus.PUBLIEE.value},
        {
            "_id": 0,
            "id": 1,
            "title": 1,
            "description": 1,
            "category": 1,
            "city": 1,
            "address": 1,
            "published_at": 1,
            "created_at": 1
        }
    )
    
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée ou non publiée")
    
    # Count responses (don't expose details)
    full_annonce = await db.annonces.find_one({"id": annonce_id}, {"responses": 1})
    annonce["responses_count"] = len(full_annonce.get("responses", []))
    
    return annonce


@router.get("/public/{annonce_id}")
async def get_public_annonce_detail(
    annonce_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get details of a published announcement"""
    if current_user.role not in ["PROFESSIONNEL", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Accès réservé aux professionnels")
    
    annonce = await db.annonces.find_one(
        {"id": annonce_id, "status": AnnonceStatus.PUBLIEE.value},
        {"_id": 0, "responses": 0}
    )
    
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée ou non publiée")
    
    # Check if current professional already responded
    full_annonce = await db.annonces.find_one({"id": annonce_id})
    already_responded = any(
        r["professional_id"] == current_user.id 
        for r in full_annonce.get("responses", [])
    )
    annonce["already_responded"] = already_responded
    
    return annonce


@router.post("/public/{annonce_id}/respond")
async def respond_to_annonce(
    annonce_id: str,
    response_data: AnnonceResponseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Respond to an announcement (professionals only)"""
    if current_user.role != "PROFESSIONNEL":
        raise HTTPException(status_code=403, detail="Seuls les professionnels peuvent répondre aux annonces")
    
    annonce = await db.annonces.find_one({"id": annonce_id})
    
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    if annonce["status"] != AnnonceStatus.PUBLIEE.value:
        raise HTTPException(status_code=400, detail="Cette annonce n'est plus disponible")
    
    # Check if already responded
    already_responded = any(
        r["professional_id"] == current_user.id 
        for r in annonce.get("responses", [])
    )
    if already_responded:
        raise HTTPException(status_code=400, detail="Vous avez déjà répondu à cette annonce")
    
    response = AnnonceResponse(
        professional_id=current_user.id,
        professional_name=current_user.full_name,
        professional_email=current_user.email,
        professional_phone=current_user.phone,
        message=response_data.message,
        price_estimate=response_data.price_estimate,
        availability=response_data.availability
    )
    
    await db.annonces.update_one(
        {"id": annonce_id},
        {
            "$push": {"responses": response.model_dump()},
            "$set": {"updated_at": datetime.now(timezone.utc)}
        }
    )
    
    # Send notification to client
    try:
        await send_response_notification_to_client(
            to_email=annonce["client_email"],
            client_name=annonce["client_name"],
            pro_name=current_user.full_name,
            annonce_title=annonce["title"],
            annonce_id=annonce_id,
            message_preview=response_data.message
        )
    except Exception as e:
        print(f"Failed to send notification to client: {e}")
    
    return {"message": "Réponse envoyée avec succès"}


@router.get("/my-responses")
async def get_my_responses(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all announcements where the professional has responded"""
    if current_user.role != "PROFESSIONNEL":
        raise HTTPException(status_code=403, detail="Accès réservé aux professionnels")
    
    annonces = await db.annonces.find(
        {"responses.professional_id": current_user.id},
        {"_id": 0}
    ).sort("updated_at", -1).to_list(100)
    
    # Add the professional's response to each annonce
    result = []
    for annonce in annonces:
        my_response = next(
            (r for r in annonce.get("responses", []) if r["professional_id"] == current_user.id),
            None
        )
        annonce["my_response"] = my_response
        annonce["is_selected"] = annonce.get("selected_response_id") == (my_response["id"] if my_response else None)
        # Remove other responses for privacy
        annonce.pop("responses", None)
        result.append(annonce)
    
    return result


# ==================== ADMIN ROUTES ====================

@router.get("/admin/all")
async def admin_get_all_annonces(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all announcements (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    query = {}
    if status_filter:
        query["status"] = status_filter
    
    annonces = await db.annonces.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    return annonces


@router.get("/admin/pending")
async def admin_get_pending_annonces(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get announcements waiting for validation (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    annonces = await db.annonces.find(
        {"status": AnnonceStatus.EN_ATTENTE.value},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    return annonces


@router.post("/admin/{annonce_id}/validate")
async def admin_validate_annonce(
    annonce_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Validate and publish an announcement (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    annonce = await db.annonces.find_one({"id": annonce_id})
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    if annonce["status"] != AnnonceStatus.EN_ATTENTE.value:
        raise HTTPException(status_code=400, detail="Cette annonce a déjà été traitée")
    
    await db.annonces.update_one(
        {"id": annonce_id},
        {
            "$set": {
                "status": AnnonceStatus.PUBLIEE.value,
                "published_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Annonce validée et publiée"}


@router.post("/admin/{annonce_id}/reject")
async def admin_reject_annonce(
    annonce_id: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Reject an announcement (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    annonce = await db.annonces.find_one({"id": annonce_id})
    if not annonce:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    await db.annonces.update_one(
        {"id": annonce_id},
        {
            "$set": {
                "status": AnnonceStatus.REFUSEE.value,
                "admin_notes": reason,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    return {"message": "Annonce refusée"}


@router.delete("/admin/{annonce_id}")
async def admin_delete_annonce(
    annonce_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete an announcement (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    result = await db.annonces.delete_one({"id": annonce_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Annonce non trouvée")
    
    return {"message": "Annonce supprimée"}


@router.get("/admin/stats")
async def admin_get_annonces_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get announcements statistics (admin only)"""
    if current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Accès réservé aux administrateurs")
    
    total = await db.annonces.count_documents({})
    pending = await db.annonces.count_documents({"status": AnnonceStatus.EN_ATTENTE.value})
    published = await db.annonces.count_documents({"status": AnnonceStatus.PUBLIEE.value})
    attributed = await db.annonces.count_documents({"status": AnnonceStatus.ATTRIBUEE.value})
    closed = await db.annonces.count_documents({"status": AnnonceStatus.CLOTUREE.value})
    rejected = await db.annonces.count_documents({"status": AnnonceStatus.REFUSEE.value})
    
    return {
        "total": total,
        "pending": pending,
        "published": published,
        "attributed": attributed,
        "closed": closed,
        "rejected": rejected
    }
