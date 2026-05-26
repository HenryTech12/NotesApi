# src/services/auth_service.py
import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User, RefreshToken, PasswordResetToken
from src.schemas.auth_schema import TokenResponse
from fastapi import HTTPException, status

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET must be at least 32 characters long")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", 60))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def create_tokens(db: AsyncSession, user: User) -> TokenResponse:
    # Access token
    access_token = create_access_token({
        "sub": str(user.id),
        "email": user.email,
        "role": user.role
    })
    
    # Refresh token (opaque)
    raw_refresh_token = secrets.token_urlsafe(32)
    hashed_refresh_token = hash_token(raw_refresh_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    db_refresh_token = RefreshToken(
        user_id=user.id,
        token_hash=hashed_refresh_token,
        expires_at=expires_at
    )
    db.add(db_refresh_token)
    await db.flush()
    
    return TokenResponse(
        accessToken=access_token,
        expiresIn=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refreshToken=raw_refresh_token
    )

async def refresh_access_token(db: AsyncSession, refresh_token: str) -> TokenResponse:
    hashed_token = hash_token(refresh_token)
    stmt = select(RefreshToken).where(
        RefreshToken.token_hash == hashed_token,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "InvalidRefreshToken", "message": "Invalid or expired refresh token."}
        )
    
    # Rotate token: revoke old one
    db_token.revoked = True
    
    # Get user
    stmt_user = select(User).where(User.id == db_token.user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalar_one()
    
    # Create new pair
    return await create_tokens(db, user)

async def revoke_refresh_token(db: AsyncSession, refresh_token: str):
    hashed_token = hash_token(refresh_token)
    stmt = select(RefreshToken).where(RefreshToken.token_hash == hashed_token)
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()
    if db_token:
        db_token.revoked = True

async def create_reset_token(db: AsyncSession, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    hashed_token = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    
    db_token = PasswordResetToken(
        user_id=user.id,
        token_hash=hashed_token,
        expires_at=expires_at
    )
    db.add(db_token)
    return raw_token

async def reset_password(db: AsyncSession, reset_token: str, new_password: str):
    hashed_token = hash_token(reset_token)
    stmt = select(PasswordResetToken).where(
        PasswordResetToken.token_hash == hashed_token,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.now(timezone.utc)
    )
    result = await db.execute(stmt)
    db_token = result.scalar_one_or_none()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "InvalidResetToken", "message": "Invalid or expired reset token."}
        )
    
    # Get user
    stmt_user = select(User).where(User.id == db_token.user_id)
    result_user = await db.execute(stmt_user)
    user = result_user.scalar_one()
    
    # Update password
    user.password_hash = hash_password(new_password)
    db_token.used = True
    
    # Revoke ALL refresh tokens
    stmt_revoke = select(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked == False)
    result_revoke = await db.execute(stmt_revoke)
    for rt in result_revoke.scalars():
        rt.revoked = True
