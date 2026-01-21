"""
Authentication API endpoints
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.audit import AuditAction
from app.services.auth_service import auth_service, TokenPair
from app.services.audit_service import AuditService

router = APIRouter()


# ============ Request/Response Schemas ============

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    avatar_url: Optional[str]
    is_active: bool
    is_superuser: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenPair


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


# ============ Dependencies ============

async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dependency to get the current authenticated user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = parts[1]
    user_id = auth_service.verify_access_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")
    
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Dependency to optionally get the current user (for public endpoints)"""
    if not authorization:
        return None
    
    try:
        return await get_current_user(authorization, db)
    except HTTPException:
        return None


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None


# ============ Endpoints ============

@router.post("/register", response_model=AuthResponse)
async def register(
    request: Request,
    data: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a new user"""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate password
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Create user
    user = User(
        email=data.email,
        password_hash=auth_service.hash_password(data.password),
        name=data.name,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Log the registration
    audit = AuditService(db)
    await audit.log_auth(
        action=AuditAction.USER_REGISTER,
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()
    
    # Create tokens
    tokens = auth_service.create_token_pair(user.id)
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
        ),
        tokens=tokens,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    data: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password"""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()
    
    if not user or not auth_service.verify_password(data.password, user.password_hash):
        # Log failed attempt
        audit = AuditService(db)
        await audit.log_auth(
            action=AuditAction.USER_LOGIN,
            user_id=data.email,  # Use email since we don't have user_id
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            success=False,
            failure_reason="Invalid credentials",
        )
        await db.commit()
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=401, detail="User is inactive")
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    
    # Log successful login
    audit = AuditService(db)
    await audit.log_auth(
        action=AuditAction.USER_LOGIN,
        user_id=user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()
    
    # Create tokens
    tokens = auth_service.create_token_pair(user.id)
    
    return AuthResponse(
        user=UserResponse(
            id=user.id,
            email=user.email,
            name=user.name,
            avatar_url=user.avatar_url,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            created_at=user.created_at,
        ),
        tokens=tokens,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token"""
    user_id = auth_service.verify_refresh_token(data.refresh_token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # Verify user still exists and is active
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    # Create new token pair
    tokens = auth_service.create_token_pair(user.id)
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout the current user (logs the event)"""
    audit = AuditService(db)
    await audit.log_auth(
        action=AuditAction.USER_LOGOUT,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()
    
    return {"message": "Logged out successfully"}


@router.put("/me", response_model=UserResponse)
async def update_me(
    name: Optional[str] = None,
    avatar_url: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile"""
    if name:
        current_user.name = name
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    
    await db.commit()
    await db.refresh(current_user)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_superuser=current_user.is_superuser,
        created_at=current_user.created_at,
    )


@router.post("/change-password")
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Change password for current user"""
    if not auth_service.verify_password(current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    if len(new_password) < 8:
        raise HTTPException(status_code=400, detail="New password must be at least 8 characters")
    
    current_user.password_hash = auth_service.hash_password(new_password)
    
    # Log the password change
    audit = AuditService(db)
    await audit.log_auth(
        action=AuditAction.USER_PASSWORD_CHANGE,
        user_id=current_user.id,
        ip_address=get_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    await db.commit()
    
    return {"message": "Password changed successfully"}
