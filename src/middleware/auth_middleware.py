# src/middleware/auth_middleware.py
import os
import uuid
from fastapi import Request, HTTPException, status, Depends
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.user import User

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "Unauthorized", "message": "Missing or invalid authorization header."},
            headers={"x-ms-error-code": "Unauthorized"}
        )
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "Unauthorized", "message": "Invalid token payload."},
                headers={"x-ms-error-code": "Unauthorized"}
            )
        user_id = uuid.UUID(user_id_str)
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "Unauthorized", "message": "Token expired or invalid."},
            headers={"x-ms-error-code": "Unauthorized"}
        )
        
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "Unauthorized", "message": "User not found."},
            headers={"x-ms-error-code": "Unauthorized"}
        )
    
    if user.is_flagged:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "AccountSuspended", "message": "Your account has been flagged and suspended. Please contact support."},
            headers={"x-ms-error-code": "Forbidden"}
        )
    
    request.state.user = user
    return user

async def get_admin_user(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "Forbidden", "message": "Admin role required."},
            headers={"x-ms-error-code": "Forbidden"}
        )
    return user
