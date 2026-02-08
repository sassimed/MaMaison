from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.dependencies import get_db, get_current_user
from models.user import User
from models.review import ReviewCreate, ReviewResponse, ReviewStats, ProfessionalStats, ProductStats, create_review_dict
from typing import Optional
from datetime import datetime, timezone

router = APIRouter(prefix="/reviews", tags=["Reviews"])


async def calculate_review_stats(db: AsyncIOMotorDatabase, target_type: str, target_id: str) -> dict:
    """Calculate review statistics for a target"""
    pipeline = [
        {"$match": {"target_type": target_type, "target_id": target_id}},
        {"$group": {
            "_id": "$rating",
            "count": {"$sum": 1}
        }}
    ]
    
    results = await db.reviews.aggregate(pipeline).to_list(10)
    
    total = 0
    weighted_sum = 0
    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    
    for r in results:
        rating = r["_id"]
        count = r["count"]
        distribution[rating] = count
        total += count
        weighted_sum += rating * count
    
    average = round(weighted_sum / total, 1) if total > 0 else 0.0
    
    return {
        "average_rating": average,
        "total_reviews": total,
        "rating_distribution": distribution
    }


@router.post("", response_model=dict)
async def create_review(
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Create a new review for a product or professional"""
    
    # Verify target exists
    if review.target_type == "product":
        target = await db.products.find_one({"id": review.target_id})
        if not target:
            raise HTTPException(status_code=404, detail="Produit non trouvé")
    elif review.target_type == "professional":
        target = await db.users.find_one({"id": review.target_id, "role": "PROFESSIONNEL"})
        if not target:
            raise HTTPException(status_code=404, detail="Professionnel non trouvé")
    else:
        raise HTTPException(status_code=400, detail="Type de cible invalide")
    
    # Check if user already reviewed this target
    existing = await db.reviews.find_one({
        "target_type": review.target_type,
        "target_id": review.target_id,
        "user_id": current_user.id
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Vous avez déjà laissé un avis")
    
    # For professional reviews, check if user had an intervention with them
    if review.target_type == "professional":
        # Check if user has a completed annonce with this professional
        annonce = await db.annonces.find_one({
            "client_id": current_user.id,
            "selected_response_id": {"$ne": None},
            "status": {"$in": ["ATTRIBUEE", "CLOTUREE"]},
            "responses": {
                "$elemMatch": {
                    "professional_id": review.target_id
                }
            }
        })
        
        # Also check if professional was selected
        if annonce:
            selected_response = next(
                (r for r in annonce.get("responses", []) if r.get("id") == annonce.get("selected_response_id")),
                None
            )
            if not selected_response or selected_response.get("professional_id") != review.target_id:
                annonce = None
        
        if not annonce:
            raise HTTPException(
                status_code=403, 
                detail="Vous devez avoir travaillé avec ce professionnel pour laisser un avis"
            )
    
    # For product reviews, check if user purchased the product
    if review.target_type == "product":
        purchase = await db.purchase_requests.find_one({
            "user_id": current_user.id,
            "status": {"$in": ["VALIDEE", "EN_PREPARATION", "EXPEDIEE", "LIVREE"]},
            "items": {
                "$elemMatch": {"product_id": review.target_id}
            }
        })
        
        if not purchase:
            raise HTTPException(
                status_code=403,
                detail="Vous devez avoir acheté ce produit pour laisser un avis"
            )
    
    # Create review
    review_dict = create_review_dict(
        target_type=review.target_type,
        target_id=review.target_id,
        user_id=current_user.id,
        user_name=current_user.full_name,
        rating=review.rating,
        comment=review.comment
    )
    
    await db.reviews.insert_one(review_dict)
    
    # Update target's average rating
    stats = await calculate_review_stats(db, review.target_type, review.target_id)
    
    if review.target_type == "product":
        await db.products.update_one(
            {"id": review.target_id},
            {"$set": {
                "average_rating": stats["average_rating"],
                "review_count": stats["total_reviews"]
            }}
        )
    elif review.target_type == "professional":
        await db.users.update_one(
            {"id": review.target_id},
            {"$set": {
                "average_rating": stats["average_rating"],
                "review_count": stats["total_reviews"]
            }}
        )
    
    return {
        "message": "Avis ajouté avec succès",
        "review_id": review_dict["id"],
        "new_average": stats["average_rating"]
    }


@router.get("/product/{product_id}")
async def get_product_reviews(
    product_id: str,
    cursor: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get reviews for a product with cursor-based pagination"""
    
    # Verify product exists
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    query = {"target_type": "product", "target_id": product_id}
    
    # Apply cursor
    if cursor:
        try:
            cursor_parts = cursor.split("|")
            cursor_timestamp = datetime.fromisoformat(cursor_parts[0].replace('Z', '+00:00'))
            cursor_id = cursor_parts[1] if len(cursor_parts) > 1 else ""
            
            query["$or"] = [
                {"created_at": {"$lt": cursor_timestamp}},
                {"created_at": cursor_timestamp, "id": {"$lt": cursor_id}}
            ]
        except:
            pass
    
    # Get reviews
    reviews = await db.reviews.find(
        query,
        {"_id": 0}
    ).sort([("created_at", -1), ("id", -1)]).limit(limit + 1).to_list(limit + 1)
    
    has_more = len(reviews) > limit
    if has_more:
        reviews = reviews[:limit]
    
    # Build next cursor
    next_cursor = None
    if reviews and has_more:
        last = reviews[-1]
        ts = last["created_at"]
        if hasattr(ts, 'isoformat'):
            next_cursor = f"{ts.isoformat()}|{last['id']}"
    
    # Get stats
    stats = await calculate_review_stats(db, "product", product_id)
    
    return {
        "product": {
            "id": product["id"],
            "name": product["name"],
            "image_url": product.get("image_url")
        },
        "stats": stats,
        "reviews": reviews,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
            "limit": limit
        }
    }


