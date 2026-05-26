# src/schemas/auth_schema.py
from pydantic import BaseModel, EmailStr, Field, field_validator
import re
import uuid
from datetime import datetime
from typing import Optional

PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"

class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., max_length=255)
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "Password must be at least 8 characters long, "
                "include uppercase, lowercase, a digit, and a special character."
            )
        return v

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "Bearer"
    expiresIn: int
    refreshToken: str

class RefreshRequest(BaseModel):
    refreshToken: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    resetToken: str
    newPassword: str

    @field_validator("newPassword")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.match(PASSWORD_REGEX, v):
            raise ValueError(
                "Password must be at least 8 characters long, "
                "include uppercase, lowercase, a digit, and a special character."
            )
        return v

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
        alias_generator = lambda s: "".join(
            word.capitalize() if i > 0 else word for i, word in enumerate(s.split("_"))
        )
        populate_by_name = True

    @field_validator("created_at", mode="before")
    @classmethod
    def format_datetime(cls, v):
        if isinstance(v, datetime):
            return v.isoformat()
        return v
