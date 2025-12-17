from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from memexia_backend.enums import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile (self)."""

    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)


class UserRoleUpdate(BaseModel):
    """Schema for admin to update user role."""

    role: UserRole


class Token(BaseModel):
    """JWT token response schema."""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Token payload data."""

    username: str


class User(UserBase):
    """User response schema."""

    id: int
    role: str
    is_superuser: bool
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserList(BaseModel):
    """User list item schema (for admin view)."""

    id: int
    email: EmailStr
    username: str
    role: str
    is_superuser: bool
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True
