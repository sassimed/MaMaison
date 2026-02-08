from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from utils.auth import verify_token
from models.user import User, UserRole

# This will be set by server.py at startup
_db: AsyncIOMotorDatabase = None

def set_database(database: AsyncIOMotorDatabase):
    """Set the database instance (called from server.py)"""
    global _db
    _db = database

def get_db() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if _db is None:
        raise RuntimeError("Database not initialized")
    return _db

# Security
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: AsyncIOMotorDatabase = Depends(get_db)) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token, "access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    
    # Fetch user from database
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user_doc is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    # Convert datetime strings back to datetime objects
    if isinstance(user_doc.get('created_at'), str):
        from datetime import datetime
        user_doc['created_at'] = datetime.fromisoformat(user_doc['created_at'])
    if isinstance(user_doc.get('updated_at'), str):
        from datetime import datetime
        user_doc['updated_at'] = datetime.fromisoformat(user_doc['updated_at'])
    
    return User(**user_doc)

def require_role(allowed_roles: List[UserRole]):
    """Dependency to check if user has required role"""
    async def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user
    return role_checker
