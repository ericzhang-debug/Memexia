"""
User management API routes for administrators.

This module provides REST API endpoints for user management,
accessible only to administrators.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from memexia_backend.database import get_db
from memexia_backend.models import User
from memexia_backend.schemas import UserList, UserRoleUpdate, User as UserSchema
from memexia_backend.enums import Permission, UserRole
from memexia_backend.utils.permissions import require_permission

router = APIRouter(tags=["users"], prefix="/api/v1/users")


@router.get("", response_model=List[UserList])
def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum users to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_READ_ALL)),
):
    """
    List all users (admin only).

    Requires USER_READ_ALL permission.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserList.model_validate(user) for user in users]


@router.get("/{user_id}", response_model=UserSchema)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_READ_ALL)),
):
    """
    Get a specific user by ID (admin only).

    Requires USER_READ_ALL permission.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserSchema.model_validate(user)


@router.patch("/{user_id}/role", response_model=UserSchema)
def update_user_role(
    user_id: int,
    role_update: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_UPDATE_ROLE)),
):
    """
    Update a user's role (admin only).

    Requires USER_UPDATE_ROLE permission.

    Note: Cannot modify superuser accounts or own account.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-modification
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own role",
        )

    # Prevent modification of superusers
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify superuser accounts",
        )

    # Update role
    user.role = role_update.role.value
    db.commit()
    db.refresh(user)

    return UserSchema.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_DELETE)),
):
    """
    Delete a user (admin only).

    Requires USER_DELETE permission.

    Note: Cannot delete superuser accounts or own account.
    This will also delete all the user's knowledge bases.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deletion
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    # Prevent deletion of superusers
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete superuser accounts",
        )

    # Delete user (cascade will delete knowledge bases)
    db.delete(user)
    db.commit()


@router.patch("/{user_id}/activate", response_model=UserSchema)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_UPDATE_ROLE)),
):
    """
    Activate a deactivated user (admin only).
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = True
    db.commit()
    db.refresh(user)

    return UserSchema.model_validate(user)


@router.patch("/{user_id}/deactivate", response_model=UserSchema)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.USER_UPDATE_ROLE)),
):
    """
    Deactivate a user (admin only).

    Deactivated users cannot log in.
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent self-deactivation
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    # Prevent deactivation of superusers
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate superuser accounts",
        )

    user.is_active = False
    db.commit()
    db.refresh(user)

    return UserSchema.model_validate(user)
