"""
Auth schemas — Pydantic models for request/response validation.

Separation of concerns:
- Request schemas: validate what comes IN (strict)
- Response schemas: shape what goes OUT (explicit fields only)
- Never return hashed_password, provider_id, or internal fields
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


# ── Request Schemas ───────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Enforce password policy.
        Minimum requirements — adjust to your security policy.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) == 0:
            return None
        return v.strip() if v else v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Response Schemas ──────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """
    Returned after successful login/register/OAuth.
    access_token: short-lived JWT — send as Bearer on every API request
    refresh_token: long-lived random token — use to get new access token
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds


class UserResponse(BaseModel):
    """
    Safe user representation — never includes sensitive fields.
    """
    id: UUID
    email: str
    full_name: Optional[str]
    picture: Optional[str]
    provider: str
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True