# src/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.user import User
from src.schemas.auth_schema import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, ForgotPasswordRequest,
    ResetPasswordRequest, UserResponse
)
from src.services.auth_service import (
    hash_password, verify_password, create_tokens,
    refresh_access_token, revoke_refresh_token,
    create_reset_token, reset_password
)
from src.routers.notes import verify_api_version
from src.middleware.auth_middleware import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(verify_api_version)]
)

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check uniqueness
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "EmailAlreadyExists", "message": "A user with this email already exists."}
        )
    
    new_user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        role="user"
    )
    db.add(new_user)
    await db.flush()
    return new_user

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Timing attack protection
    dummy_hash = "$2b$12$LQv3c1yqBWVHxkd0LqCFS.Djg5yP6Kx.LIDv6BfXp3kG6C.fV0G5y"
    
    if not user or not verify_password(request.password, user.password_hash):
        # Still verify if user exists to consume time
        if not user:
            verify_password(request.password, dummy_hash)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "InvalidCredentials", "message": "Invalid email or password."}
        )
    
    return await create_tokens(db, user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await refresh_access_token(db, request.refreshToken)

@router.post("/logout")
async def logout(request: RefreshRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await revoke_refresh_token(db, request.refreshToken)
    return {"message": "Logged out successfully."}

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == request.email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    reset_token = None
    if user:
        reset_token = await create_reset_token(db, user)
        
    return {
        "message": "If that email exists, a reset token has been issued.",
        "resetToken": reset_token
    }

@router.post("/reset-password")
async def reset_password_route(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await reset_password(db, request.resetToken, request.newPassword)
    return {"message": "Password reset successfully."}
