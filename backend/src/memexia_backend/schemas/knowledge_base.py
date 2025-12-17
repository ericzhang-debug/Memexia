"""
KnowledgeBase schemas for API request/response validation.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class KnowledgeBaseBase(BaseModel):
    """Base schema with common fields."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class KnowledgeBaseCreate(KnowledgeBaseBase):
    """Schema for creating a new knowledge base."""

    is_public: bool = False
    seed_content: Optional[str] = Field(
        None,
        description="Content for the initial seed node",
        max_length=2000,
    )


class KnowledgeBaseUpdate(BaseModel):
    """Schema for updating a knowledge base."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_public: Optional[bool] = None


class KnowledgeBaseCopy(BaseModel):
    """Schema for copying a public knowledge base."""

    new_name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=100,
        description="Name for the copied knowledge base. Defaults to 'Copy of {original}'",
    )


class KnowledgeBaseResponse(KnowledgeBaseBase):
    """Full knowledge base response schema."""

    id: str
    owner_id: int
    seed_node_id: Optional[str]
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseListItem(BaseModel):
    """Simplified schema for list views."""

    id: str
    name: str
    description: Optional[str]
    owner_id: int
    is_public: bool
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseWithOwner(KnowledgeBaseResponse):
    """Knowledge base response with owner info."""

    owner_username: str


class PaginatedKnowledgeBases(BaseModel):
    """Paginated list of knowledge bases."""

    items: list[KnowledgeBaseListItem]
    total: int
    page: int
    page_size: int
    total_pages: int