@router.get("/professional/{professional_id}")
async def get_professional_reviews(
    professional_id: str,
    cursor: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get reviews for a professional with cursor-based pagination"""
    
    # Verify professional exists
    professional = await db.users.find_one(
        {"id": professional_id, "role": "PROFESSIONNEL"},
        {"_id": 0, "hashed_password": 0}
    )
    if not professional:
        raise HTTPException(status_code=404, detail="Professionnel non trouvé")
    
    query = {"target_type": "professional", "target_id": professional_id}
    
    # Apply cursor
    if cursor:
        try:
            cursor_parts = cursor.split("|")
            cursor_timestamp = datetime.fromisoformat(cursor_parts[0].replace('Z', '+00:00'))
            cursor_id = cursor_parts[1] if len(cursor_parts) > 1 else ""
            
            query["$or"] = [
                {"created_at": {"$lt": cursor_timestamp}},
                {"created_at": cursor_timestamp, "id": {"$lt": cursor_id}}
            ]
        except:
            pass
    
    # Get reviews
    reviews = await db.reviews.find(
        query,
        {"_id": 0}
    ).sort([("created_at", -1), ("id", -1)]).limit(limit + 1).to_list(limit + 1)
    
    has_more = len(reviews) > limit
    if has_more:
        reviews = reviews[:limit]
    
    # Build next cursor
    next_cursor = None
    if reviews and has_more:
        last = reviews[-1]
        ts = last["created_at"]
        if hasattr(ts, 'isoformat'):
            next_cursor = f"{ts.isoformat()}|{last['id']}"
    
    # Get stats
    stats = await calculate_review_stats(db, "professional", professional_id)
    
    # Count interventions (completed annonces)
    intervention_count = await db.annonces.count_documents({
        "status": {"$in": ["ATTRIBUEE", "CLOTUREE"]},
        "responses": {
            "$elemMatch": {"professional_id": professional_id}
        }
    })
    
    # More accurate: count only where this professional was selected
    pipeline = [
        {"$match": {"status": {"$in": ["ATTRIBUEE", "CLOTUREE"]}}},
        {"$unwind": "$responses"},
        {"$match": {
            "responses.professional_id": professional_id,
            "$expr": {"$eq": ["$responses.id", "$selected_response_id"]}
        }},
        {"$count": "total"}
    ]
    result = await db.annonces.aggregate(pipeline).to_list(1)
    intervention_count = result[0]["total"] if result else 0
    
    return {
        "professional": {
            "id": professional["id"],
            "name": professional["full_name"],
            "email": professional.get("email"),
            "phone": professional.get("phone"),
            "company_name": professional.get("company_name")
        },
        "stats": {
            **stats,
            "intervention_count": intervention_count
        },
        "reviews": reviews,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
            "limit": limit
        }
    }


@router.get("/product/{product_id}/stats")
async def get_product_stats(
    product_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get statistics for a product (rating + sales)"""
    
    product = await db.products.find_one({"id": product_id}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Produit non trouvé")
    
    # Get review stats
    stats = await calculate_review_stats(db, "product", product_id)
    
    # Count sales (sum of quantities in validated purchase requests)
    pipeline = [
        {"$match": {"status": {"$in": ["VALIDEE", "EN_PREPARATION", "EXPEDIEE", "LIVREE"]}}},
        {"$unwind": "$items"},
        {"$match": {"items.product_id": product_id}},
        {"$group": {"_id": None, "total": {"$sum": "$items.quantity"}}}
    ]
    result = await db.purchase_requests.aggregate(pipeline).to_list(1)
    sales_count = result[0]["total"] if result else 0
    
    return {
        "product_id": product_id,
        "product_name": product["name"],
        "average_rating": stats["average_rating"],
        "total_reviews": stats["total_reviews"],
        "rating_distribution": stats["rating_distribution"],
        "sales_count": sales_count
    }


@router.get("/professional/{professional_id}/stats")
async def get_professional_stats(
    professional_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get statistics for a professional (rating + interventions)"""
    
    professional = await db.users.find_one(
        {"id": professional_id, "role": "PROFESSIONNEL"},
        {"_id": 0, "hashed_password": 0}
    )
    if not professional:
        raise HTTPException(status_code=404, detail="Professionnel non trouvé")
    
    # Get review stats
    stats = await calculate_review_stats(db, "professional", professional_id)
    
    # Count interventions where this professional was selected
    pipeline = [
        {"$match": {"status": {"$in": ["ATTRIBUEE", "CLOTUREE"]}}},
        {"$unwind": "$responses"},
        {"$match": {
            "responses.professional_id": professional_id,
            "$expr": {"$eq": ["$responses.id", "$selected_response_id"]}
        }},
        {"$count": "total"}
    ]
    result = await db.annonces.aggregate(pipeline).to_list(1)
    intervention_count = result[0]["total"] if result else 0
    
    return {
        "professional_id": professional_id,
        "professional_name": professional["full_name"],
        "average_rating": stats["average_rating"],
        "total_reviews": stats["total_reviews"],
        "rating_distribution": stats["rating_distribution"],
        "intervention_count": intervention_count
    }


@router.delete("/{review_id}")
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a review (only by the author or admin)"""
    
    review = await db.reviews.find_one({"id": review_id})
    if not review:
        raise HTTPException(status_code=404, detail="Avis non trouvé")
    
    # Check permission
    if review["user_id"] != current_user.id and current_user.role != "ADMIN":
        raise HTTPException(status_code=403, detail="Non autorisé")
    
    # Delete review
    await db.reviews.delete_one({"id": review_id})
    
    # Recalculate stats
    stats = await calculate_review_stats(db, review["target_type"], review["target_id"])
    
    # Update target's rating
    if review["target_type"] == "product":
        await db.products.update_one(
            {"id": review["target_id"]},
            {"$set": {
                "average_rating": stats["average_rating"],
                "review_count": stats["total_reviews"]
            }}
        )
    elif review["target_type"] == "professional":
        await db.users.update_one(
            {"id": review["target_id"]},
            {"$set": {
                "average_rating": stats["average_rating"],
                "review_count": stats["total_reviews"]
            }}
        )
    
    return {"message": "Avis supprimé"}


@router.get("/my-reviews")
async def get_my_reviews(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all reviews written by the current user"""
    
    reviews = await db.reviews.find(
        {"user_id": current_user.id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with target info
    for review in reviews:
        if review["target_type"] == "product":
            product = await db.products.find_one({"id": review["target_id"]}, {"_id": 0, "name": 1, "image_url": 1})
            review["target_name"] = product["name"] if product else "Produit supprimé"
            review["target_image"] = product.get("image_url") if product else None
        elif review["target_type"] == "professional":
            pro = await db.users.find_one({"id": review["target_id"]}, {"_id": 0, "full_name": 1})
            review["target_name"] = pro["full_name"] if pro else "Professionnel supprimé"
    
    return reviews
