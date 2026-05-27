# src/routers/notes.py
import uuid
from fastapi import APIRouter, HTTPException, Query, status, Request, Depends
from typing import Optional, List
from src.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User
from src.middleware.auth_middleware import get_current_user
from src.services.note_service import NoteService
from src.schemas.note_schema import (
    Note as NoteSchema, NoteBase, NoteUpdate, 
    NoteListResponse, NoteBulkResponse
)

SUPPORTED_API_VERSIONS = ["2024-05-25", "2024-05-01"]
DEFAULT_API_VERSION = "2024-05-25"

async def verify_api_version(api_version: Optional[str] = Query(None, alias="api-version")):
    if api_version is None:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MissingApiVersion",
                "message": "The 'api-version' query parameter is required.",
                "availableVersions": SUPPORTED_API_VERSIONS,
                "hint": f"Add ?api-version={DEFAULT_API_VERSION} to your request."
            }
        )
    if api_version not in SUPPORTED_API_VERSIONS:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "UnsupportedApiVersion",
                "message": f"api-version '{api_version}' is not supported.",
                "availableVersions": SUPPORTED_API_VERSIONS,
                "hint": f"Use one of: {', '.join(SUPPORTED_API_VERSIONS)}"
            }
        )
    return api_version

router = APIRouter(
    prefix="/notes", 
    tags=["notes"],
    dependencies=[Depends(verify_api_version), Depends(get_current_user)]
)

@router.get("", response_model=NoteListResponse)
async def list_notes(
    request: Request,
    top: Optional[int] = Query(None, ge=1, le=100),
    skip: Optional[int] = Query(None, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    orderby: str = Query("created_at desc"), 
    filter: Optional[str] = Query(None), 
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    final_top = limit if limit is not None else (top if top is not None else 10)
    
    if page is not None:
        final_skip = (page - 1) * final_top
    elif skip is not None:
        final_skip = skip
    else:
        final_skip = 0

    notes, total = await NoteService.list_notes(
        db, current_user, top=final_top, skip=final_skip, filter_str=filter, search=search, orderby=orderby, is_admin=(current_user.role == "admin")
    )
    
    next_link = None
    if final_skip + final_top < total:
        from urllib.parse import urlencode
        query_params = dict(request.query_params)
        query_params["skip"] = str(final_skip + final_top)
        if "page" in query_params:
            query_params.pop("page")
        query_string = urlencode(query_params)
        base_url = str(request.url).split('?')[0]
        next_link = f"{base_url}?{query_string}"

    return {
        "value": notes,
        "nextLink": next_link
    }

@router.post("", status_code=status.HTTP_201_CREATED, response_model=NoteSchema)
async def create_note(
    note_data: NoteBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await NoteService.create_note(
        db, current_user.id, title=note_data.title, body=note_data.body, tags=note_data.tags
    )

@router.post("/bulk", status_code=status.HTTP_201_CREATED, response_model=NoteBulkResponse)
async def create_notes_bulk(
    notes_data: List[NoteBase],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    created = await NoteService.create_notes_bulk(db, current_user.id, notes_data)
    return {"value": created}

@router.get("/{id}", response_model=NoteSchema)
async def get_note(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = await NoteService.get_note(db, id, current_user, is_admin=(current_user.role == "admin"))
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return note

@router.put("/{id}", response_model=NoteSchema)
async def replace_note(
    id: uuid.UUID, 
    note_data: NoteBase,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = await NoteService.update_note(
        db, id, current_user, note_data.model_dump(), is_admin=(current_user.role == "admin")
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return note

@router.patch("/{id}", response_model=NoteSchema)
async def patch_note(
    id: uuid.UUID, 
    note_data: NoteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    patch_fields = note_data.model_dump(exclude_unset=True)
    # The note_schema.py uses NoteUpdate which maps to snake_case for model_dump by default
    # But let's check if there's any confusion with camelCase in the field names
    note = await NoteService.update_note(
        db, id, current_user, patch_fields, is_admin=(current_user.role == "admin")
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return note

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_note(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    deleted = await NoteService.delete_note(db, id, current_user, is_admin=(current_user.role == "admin"))
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return {"message": f"Note with id {id} deleted successfully."}


@router.post("/{id}/summary", response_model=NoteSchema)
async def generate_summary_for_note(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Attempts to generate or return cached summary; resilient on failures
    note = await NoteService.generate_summary(db, id, current_user, is_admin=(current_user.role == "admin"))
    if note is None:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return note


@router.post("/{id}/auto_tags", response_model=NoteSchema)
async def auto_tag_note(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tags = await NoteService.suggest_tags(db, id, current_user, is_admin=(current_user.role == "admin"))
    if tags is None:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    # Return the updated note
    note = await NoteService.get_note(db, id, current_user, is_admin=(current_user.role == "admin"))
    return note
