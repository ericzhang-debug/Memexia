"""
Knowledge Base API routes.

This module provides REST API endpoints for knowledge base management.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from memexia_backend.database import get_db
from memexia_backend.models import User
from memexia_backend.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseCopy,
    KnowledgeBaseResponse,
    KnowledgeBaseListItem,
    PaginatedKnowledgeBases,
)
from memexia_backend.services.knowledge_base_service import knowledge_base_service
from memexia_backend.routers.v1.auth import get_current_user
from memexia_backend.enums import Permission
from memexia_backend.utils.permissions import require_permission

router = APIRouter(tags=["knowledge-bases"], prefix="/api/v1/knowledge-bases")


@router.get("", response_model=PaginatedKnowledgeBases)
def list_knowledge_bases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    mine_only: bool = Query(False, description="Only show my knowledge bases"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = None,
):
    """
    List knowledge bases.

    - **Guests**: Only see public knowledge bases
    - **Users**: See their own + public knowledge bases
    - **Admins**: See all knowledge bases
    """
    items, total = knowledge_base_service.get_list(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        owner_only=mine_only,
    )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedKnowledgeBases(
        items=[KnowledgeBaseListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/my", response_model=PaginatedKnowledgeBases)
def list_my_knowledge_bases(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List current user's knowledge bases only.

    Requires authentication.
    """
    items, total = knowledge_base_service.get_list(
        db=db,
        user=current_user,
        page=page,
        page_size=page_size,
        owner_only=True,
    )

    total_pages = (total + page_size - 1) // page_size

    return PaginatedKnowledgeBases(
        items=[KnowledgeBaseListItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.KB_CREATE)),
):
    """
    Create a new knowledge base.

    Requires authentication and KB_CREATE permission.
    """
    kb = knowledge_base_service.create(db=db, kb_data=kb_data, owner=current_user)
    return KnowledgeBaseResponse.model_validate(kb)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = None,
):
    """
    Get a specific knowledge base.

    Access control:
    - Public knowledge bases are accessible to everyone
    - Private knowledge bases are only accessible to owners and admins
    """
    kb = knowledge_base_service.get_by_id(db=db, kb_id=kb_id, user=current_user)

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found or access denied",
        )

    return KnowledgeBaseResponse.model_validate(kb)


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    kb_id: str,
    update_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update a knowledge base.

    Only owners and admins can update knowledge bases.
    """
    kb = knowledge_base_service.get_by_id(db=db, kb_id=kb_id, user=current_user)

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    if not knowledge_base_service.can_modify(kb, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to modify this knowledge base",
        )

    updated_kb = knowledge_base_service.update(db=db, kb=kb, update_data=update_data)
    return KnowledgeBaseResponse.model_validate(updated_kb)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    kb_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a knowledge base.

    Only owners and admins can delete knowledge bases.
    """
    kb = knowledge_base_service.get_by_id(db=db, kb_id=kb_id, user=current_user)

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    if not knowledge_base_service.can_delete(kb, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this knowledge base",
        )

    knowledge_base_service.delete(db=db, kb=kb)


@router.post("/{kb_id}/copy", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def copy_knowledge_base(
    kb_id: str,
    copy_data: KnowledgeBaseCopy,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.KB_COPY_PUBLIC)),
):
    """
    Copy a public knowledge base.

    Creates a private copy of the specified public knowledge base
    owned by the current user.
    """
    # Get the source knowledge base
    kb = knowledge_base_service.get_by_id(db=db, kb_id=kb_id, user=current_user)

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    if not kb.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Can only copy public knowledge bases",
        )

    new_kb = knowledge_base_service.copy(
        db=db,
        source_kb=kb,
        new_owner=current_user,
        new_name=copy_data.new_name,
    )

    return KnowledgeBaseResponse.model_validate(new_kb)
