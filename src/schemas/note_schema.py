# src/schemas/note_schema.py
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=150)
    body: str = Field(..., min_length=3, max_length=5000)
    tags: Optional[List[str]] = []

    @field_validator("title", "body")
    @classmethod
    def trim_strings(cls, v: str) -> str:
        return v.strip()

class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=150)
    body: Optional[str] = Field(None, min_length=3, max_length=5000)
    tags: Optional[List[str]] = None

    @field_validator("title", "body")
    @classmethod
    def trim_strings(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip()
        return v

class Note(NoteBase):
    id: str
    createdAt: str
    updatedAt: str

# Response Shapes
class SuccessResponse(BaseModel):
    success: bool = True
    data: dict

class NoteListMeta(BaseModel):
    total: int
    page: int
    limit: int
    totalPages: int
    hasNextPage: bool
    hasPrevPage: bool

class NoteListResponse(BaseModel):
    success: bool = True
    data: List[Note]
    meta: NoteListMeta

class ErrorDetail(BaseModel):
    field: str
    message: str

class ErrorResponse(BaseModel):
    success: bool = False
    error: dict # {message: str, details: optional list}
