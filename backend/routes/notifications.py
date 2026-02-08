"""
Notifications Service - Email, In-App & Push Notifications for MyDar
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
import os
import uuid
import logging
from dotenv import load_dotenv

from utils.dependencies import get_current_user, get_db
from models.user import User
from services.email_service import send_email
from services.push_service import (
    send_new_annonce_push,
    send_annonce_response_push,
    send_push_to_user
)

load_dotenv()

router = APIRouter(prefix="/notifications", tags=["notifications"])
logger = logging.getLogger(__name__)

FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://mydar-tn.com")
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")


# ============ MODELS ============

class NotifyProfessionalsRequest(BaseModel):
    professional_ids: List[str]


# ============ EMAIL TEMPLATES ============

def get_match_notification_email(data: dict) -> str:
    """Generate HTML email for match notification"""
    
    match_reasons_html = ' '.join([
        f'<span style="display: inline-block; background: #e0e7ff; color: #4338ca; padding: 4px 12px; border-radius: 20px; font-size: 12px; margin: 2px;">{r}</span>' 
        for r in data.get('match_reasons', [])
    ])
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="text-align: center; margin-bottom: 30px;">
            <h1 style="background: linear-gradient(90deg, #7C3AED, #06B6D4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">MyDar</h1>
            <p style="color: #6b7280;">Nouvelle opportunité de mission !</p>
        </div>
        
        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px; margin-bottom: 20px;">
            <h2 style="color: #1f2937; margin-top: 0;">Bonjour {data.get('pro_name', 'Professionnel')} 👋</h2>
            <p>Un client recherche un professionnel pour une mission qui correspond à votre profil !</p>
            
            <div style="background-color: white; border-left: 4px solid #7c3aed; border-radius: 0 8px 8px 0; padding: 20px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #7c3aed;">📋 {data.get('annonce_title', 'Nouvelle demande')}</h3>
                <p><strong>📍 Ville :</strong> {data.get('city', 'Non spécifiée')}</p>
                <p><strong>🏷️ Catégorie :</strong> {data.get('category', 'Non spécifiée')}</p>
                <p><strong>📝 Description :</strong></p>
                <p style="color: #6b7280;">{data.get('description', '')[:300]}...</p>
            </div>
            
            <div style="text-align: center; margin: 20px 0;">
                <p style="font-size: 18px;"><strong>Score de compatibilité : {data.get('match_score', 0)}%</strong></p>
                <div>{match_reasons_html}</div>
            </div>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{data.get('link', '#')}" style="display: inline-block; background: linear-gradient(90deg, #7C3AED, #06B6D4); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: bold; font-size: 16px;">Voir la demande et répondre →</a>
            </div>
            
            <p style="color: #6b7280; font-size: 14px;">
                💡 Conseil : Répondez rapidement pour augmenter vos chances d'être sélectionné !
            </p>
        </div>
        
        <div style="text-align: center; color: #6b7280; font-size: 12px;">
            <p>MyDar - Votre partenaire domotique en Tunisie</p>
            <p>© 2026 MyDar. Tous droits réservés.</p>
        </div>
    </body>
    </html>
    """


async def send_match_notification_email(to_email: str, data: dict) -> dict:
    """Send match notification email to professional"""
    try:
        html_content = get_match_notification_email(data)
        result = await send_email(
            to_email=to_email,
            subject=f"🏠 MyDar - Nouvelle mission : {data.get('annonce_title', 'Demande client')}",
            html_content=html_content
        )
        return result
    except Exception as e:
        logger.error(f"Failed to send match notification email: {e}")
        return {"status": "error", "error": str(e)}


# ============ IN-APP NOTIFICATIONS ============

async def create_notification(
    db: AsyncIOMotorDatabase,
    user_id: str,
    title: str,
    message: str,
    notification_type: str = "info",
    link: str = None,
    data: dict = None
) -> dict:
    """Create an in-app notification for a user"""
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notification_type,
        "link": link,
        "data": data or {},
        "read": False,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.notifications.insert_one(notification)
    return notification


# ============ API ENDPOINTS ============

@router.get("")
async def get_my_notifications(
    limit: int = 20,
    unread_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get current user's notifications"""
    query = {"user_id": current_user.id}
    if unread_only:
        query["read"] = False
    
    notifications = await db.notifications.find(
        query,
        {"_id": 0}
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    # Get unread count
    unread_count = await db.notifications.count_documents({
        "user_id": current_user.id,
        "read": False
    })
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }


@router.post("/mark-read/{notification_id}")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Mark a notification as read"""
    result = await db.notifications.update_one(
        {"id": notification_id, "user_id": current_user.id},
        {"$set": {"read": True}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    return {"status": "success"}


@router.post("/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Mark all notifications as read"""
    result = await db.notifications.update_many(
        {"user_id": current_user.id, "read": False},
        {"$set": {"read": True}}
    )
    
    return {"status": "success", "updated": result.modified_count}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Delete a notification"""
    result = await db.notifications.delete_one({
        "id": notification_id,
        "user_id": current_user.id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    return {"status": "success"}


# ============ PUSH SUBSCRIPTION ============

@router.post("/subscribe-push")
async def subscribe_to_push(
    subscription: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Save push notification subscription for a user"""
    await db.push_subscriptions.update_one(
        {"user_id": current_user.id},
        {
            "$set": {
                "user_id": current_user.id,
                "subscription": subscription,
                "updated_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )
    
    return {"status": "success", "message": "Notifications push activées"}


@router.delete("/unsubscribe-push")
async def unsubscribe_from_push(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Remove push notification subscription"""
    await db.push_subscriptions.delete_one({"user_id": current_user.id})
    return {"status": "success", "message": "Notifications push désactivées"}


@router.get("/vapid-public-key")
async def get_vapid_public_key():
    """Get VAPID public key for push subscription"""
    if not VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="Push notifications not configured")
    return {"public_key": VAPID_PUBLIC_KEY}


@router.get("/push-status")
async def get_push_status(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Check if user has push notifications enabled"""
    subscription = await db.push_subscriptions.find_one({"user_id": current_user.id})
    return {
        "enabled": subscription is not None,
        "subscribed_at": subscription.get("updated_at") if subscription else None
    }


@router.post("/test-push")
async def test_push_notification(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Send a test push notification to current user"""
    result = await send_push_to_user(
        db=db,
        user_id=current_user.id,
        title="🔔 Test MyDar",
        body="Les notifications push fonctionnent correctement !",
        url="/dashboard"
    )
    
    if result.get("status") == "no_subscription":
        raise HTTPException(
            status_code=400, 
            detail="Aucun abonnement push trouvé. Activez d'abord les notifications."
        )
    
    return result
