from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.message import Message, MessageCreate, MessageReply, MessageType, Conversation
from models.user import User
from utils.dependencies import get_db, get_current_user
from datetime import datetime, timezone
from typing import List, Optional

router = APIRouter(prefix="/messages", tags=["Messages"])


@router.post("", response_model=Message, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Send a new message to admin team"""
    conversation_id = str(datetime.now(timezone.utc).timestamp()).replace('.', '')
    
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        sender_role=current_user.role,
        subject=message_data.subject,
        content=message_data.content,
        message_type=MessageType.USER_TO_ADMIN,
        related_request_id=message_data.related_request_id
    )
    
    # Convert to dict and serialize datetime
    doc = message.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.messages.insert_one(doc)
    
    return message


@router.get("/conversations", response_model=List[Conversation])
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get user's message conversations"""
    # Aggregate to get conversations
    pipeline = [
        {"$match": {"sender_id": current_user.id}},
        {"$sort": {"created_at": -1}},
        {"$group": {
            "_id": "$conversation_id",
            "subject": {"$first": "$subject"},
            "user_id": {"$first": "$sender_id"},
            "user_name": {"$first": "$sender_name"},
            "last_message_at": {"$first": "$created_at"},
            "messages": {"$push": "$$ROOT"}
        }},
        {"$project": {
            "id": "$_id",
            "subject": 1,
            "user_id": 1,
            "user_name": 1,
            "last_message_at": 1,
            "unread_count": {
                "$size": {
                    "$filter": {
                        "input": "$messages",
                        "cond": {"$and": [
                            {"$eq": ["$$this.is_read", False]},
                            {"$ne": ["$$this.sender_id", current_user.id]}
                        ]}
                    }
                }
            }
        }},
        {"$sort": {"last_message_at": -1}}
    ]
    
    conversations = await db.messages.aggregate(pipeline).to_list(50)
    
    # Convert datetime strings
    for conv in conversations:
        if isinstance(conv.get('last_message_at'), str):
            conv['last_message_at'] = datetime.fromisoformat(conv['last_message_at'])
        conv['is_closed'] = False
    
    return conversations


@router.get("/conversation/{conversation_id}", response_model=List[Message])
async def get_conversation_messages(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get all messages in a conversation"""
    messages = await db.messages.find(
        {"conversation_id": conversation_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    # Mark messages as read
    await db.messages.update_many(
        {
            "conversation_id": conversation_id,
            "sender_id": {"$ne": current_user.id},
            "is_read": False
        },
        {"$set": {"is_read": True}}
    )
    
    # Convert datetime strings
    for msg in messages:
        if isinstance(msg.get('created_at'), str):
            msg['created_at'] = datetime.fromisoformat(msg['created_at'])
    
    return messages


@router.post("/conversation/{conversation_id}/reply", response_model=Message)
async def reply_to_conversation(
    conversation_id: str,
    reply_data: MessageReply,
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Reply to an existing conversation"""
    # Get original conversation
    original = await db.messages.find_one(
        {"conversation_id": conversation_id},
        {"_id": 0}
    )
    
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation non trouvée"
        )
    
    message = Message(
        conversation_id=conversation_id,
        sender_id=current_user.id,
        sender_name=current_user.full_name,
        sender_role=current_user.role,
        subject=f"Re: {original['subject']}",
        content=reply_data.content,
        message_type=MessageType.USER_TO_ADMIN if current_user.role != "ADMIN" else MessageType.ADMIN_TO_USER,
        related_request_id=original.get('related_request_id')
    )
    
    # Convert to dict and serialize datetime
    doc = message.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    await db.messages.insert_one(doc)
    
    return message


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get count of unread messages"""
    count = await db.messages.count_documents({
        "conversation_id": {"$in": await db.messages.distinct("conversation_id", {"sender_id": current_user.id})},
        "sender_id": {"$ne": current_user.id},
        "is_read": False
    })
    
    return {"unread_count": count}
