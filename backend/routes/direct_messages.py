"""
Direct Messaging System - Client <-> Professional communication
"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from models.user import User
from utils.dependencies import get_db, get_current_user

router = APIRouter(prefix="/direct-messages", tags=["Direct Messages"])


# ============ MODELS ============

class DirectMessageCreate(BaseModel):
    """Create a new direct message"""
    content: str
    annonce_id: Optional[str] = None  # Link to announcement


class DirectMessage(BaseModel):
    """Direct message between users"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    sender_id: str
    sender_name: str
    sender_role: str
    sender_avatar: Optional[str] = None
    content: str
    is_read: bool = False
    annonce_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DirectConversation(BaseModel):
    """Conversation between two users"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    participant_1_id: str
    participant_1_name: str
    participant_1_role: str
    participant_2_id: str
    participant_2_name: str
    participant_2_role: str
    annonce_id: Optional[str] = None
    annonce_title: Optional[str] = None
    last_message: Optional[str] = None
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StartConversationRequest(BaseModel):
    """Start a new conversation"""
    recipient_id: str
    initial_message: str
    annonce_id: Optional[str] = None


# ============ HELPER FUNCTIONS ============

async def get_or_create_conversation(
    db: AsyncIOMotorDatabase,
    user1_id: str,
    user1_name: str,
    user1_role: str,
    user2_id: str,
    user2_name: str,
    user2_role: str,
    annonce_id: Optional[str] = None,
    annonce_title: Optional[str] = None
) -> dict:
    """Get existing conversation or create new one"""
    # Find existing conversation between these two users (for the same annonce if specified)
    query = {
        "$or": [
            {"participant_1_id": user1_id, "participant_2_id": user2_id},
            {"participant_1_id": user2_id, "participant_2_id": user1_id}
        ]
    }
    
    if annonce_id:
        query["annonce_id"] = annonce_id
    
    existing = await db.direct_conversations.find_one(query, {"_id": 0})
    
    if existing:
        return existing
    
    # Create new conversation
    conversation = DirectConversation(
        participant_1_id=user1_id,
        participant_1_name=user1_name,
        participant_1_role=user1_role,
        participant_2_id=user2_id,
        participant_2_name=user2_name,
        participant_2_role=user2_role,
        annonce_id=annonce_id,
        annonce_title=annonce_title
    )
    
    doc = conversation.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['last_message_at'] = doc['last_message_at'].isoformat()
    
    await db.direct_conversations.insert_one(doc)
    
    return doc


# ============ API ENDPOINTS ============

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_conversation(
    request: StartConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start a new conversation with another user"""
    # Get recipient info
    recipient = await db.users.find_one(
        {"id": request.recipient_id},
        {"_id": 0, "id": 1, "full_name": 1, "role": 1}
    )
    
    if not recipient:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    
    if recipient["id"] == current_user.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas vous envoyer un message")
    
    # Get annonce info if provided
    annonce_title = None
    if request.annonce_id:
        annonce = await db.annonces.find_one(
            {"id": request.annonce_id},
            {"_id": 0, "title": 1}
        )
        if annonce:
            annonce_title = annonce.get("title")
    
    # Get or create conversation
    conversation = await get_or_create_conversation(
        db=db,
        user1_id=current_user.id,
        user1_name=current_user.full_name,
        user1_role=current_user.role,
        user2_id=recipient["id"],
        user2_name=recipient["full_name"],
        user2_role=recipient["role"],
        annonce_id=request.annonce_id,
        annonce_title=annonce_title
    )
    
    # Create the first message
    message = DirectMessage(
        conversation_id=conversation["id"],
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        sender_role=current_user.role,
        content=request.initial_message,
        annonce_id=request.annonce_id
    )
    
    msg_doc = message.model_dump()
    msg_doc['created_at'] = msg_doc['created_at'].isoformat()
    
    await db.direct_messages.insert_one(msg_doc)
    
    # Update conversation last message
    await db.direct_conversations.update_one(
        {"id": conversation["id"]},
        {
            "$set": {
                "last_message": request.initial_message[:100],
                "last_message_at": msg_doc['created_at']
            }
        }
    )
    
    # Create notification for recipient
    from routes.notifications import create_notification
    
    # Determine link based on whether there's an annonce
    if request.annonce_id:
        notification_link = f"/dashboard/my-annonces/{request.annonce_id}"
    else:
        notification_link = f"/dashboard/messages?conversation={conversation['id']}"
    
    await create_notification(
        db=db,
        user_id=recipient["id"],
        title=f"💬 Message de {current_user.full_name}",
        message=request.initial_message[:100] + ("..." if len(request.initial_message) > 100 else ""),
        notification_type="message",
        link=notification_link,
        data={
            "conversation_id": conversation["id"], 
            "sender_id": current_user.id,
            "annonce_id": request.annonce_id
        }
    )
    
    # Send push notification
    try:
        from services.push_service import send_message_push
        await send_message_push(
            db=db,
            recipient_id=recipient["id"],
            sender_name=current_user.full_name,
            message_preview=request.initial_message,
            conversation_id=conversation["id"]
        )
    except Exception:
        pass  # Push notification is optional
    
    return {
        "conversation_id": conversation["id"],
        "message_id": message.id,
        "status": "success"
    }


