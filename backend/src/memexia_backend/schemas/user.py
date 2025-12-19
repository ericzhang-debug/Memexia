from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re

from memexia_backend.enums import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""

    email: str
    username: str = Field(..., min_length=3, max_length=50)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Custom email validator that allows .local domains."""
        # Basic email pattern that allows .local domains
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email address')
        return v.lower()


class UserCreate(UserBase):
    """Schema for user registration."""

    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserUpdate(BaseModel):
    """Schema for updating user profile (self)."""

    email: Optional[str] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Custom email validator that allows .local domains."""
        if v is None:
            return v
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email address')
        return v.lower()


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
    email: str
    username: str
    role: str
    is_superuser: bool
    is_active: bool
    is_verified: bool
    created_at: datetime

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Custom email validator that allows .local domains."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email address')
        return v.lower()

    class Config:
        from_attributes = True
