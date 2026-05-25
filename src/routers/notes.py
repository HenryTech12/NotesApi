# src/routers/notes.py
from fastapi import APIRouter, HTTPException, Query, status, Request, Depends, Response
from typing import Optional, List
from src.utils.store import store
from src.schemas.note_schema import (
    Note, NoteBase, NoteUpdate, 
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
    dependencies=[Depends(verify_api_version)]
)

@router.get("", response_model=NoteListResponse)
async def list_notes(
    request: Request,
    top: Optional[int] = Query(None, ge=1, le=100),
    skip: Optional[int] = Query(None, ge=0),
    limit: Optional[int] = Query(None, ge=1, le=100),
    page: Optional[int] = Query(None, ge=1),
    orderby: str = Query("createdAt desc"), # Azure uses space-separated desc/asc
    filter: Optional[str] = Query(None), # e.g. "tag eq 'work'"
    search: Optional[str] = None
):
    # Resolve pagination aliases
    # Priority: limit/page (Bonus Challenge) > top/skip (Azure)
    # This ensures the bonus features work even if the primary params are present
    final_top = limit if limit is not None else (top if top is not None else 10)
    
    if page is not None:
        final_skip = (page - 1) * final_top
    elif skip is not None:
        final_skip = skip
    else:
        final_skip = 0

    notes = store.find_all()

    # Simple filter implementation (tag eq 'val')
    if filter:
        # Improved regex or more flexible parsing would be better, but keeping it simple/robust
        import re
        match = re.search(r"tag eq ['\"](.+?)['\"]", filter, re.IGNORECASE)
        if match:
            tag_val = match.group(1)
            notes = [n for n in notes if any(t.lower() == tag_val.lower() for t in n["tags"])]
        elif "tag eq " in filter.lower():
            # Handle unquoted case
            tag_val = filter.lower().split("tag eq ")[1].strip()
            notes = [n for n in notes if any(t.lower() == tag_val.lower() for t in n["tags"])]

    # Search by title or body
    if search:
        search_lower = search.lower()
        notes = [n for n in notes if search_lower in n["title"].lower() or search_lower in n["body"].lower()]

    # Sorting (orderby=field [asc|desc])
    if orderby:
        parts = orderby.split()
        sort_field = parts[0]
        reverse = parts[1].lower() == "desc" if len(parts) > 1 else False
        notes.sort(key=lambda x: x.get(sort_field, ""), reverse=reverse)

    total = len(notes)
    data = notes[final_skip : final_skip + final_top]
    
    # nextLink generation following Azure pattern (absolute URL)
    next_link = None
    if final_skip + final_top < total:
        # Reconstruct URL with current params
        from urllib.parse import urlencode
        query_params = dict(request.query_params)
        
        # Azure guidelines prefer $skip for continuation
        query_params["skip"] = str(final_skip + final_top)
        
        # Remove page alias if present to avoid confusion in nextLink
        if "page" in query_params:
            query_params.pop("page")
            
        query_string = urlencode(query_params)
        
        # request.url includes the scheme, host, and port correctly
        base_url = str(request.url).split('?')[0]
        next_link = f"{base_url}?{query_string}"

    return {
        "value": data,
        "nextLink": next_link
    }

@router.post("", status_code=status.HTTP_201_CREATED, response_model=Note)
async def create_note(
    note_data: NoteBase
):
    note = store.create(
        title=note_data.title, 
        body=note_data.body, 
        tags=note_data.tags
    )
    return note

@router.post("/bulk", status_code=status.HTTP_201_CREATED, response_model=NoteBulkResponse)
async def create_notes_bulk(
    notes_data: List[NoteBase]
):
    created_notes = []
    for note_data in notes_data:
        note = store.create(
            title=note_data.title,
            body=note_data.body,
            tags=note_data.tags
        )
        created_notes.append(note)
    return {"value": created_notes}

@router.get("/{id}", response_model=Note)
async def get_note(
    id: str
):
    note = store.find_by_id(id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return note

@router.put("/{id}", response_model=Note)
async def replace_note(
    id: str, 
    note_data: NoteBase
):
    note = store.replace(
        id, 
        title=note_data.title, 
        body=note_data.body, 
        tags=note_data.tags
    )
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return note

@router.patch("/{id}", response_model=Note)
async def patch_note(
    id: str, 
    note_data: NoteUpdate
):
    patch_fields = note_data.model_dump(exclude_unset=True)
    
    note = store.patch(id, patch_fields)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    return note

@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_note(
    id: str
):
    # The brief explicitly requires 200 OK for deletes.
    # We first check if the resource exists to satisfy strict 404 requirements for non-existent IDs.
    deleted = store.remove(id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Note with id {id} not found.")
    
    return {"message": f"Note with id {id} deleted successfully."}
