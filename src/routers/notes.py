# src/routers/notes.py
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional, List
from src.utils.store import store
from src.schemas.note_schema import (
    Note, NoteBase, NoteUpdate, 
    NoteListResponse, SuccessResponse
)
import math

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("", response_model=NoteListResponse)
async def list_notes(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    sort: str = Query("createdAt", regex="^(createdAt|updatedAt|title)$"),
    order: str = Query("desc", regex="^(asc|desc)$"),
    tag: Optional[str] = None,
    search: Optional[str] = None
):
    notes = store.find_all()

    # Filtering by tag
    if tag:
        tag_lower = tag.lower()
        notes = [n for n in notes if any(t.lower() == tag_lower for t in n["tags"])]

    # Search by title or body
    if search:
        search_lower = search.lower()
        notes = [n for n in notes if search_lower in n["title"].lower() or search_lower in n["body"].lower()]

    # Sorting
    reverse = (order == "desc")
    notes.sort(key=lambda x: x[sort], reverse=reverse)

    # Pagination
    total = len(notes)
    total_pages = math.ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    end = start + limit
    
    data = notes[start:end]

    return {
        "success": True,
        "data": data,
        "meta": {
            "total": total,
            "page": page,
            "limit": limit,
            "totalPages": total_pages,
            "hasNextPage": page < total_pages,
            "hasPrevPage": page > 1
        }
    }

@router.post("", status_code=status.HTTP_201_CREATED, response_model=SuccessResponse)
async def create_note(note_data: NoteBase):
    note = store.create(
        title=note_data.title, 
        body=note_data.body, 
        tags=note_data.tags
    )
    return {"success": True, "data": note}

@router.get("/{note_id}", response_model=SuccessResponse)
async def get_note(note_id: str):
    note = store.find_by_id(note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found.")
    return {"success": True, "data": note}

@router.put("/{note_id}", response_model=SuccessResponse)
async def replace_note(note_id: str, note_data: NoteBase):
    note = store.replace(
        note_id, 
        title=note_data.title, 
        body=note_data.body, 
        tags=note_data.tags
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found.")
    return {"success": True, "data": note}

@router.patch("/{note_id}", response_model=SuccessResponse)
async def patch_note(note_id: str, note_data: NoteUpdate):
    # Ensure at least one field is provided
    patch_fields = note_data.model_dump(exclude_unset=True)
    if not patch_fields:
        raise HTTPException(status_code=422, detail="At least one of [title, body, tags] must be provided.")
    
    note = store.patch(note_id, patch_fields)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found.")
    return {"success": True, "data": note}

@router.delete("/{note_id}", response_model=SuccessResponse)
async def delete_note(note_id: str):
    success = store.remove(note_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Note with id {note_id} not found.")
    return {"success": True, "data": {"id": note_id}}
