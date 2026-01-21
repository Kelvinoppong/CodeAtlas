"""
Authentication Service - JWT tokens and password hashing
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import hashlib
import hmac

import jwt
from pydantic import BaseModel

from app.core.config import settings


class TokenPayload(BaseModel):
    """JWT token payload"""
    sub: str  # user_id
    exp: datetime
    iat: datetime
    type: str  # access or refresh


class TokenPair(BaseModel):
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthService:
    """Authentication service for JWT and password handling"""
    
    # Token settings
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    ALGORITHM = "HS256"
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or settings.SECRET_KEY or secrets.token_urlsafe(32)
    
    # ============ Password Hashing ============
    
    def hash_password(self, password: str) -> str:
        """Hash a password using PBKDF2-HMAC-SHA256"""
        salt = secrets.token_hex(16)
        iterations = 100000
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations,
        )
        return f"pbkdf2:sha256:{iterations}${salt}${hash_bytes.hex()}"
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against its hash"""
        try:
            parts = password_hash.split("$")
            if len(parts) != 3:
                return False
            
            header, salt, stored_hash = parts
            header_parts = header.split(":")
            if len(header_parts) != 3:
                return False
            
            _, _, iterations_str = header_parts
            iterations = int(iterations_str)
            
            computed_hash = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                iterations,
            )
            
            return hmac.compare_digest(computed_hash.hex(), stored_hash)
        except Exception:
            return False
    
    # ============ JWT Tokens ============
    
    def create_access_token(self, user_id: str) -> str:
        """Create a new access token"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "access",
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create a new refresh token"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": now,
            "type": "refresh",
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.ALGORITHM)
    
    def create_token_pair(self, user_id: str) -> TokenPair:
        """Create both access and refresh tokens"""
        return TokenPair(
            access_token=self.create_access_token(user_id),
            refresh_token=self.create_refresh_token(user_id),
            token_type="bearer",
            expires_in=self.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
    
    def decode_token(self, token: str) -> Optional[TokenPayload]:
        """Decode and validate a JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM],
            )
            return TokenPayload(**payload)
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def verify_access_token(self, token: str) -> Optional[str]:
        """Verify an access token and return the user_id"""
        payload = self.decode_token(token)
        if payload and payload.type == "access":
            return payload.sub
        return None
    
    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Verify a refresh token and return the user_id"""
        payload = self.decode_token(token)
        if payload and payload.type == "refresh":
            return payload.sub
        return None


# Global instance
auth_service = AuthService()
