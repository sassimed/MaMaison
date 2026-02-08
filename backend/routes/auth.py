from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.user import UserCreate, User, UserInDB, Token, TokenData, UserRole
from utils.auth import hash_password, verify_password, create_access_token, create_refresh_token, verify_token
from utils.dependencies import get_db, get_current_user
from services.email_service import send_verification_email, send_password_reset_email
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
import secrets
import logging

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = logging.getLogger(__name__)

class LoginRequest(BaseModel):
    email: str
    password: str

class RefreshRequest(BaseModel):
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

class VerifyEmailRequest(BaseModel):
    token: str

class ResendVerificationRequest(BaseModel):
    email: EmailStr


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, background_tasks: BackgroundTasks, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Register a new user and send verification email"""
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_dict = user_data.model_dump()
    hashed_password = hash_password(user_dict.pop("password"))
    
    user_obj = User(**user_dict)
    user_in_db = UserInDB(**user_obj.model_dump(), hashed_password=hashed_password)
    
    # Generate verification token
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    # Convert to dict and serialize datetime
    doc = user_in_db.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    doc['is_email_verified'] = False
    doc['verification_token'] = verification_token
    doc['verification_expires'] = verification_expires.isoformat()
    
    await db.users.insert_one(doc)
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        user_obj.email,
        user_obj.full_name,
        verification_token
    )
    
    logger.info(f"User registered: {user_obj.email}")
    
    return {
        "message": "Inscription réussie ! Un email de confirmation a été envoyé à votre adresse.",
        "email": user_obj.email,
        "requires_verification": True
    }


@router.post("/verify-email")
async def verify_email(request: VerifyEmailRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Verify user email with token"""
    user_doc = await db.users.find_one({"verification_token": request.token}, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de vérification invalide"
        )
    
    # Check if token is expired
    expires = datetime.fromisoformat(user_doc['verification_expires'])
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le token de vérification a expiré. Veuillez demander un nouveau lien."
        )
    
    # Update user as verified
    await db.users.update_one(
        {"verification_token": request.token},
        {
            "$set": {
                "is_email_verified": True,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$unset": {
                "verification_token": "",
                "verification_expires": ""
            }
        }
    )
    
    logger.info(f"Email verified for user: {user_doc['email']}")
    
    return {"message": "Email vérifié avec succès ! Vous pouvez maintenant vous connecter."}


