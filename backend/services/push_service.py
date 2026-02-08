"""
Web Push Notification Service for MyDar
"""
import os
import base64
import json
import asyncio
import logging
from typing import Optional
from pywebpush import webpush, WebPushException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Load VAPID configuration
VAPID_PUBLIC_KEY = os.environ.get("VAPID_PUBLIC_KEY")
VAPID_PRIVATE_KEY_PEM_B64 = os.environ.get("VAPID_PRIVATE_KEY_PEM_B64")
VAPID_MAILTO = os.environ.get("VAPID_MAILTO", "mailto:contact@mydar.tn")

# Decode private key from base64
VAPID_PRIVATE_KEY_PEM = None
if VAPID_PRIVATE_KEY_PEM_B64:
    VAPID_PRIVATE_KEY_PEM = base64.b64decode(VAPID_PRIVATE_KEY_PEM_B64).decode()


def get_vapid_claims():
    """Get VAPID claims for webpush"""
    return {
        "sub": VAPID_MAILTO
    }


async def send_push_notification(
    subscription: dict,
    title: str,
    body: str,
    icon: str = "/mydar-logo.png",
    badge: str = "/mydar-logo.png",
    url: str = None,
    tag: str = None,
    data: dict = None
) -> dict:
    """
    Send a push notification to a single subscription
    
    Args:
        subscription: The push subscription object from the browser
        title: Notification title
        body: Notification body text
        icon: Icon URL (default: app logo)
        badge: Badge icon URL
        url: URL to open when notification is clicked
        tag: Notification tag (for grouping)
        data: Additional data to pass to the service worker
    
    Returns:
        dict with status and details
    """
    if not VAPID_PRIVATE_KEY_PEM:
        logger.error("VAPID private key not configured")
        return {"status": "error", "error": "Push notifications not configured"}
    
    # Build notification payload
    notification_payload = {
        "title": title,
        "body": body,
        "icon": icon,
        "badge": badge,
        "tag": tag or "mydar-notification",
        "data": {
            "url": url or "/dashboard",
            **(data or {})
        },
        "requireInteraction": True,
        "vibrate": [200, 100, 200]
    }
    
    try:
        # Run webpush in thread pool to avoid blocking
        response = await asyncio.to_thread(
            webpush,
            subscription_info=subscription,
            data=json.dumps(notification_payload),
            vapid_private_key=VAPID_PRIVATE_KEY_PEM,
            vapid_claims=get_vapid_claims()
        )
        
        logger.info(f"Push notification sent successfully: {title}")
        return {"status": "success", "response": str(response)}
        
    except WebPushException as e:
        logger.error(f"WebPush error: {e}")
        
        # Handle expired subscriptions
        if e.response and e.response.status_code in [404, 410]:
            return {"status": "expired", "error": "Subscription expired"}
        
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Push notification error: {e}")
        return {"status": "error", "error": str(e)}


async def send_push_to_user(
    db,
    user_id: str,
    title: str,
    body: str,
    url: str = None,
    **kwargs
) -> dict:
    """
    Send push notification to a specific user
    
    Args:
        db: Database connection
        user_id: The user's ID
        title: Notification title
        body: Notification body
        url: URL to open on click
        **kwargs: Additional arguments for send_push_notification
    
    Returns:
        dict with status
    """
    # Get user's push subscription
    sub_doc = await db.push_subscriptions.find_one({"user_id": user_id})
    
    if not sub_doc or not sub_doc.get("subscription"):
        logger.debug(f"No push subscription found for user {user_id}")
        return {"status": "no_subscription", "user_id": user_id}
    
    result = await send_push_notification(
        subscription=sub_doc["subscription"],
        title=title,
        body=body,
        url=url,
        **kwargs
    )
    
    # If subscription expired, remove it from database
    if result.get("status") == "expired":
        await db.push_subscriptions.delete_one({"user_id": user_id})
        logger.info(f"Removed expired subscription for user {user_id}")
    
    return result


async def send_push_to_multiple_users(
    db,
    user_ids: list,
    title: str,
    body: str,
    url: str = None,
    **kwargs
) -> dict:
    """
    Send push notification to multiple users
    
    Args:
        db: Database connection
        user_ids: List of user IDs
        title: Notification title
        body: Notification body
        url: URL to open on click
        **kwargs: Additional arguments
    
    Returns:
        dict with success/failure counts
    """
    results = {
        "total": len(user_ids),
        "sent": 0,
        "failed": 0,
        "no_subscription": 0,
        "expired": 0,
        "details": []
    }
    
    for user_id in user_ids:
        result = await send_push_to_user(
            db=db,
            user_id=user_id,
            title=title,
            body=body,
            url=url,
            **kwargs
        )
        
        status = result.get("status")
        if status == "success":
            results["sent"] += 1
        elif status == "no_subscription":
            results["no_subscription"] += 1
        elif status == "expired":
            results["expired"] += 1
        else:
            results["failed"] += 1
        
        results["details"].append({
            "user_id": user_id,
            "status": status
        })
    
    logger.info(
        f"Push notifications sent: {results['sent']}/{results['total']} "
        f"(failed: {results['failed']}, no_sub: {results['no_subscription']}, expired: {results['expired']})"
    )
    
    return results


# ============ NOTIFICATION TEMPLATES ============

async def send_new_annonce_push(
    db,
    professional_id: str,
    annonce_title: str,
    city: str,
    match_score: int,
    annonce_id: str
) -> dict:
    """Send push notification to professional about new matching announcement"""
    
    title = "🏠 Nouvelle mission disponible !"
    body = f"{annonce_title} à {city} - Compatibilité: {match_score}%"
    url = "/dashboard/annonces"
    
    return await send_push_to_user(
        db=db,
        user_id=professional_id,
        title=title,
        body=body,
        url=url,
        tag=f"annonce-{annonce_id}",
        data={"annonce_id": annonce_id, "type": "new_annonce"}
    )


async def send_annonce_response_push(
    db,
    client_id: str,
    pro_name: str,
    annonce_title: str,
    annonce_id: str
) -> dict:
    """Send push notification to client when a professional responds"""
    
    title = "✅ Réponse d'un professionnel !"
    body = f"{pro_name} a répondu à votre annonce: {annonce_title}"
    url = f"/dashboard/my-annonces/{annonce_id}"
    
    return await send_push_to_user(
        db=db,
        user_id=client_id,
        title=title,
        body=body,
        url=url,
        tag=f"response-{annonce_id}",
        data={"annonce_id": annonce_id, "type": "annonce_response"}
    )


async def send_message_push(
    db,
    recipient_id: str,
    sender_name: str,
    message_preview: str,
    conversation_id: str = None
) -> dict:
    """Send push notification for new message"""
    
    title = f"💬 Message de {sender_name}"
    body = message_preview[:100] + ("..." if len(message_preview) > 100 else "")
    url = "/dashboard/messages"
    
    return await send_push_to_user(
        db=db,
        user_id=recipient_id,
        title=title,
        body=body,
        url=url,
        tag=f"message-{sender_name}",
        data={"type": "message", "conversation_id": conversation_id}
    )
