# src/schemas/note_schema.py
from pydantic import BaseModel, Field, field_validator, model_validator
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

    @model_validator(mode="after")
    def check_at_least_one_field(self) -> "NoteUpdate":
        if self.title is None and self.body is None and self.tags is None:
            raise ValueError("At least one of [title, body, tags] must be provided.")
        return self

class Note(NoteBase):
    id: str
    createdAt: str
    updatedAt: str

# Response Shapes following Azure guidelines (Direct resource or 'value' for collections)
# Note: x-ms-request-id is handled in middleware headers

class NoteListResponse(BaseModel):
    value: List[Note]
    nextLink: Optional[str] = None

class NoteBulkResponse(BaseModel):
    value: List[Note]

# Error schemas matching Azure standard
class InnerError(BaseModel):
    code: Optional[str] = None
    innererror: Optional["InnerError"] = None

class AzureErrorDetail(BaseModel):
    code: str
    message: str
    target: Optional[str] = None
    details: Optional[List["AzureErrorDetail"]] = None
    innererror: Optional[InnerError] = None

class AzureErrorResponse(BaseModel):
    error: AzureErrorDetail

AzureErrorDetail.model_rebuild()
InnerError.model_rebuild()