@router.post("/resend-verification")
async def resend_verification(request: ResendVerificationRequest, background_tasks: BackgroundTasks, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Resend verification email"""
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    if not user_doc:
        # Don't reveal if email exists
        return {"message": "Si cet email existe, un nouveau lien de vérification a été envoyé."}
    
    if user_doc.get('is_email_verified', False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cet email est déjà vérifié"
        )
    
    # Generate new verification token
    verification_token = secrets.token_urlsafe(32)
    verification_expires = datetime.now(timezone.utc) + timedelta(hours=24)
    
    await db.users.update_one(
        {"email": request.email},
        {
            "$set": {
                "verification_token": verification_token,
                "verification_expires": verification_expires.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        request.email,
        user_doc['full_name'],
        verification_token
    )
    
    return {"message": "Si cet email existe, un nouveau lien de vérification a été envoyé."}


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Login and get access token"""
    # Find user
    user_doc = await db.users.find_one({"email": login_data.email}, {"_id": 0})
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    user_in_db = UserInDB(**user_doc)
    
    # Verify password
    if not verify_password(login_data.password, user_in_db.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    
    # Check if user is active
    if not user_in_db.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte utilisateur suspendu"
        )
    
    # Check if email is verified
    if not user_doc.get('is_email_verified', True):  # Default True for existing users
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Veuillez d'abord vérifier votre adresse email. Vérifiez votre boîte de réception."
        )
    
    # Create tokens
    token_data = {"sub": user_in_db.id, "role": user_in_db.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, background_tasks: BackgroundTasks, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Request password reset"""
    user_doc = await db.users.find_one({"email": request.email}, {"_id": 0})
    
    # Always return success to prevent email enumeration
    if not user_doc:
        return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
    
    await db.users.update_one(
        {"email": request.email},
        {
            "$set": {
                "reset_token": reset_token,
                "reset_expires": reset_expires.isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    # Send reset email in background
    background_tasks.add_task(
        send_password_reset_email,
        request.email,
        user_doc['full_name'],
        reset_token
    )
    
    logger.info(f"Password reset requested for: {request.email}")
    
    return {"message": "Si cet email existe, un lien de réinitialisation a été envoyé."}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Reset password with token"""
    user_doc = await db.users.find_one({"reset_token": request.token}, {"_id": 0})
    
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token de réinitialisation invalide"
        )
    
    # Check if token is expired
    expires = datetime.fromisoformat(user_doc['reset_expires'])
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le token de réinitialisation a expiré. Veuillez faire une nouvelle demande."
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le mot de passe doit contenir au moins 6 caractères"
        )
    
    # Hash new password
    hashed_password = hash_password(request.new_password)
    
    # Update password and remove reset token
    await db.users.update_one(
        {"reset_token": request.token},
        {
            "$set": {
                "hashed_password": hashed_password,
                "updated_at": datetime.now(timezone.utc).isoformat()
            },
            "$unset": {
                "reset_token": "",
                "reset_expires": ""
            }
        }
    )
    
    logger.info(f"Password reset completed for: {user_doc['email']}")
    
    return {"message": "Mot de passe réinitialisé avec succès ! Vous pouvez maintenant vous connecter."}


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_data: RefreshRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Refresh access token using refresh token"""
    payload = verify_token(refresh_data.refresh_token, "refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de rafraîchissement invalide"
        )
    
    user_id = payload.get("sub")
    role = payload.get("role")
    
    # Verify user still exists and is active
    user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user_doc or not user_doc.get("is_active"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilisateur non trouvé ou inactif"
        )
    
    # Create new tokens
    token_data = {"sub": user_id, "role": role}
    access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    return Token(access_token=access_token, refresh_token=new_refresh_token)


@router.get("/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


# ==================== GOOGLE AUTH (Your Own OAuth) ====================
import httpx
from fastapi import Response, Cookie, Request
from fastapi.responses import RedirectResponse
from typing import Optional
import os
import uuid

GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

class GoogleCodeRequest(BaseModel):
    code: str
    redirect_uri: str

class SetRoleRequest(BaseModel):
    role: str  # PARTICULIER or PROFESSIONNEL

@router.get("/google/login")
async def google_login(request: Request, redirect_uri: str = None):
    """
    Redirect to Google OAuth consent screen
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS
    """
    if not redirect_uri:
        # Use the origin from the request
        redirect_uri = str(request.base_url).rstrip('/') + "/auth/google/callback"
    
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    url = f"{GOOGLE_AUTH_URL}?" + "&".join(f"{k}={v}" for k, v in params.items())
    return {"auth_url": url}


@router.post("/google/callback")
async def google_callback(
    request: GoogleCodeRequest,
    response: Response,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Exchange authorization code for tokens and user info
    REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    """
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": request.code,
                    "redirect_uri": request.redirect_uri,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Google token error: {token_response.text}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Échec de l'authentification Google"
                )
            
            tokens = token_response.json()
            access_token_google = tokens.get("access_token")
            
            # Get user info
            userinfo_response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token_google}"}
            )
            
            if userinfo_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Impossible de récupérer les informations utilisateur"
                )
            
            google_user = userinfo_response.json()
            
    except httpx.RequestError as e:
        logger.error(f"Google API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service Google indisponible"
        )
    
    email = google_user.get("email")
    name = google_user.get("name")
    picture = google_user.get("picture")
    google_id = google_user.get("id")
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email non fourni par Google"
        )
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": email}, {"_id": 0})
    
    # Generate session token
    session_token = secrets.token_urlsafe(32)
    
    if existing_user:
        # User exists - update and return
        user_id = existing_user.get("id")
        
        # Update user picture if needed
        if picture and not existing_user.get("picture"):
            await db.users.update_one(
                {"id": user_id},
                {"$set": {"picture": picture, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        
        # Store/update session
        await db.user_sessions.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "session_token": session_token,
                    "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            },
            upsert=True
        )
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        # Create JWT tokens
        token_data = {"sub": user_id, "role": existing_user.get("role", "PARTICULIER")}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        logger.info(f"Google user logged in: {email}")
        
        return {
            "status": "existing_user",
            "user": {
                "id": user_id,
                "email": existing_user.get("email"),
                "full_name": existing_user.get("full_name"),
                "role": existing_user.get("role"),
                "picture": existing_user.get("picture") or picture
            },
            "access_token": access_token,
            "refresh_token": refresh_token,
            "needs_role_selection": False
        }
    else:
        # New user - create account
        user_id = str(uuid.uuid4())
        
        new_user = {
            "id": user_id,
            "email": email,
            "full_name": name or email.split("@")[0],
            "phone": "",
            "address": "",
            "role": None,  # Will be set after role selection
            "is_active": True,
            "is_email_verified": True,
            "hashed_password": None,
            "google_id": google_id,
            "picture": picture,
            "loyalty_points": 0,
            "total_spent": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(new_user)
        
        # Store session
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Set cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        logger.info(f"New Google user created: {email}")
        
        return {
            "status": "new_user",
            "user": {
                "id": user_id,
                "email": email,
                "full_name": name,
                "role": None,
                "picture": picture
            },
            "needs_role_selection": True,
            "temp_token": session_token
        }


@router.post("/google/set-role")
async def set_google_user_role(
    request: SetRoleRequest,
    response: Response,
    session_token: Optional[str] = Cookie(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Set role for new Google user (PARTICULIER or PROFESSIONNEL)"""
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session non trouvée"
        )
    
    # Validate role
    if request.role not in ["PARTICULIER", "PROFESSIONNEL"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Type de compte invalide"
        )
    
    # Find session
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide"
        )
    
    # Check expiry
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée"
        )
    
    user_id = session.get("user_id")
    
    # Update user role
    result = await db.users.update_one(
        {"id": user_id},
        {
            "$set": {
                "role": request.role,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    # Get updated user
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    # Create JWT tokens
    token_data = {"sub": user_id, "role": request.role}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    logger.info(f"Google user {user['email']} set role to {request.role}")
    
    return {
        "status": "success",
        "user": {
            "id": user_id,
            "email": user.get("email"),
            "full_name": user.get("full_name"),
            "role": request.role,
            "picture": user.get("picture")
        },
        "access_token": access_token,
        "refresh_token": refresh_token
    }


@router.get("/google/me")
async def get_google_user(
    session_token: Optional[str] = Cookie(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get current Google authenticated user"""
    
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Non authentifié"
        )
    
    # Find session
    session = await db.user_sessions.find_one({"session_token": session_token}, {"_id": 0})
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session invalide"
        )
    
    # Check expiry
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expirée"
        )
    
    user_id = session.get("user_id")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé"
        )
    
    return {
        "id": user.get("id"),
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "role": user.get("role"),
        "picture": user.get("picture"),
        "phone": user.get("phone"),
        "address": user.get("address")
    }


@router.post("/google/logout")
async def google_logout(
    response: Response,
    session_token: Optional[str] = Cookie(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Logout Google user"""
    
    if session_token:
        # Delete session from database
        await db.user_sessions.delete_one({"session_token": session_token})
    
    # Clear cookie
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=True,
        samesite="none"
    )
    
    return {"message": "Déconnexion réussie"}

