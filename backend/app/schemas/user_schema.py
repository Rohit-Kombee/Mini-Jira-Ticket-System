"""User and auth schemas."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserCreateByAdmin(BaseModel):
    """Admin creates a user (developer or qa only)."""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=1)
    role: str = Field(..., pattern="^(developer|qa)$")


class UserUpdateByAdmin(BaseModel):
    """Admin updates user details."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=1)
    role: Optional[str] = Field(None, pattern="^(developer|qa)$")


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Login with email or username. Use 'admin' for default admin (not EmailStr to allow username)."""
    email: str = Field(..., min_length=1, description="Email or username")
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: Optional[int] = None
    email: Optional[str] = None