@router.get("/conversations")
async def get_my_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all conversations for current user"""
    conversations = await db.direct_conversations.find(
        {
            "$or": [
                {"participant_1_id": current_user.id},
                {"participant_2_id": current_user.id}
            ]
        },
        {"_id": 0}
    ).sort("last_message_at", -1).to_list(50)
    
    # Add unread counts and format for frontend
    result = []
    for conv in conversations:
        # Determine the other participant
        if conv["participant_1_id"] == current_user.id:
            other_id = conv["participant_2_id"]
            other_name = conv["participant_2_name"]
            other_role = conv["participant_2_role"]
        else:
            other_id = conv["participant_1_id"]
            other_name = conv["participant_1_name"]
            other_role = conv["participant_1_role"]
        
        # Count unread messages
        unread_count = await db.direct_messages.count_documents({
            "conversation_id": conv["id"],
            "sender_id": {"$ne": current_user.id},
            "is_read": False
        })
        
        result.append({
            "id": conv["id"],
            "other_user_id": other_id,
            "other_user_name": other_name,
            "other_user_role": other_role,
            "annonce_id": conv.get("annonce_id"),
            "annonce_title": conv.get("annonce_title"),
            "last_message": conv.get("last_message"),
            "last_message_at": conv.get("last_message_at"),
            "unread_count": unread_count,
            "created_at": conv.get("created_at")
        })
    
    return result


@router.get("/conversation/{conversation_id}")
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all messages in a conversation"""
    # Verify user is part of this conversation
    conversation = await db.direct_conversations.find_one(
        {
            "id": conversation_id,
            "$or": [
                {"participant_1_id": current_user.id},
                {"participant_2_id": current_user.id}
            ]
        },
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    # Get messages
    messages = await db.direct_messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(200)
    
    # Mark messages as read
    await db.direct_messages.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": current_user.id},
            "is_read": False
        },
        {"$set": {"is_read": True}}
    )
    
    # Get other participant info
    if conversation["participant_1_id"] == current_user.id:
        other_id = conversation["participant_2_id"]
        other_name = conversation["participant_2_name"]
        other_role = conversation["participant_2_role"]
    else:
        other_id = conversation["participant_1_id"]
        other_name = conversation["participant_1_name"]
        other_role = conversation["participant_1_role"]
    
    return {
        "conversation": {
            "id": conversation_id,
            "other_user_id": other_id,
            "other_user_name": other_name,
            "other_user_role": other_role,
            "annonce_id": conversation.get("annonce_id"),
            "annonce_title": conversation.get("annonce_title")
        },
        "messages": messages
    }


@router.post("/conversation/{conversation_id}/send")
async def send_message(
    conversation_id: str,
    message_data: DirectMessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Send a message in a conversation"""
    # Verify user is part of this conversation
    conversation = await db.direct_conversations.find_one(
        {
            "id": conversation_id,
            "$or": [
                {"participant_1_id": current_user.id},
                {"participant_2_id": current_user.id}
            ]
        },
        {"_id": 0}
    )
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    
    # Create message
    message = DirectMessage(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        sender_role=current_user.role,
        content=message_data.content,
        annonce_id=message_data.annonce_id or conversation.get("annonce_id")
    )
    
    msg_doc = message.model_dump()
    msg_doc['created_at'] = msg_doc['created_at'].isoformat()
    
    await db.direct_messages.insert_one(msg_doc)
    
    # Update conversation
    await db.direct_conversations.update_one(
        {"id": conversation_id},
        {
            "$set": {
                "last_message": message_data.content[:100],
                "last_message_at": msg_doc['created_at']
            }
        }
    )
    
    # Determine recipient
    if conversation["participant_1_id"] == current_user.id:
        recipient_id = conversation["participant_2_id"]
    else:
        recipient_id = conversation["participant_1_id"]
    
    # Determine link based on annonce
    annonce_id = conversation.get("annonce_id")
    if annonce_id:
        notification_link = f"/dashboard/my-annonces/{annonce_id}"
    else:
        notification_link = f"/dashboard/messages?conversation={conversation_id}"
    
    # Create notification
    from routes.notifications import create_notification
    await create_notification(
        db=db,
        user_id=recipient_id,
        title=f"💬 Message de {current_user.full_name}",
        message=message_data.content[:100] + ("..." if len(message_data.content) > 100 else ""),
        notification_type="message",
        link=notification_link,
        data={
            "conversation_id": conversation_id, 
            "sender_id": current_user.id,
            "annonce_id": annonce_id
        }
    )
    
    # Send push notification
    try:
        from services.push_service import send_message_push
        await send_message_push(
            db=db,
            recipient_id=recipient_id,
            sender_name=current_user.full_name,
            message_preview=message_data.content,
            conversation_id=conversation_id
        )
    except Exception:
        pass
    
    return {
        "id": message.id,
        "content": message.content,
        "sender_id": message.sender_id,
        "sender_name": message.sender_name,
        "created_at": msg_doc['created_at'],
        "status": "success"
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get total unread message count"""
    # Get user's conversation IDs
    conversations = await db.direct_conversations.find(
        {
            "$or": [
                {"participant_1_id": current_user.id},
                {"participant_2_id": current_user.id}
            ]
        },
        {"id": 1}
    ).to_list(100)
    
    conv_ids = [c["id"] for c in conversations]
    
    if not conv_ids:
        return {"unread_count": 0}
    
    count = await db.direct_messages.count_documents({
        "conversation_id": {"$in": conv_ids},
        "sender_id": {"$ne": current_user.id},
        "is_read": False
    })
    
    return {"unread_count": count}


@router.get("/by-annonce/{annonce_id}")
async def get_conversation_by_annonce(
    annonce_id: str,
    other_user_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get or check if conversation exists for an annonce"""
    conversation = await db.direct_conversations.find_one(
        {
            "annonce_id": annonce_id,
            "$or": [
                {"participant_1_id": current_user.id, "participant_2_id": other_user_id},
                {"participant_1_id": other_user_id, "participant_2_id": current_user.id}
            ]
        },
        {"_id": 0}
    )
    
    if conversation:
        return {"exists": True, "conversation_id": conversation["id"]}
    
    return {"exists": False, "conversation_id": None}
