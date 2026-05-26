# src/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_db
from src.models.user import User
from src.models.note import Note
from src.schemas.auth_schema import UserResponse
from src.schemas.note_schema import NoteListResponse
from src.middleware.auth_middleware import get_admin_user
from src.routers.notes import verify_api_version
from typing import List, Optional
from src.services.note_service import NoteService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_api_version), Depends(get_admin_user)]
)

@router.get("/users", response_model=List[UserResponse])
async def list_users(
    top: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).offset(skip).limit(top)
    result = await db.execute(stmt)
    return list(result.scalars().all())

@router.get("/users/{id}", response_model=UserResponse)
async def get_user(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/users/{id}")
async def delete_user(id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(user)
    return {"message": "User deleted successfully."}

@router.get("/notes", response_model=NoteListResponse)
async def list_all_notes(
    request: Request,
    top: int = Query(10, ge=1, le=100),
    skip: int = Query(0, ge=0),
    filter: Optional[str] = Query(None),
    orderby: str = Query("created_at desc"),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_admin_user)
):
    notes, total = await NoteService.list_notes(
        db, admin, top=top, skip=skip, filter_str=filter, orderby=orderby, is_admin=True
    )
    
    next_link = None
    if skip + top < total:
        from urllib.parse import urlencode
        query_params = dict(request.query_params)
        query_params["skip"] = str(skip + top)
        query_string = urlencode(query_params)
        base_url = str(request.url).split('?')[0]
        next_link = f"{base_url}?{query_string}"

    return {"value": notes, "nextLink": next_link}

@router.patch("/users/{id}/role", response_model=UserResponse)
async def change_role(id: str, role_data: dict, db: AsyncSession = Depends(get_db)):
    new_role = role_data.get("role")
    if new_role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    stmt = select(User).where(User.id == id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = new_role
    return user
