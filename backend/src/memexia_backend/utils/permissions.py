"""
Permission checking utilities.

This module provides a flexible permission checking system using the Strategy pattern.
The current implementation uses static role-permission mappings, but can be easily
replaced with database-driven RBAC by implementing a new PermissionChecker.

Usage:
    from memexia_backend.utils.permissions import require_permission, require_any_permission

    @router.get("/admin")
    def admin_endpoint(user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))):
        ...

    @router.get("/knowledge-bases/{kb_id}")
    def get_kb(
        kb_id: str,
        user: Optional[User] = Depends(get_current_user_optional),
        _: bool = Depends(require_kb_access(kb_id))
    ):
        ...
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable, Any

from fastapi import Depends, HTTPException, status

from memexia_backend.enums import Permission, UserRole, ROLE_PERMISSIONS


class PermissionChecker(ABC):
    """
    Abstract base class for permission checking.

    Implement this interface to create custom permission checking strategies
    (e.g., database-driven RBAC).
    """

    @abstractmethod
    def has_permission(self, user: Any, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        pass

    @abstractmethod
    def get_user_permissions(self, user: Any) -> set[Permission]:
        """Get all permissions for a user."""
        pass


class StaticPermissionChecker(PermissionChecker):
    """
    Permission checker using static role-permission mappings.

    This is the default implementation that uses the ROLE_PERMISSIONS dict.
    """

    def has_permission(self, user: Any, permission: Permission) -> bool:
        """Check if user's role includes the specified permission."""
        if user is None:
            return False

        user_role = getattr(user, "role", None)
        if user_role is None:
            return False

        try:
            role = UserRole(user_role)
            return permission in ROLE_PERMISSIONS.get(role, set())
        except ValueError:
            return False

    def get_user_permissions(self, user: Any) -> set[Permission]:
        """Get all permissions based on user's role."""
        if user is None:
            return set()

        user_role = getattr(user, "role", None)
        if user_role is None:
            return set()

        try:
            role = UserRole(user_role)
            return ROLE_PERMISSIONS.get(role, set())
        except ValueError:
            return set()


# Global permission checker instance
# Replace this with DatabasePermissionChecker for full RBAC support
_permission_checker: PermissionChecker = StaticPermissionChecker()


def get_permission_checker() -> PermissionChecker:
    """Get the current permission checker instance."""
    return _permission_checker


def set_permission_checker(checker: PermissionChecker) -> None:
    """
    Set a custom permission checker.

    Use this to switch to database-driven RBAC:
        set_permission_checker(DatabasePermissionChecker(db))
    """
    global _permission_checker
    _permission_checker = checker


def check_permission(user: Any, permission: Permission) -> bool:
    """Check if a user has a specific permission."""
    return _permission_checker.has_permission(user, permission)


def check_any_permission(user: Any, permissions: list[Permission]) -> bool:
    """Check if a user has any of the specified permissions."""
    return any(_permission_checker.has_permission(user, p) for p in permissions)


def check_all_permissions(user: Any, permissions: list[Permission]) -> bool:
    """Check if a user has all of the specified permissions."""
    return all(_permission_checker.has_permission(user, p) for p in permissions)


# FastAPI dependency factories


def require_permission(permission: Permission) -> Callable:
    """
    Create a FastAPI dependency that requires a specific permission.

    Usage:
        @router.get("/admin")
        def admin_endpoint(user: User = Depends(require_permission(Permission.SYSTEM_ADMIN))):
            ...
    """
    from memexia_backend.routers.v1.auth import get_current_user

    def dependency(current_user=Depends(get_current_user)):
        if not check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return current_user

    return dependency


def require_any_permission(permissions: list[Permission]) -> Callable:
    """
    Create a FastAPI dependency that requires any of the specified permissions.
    """
    from memexia_backend.routers.v1.auth import get_current_user

    def dependency(current_user=Depends(get_current_user)):
        if not check_any_permission(current_user, permissions):
            permission_names = [p.value for p in permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires one of {permission_names}",
            )
        return current_user

    return dependency


def require_role(role: UserRole) -> Callable:
    """
    Create a FastAPI dependency that requires a specific role.

    Usage:
        @router.get("/admin")
        def admin_endpoint(user: User = Depends(require_role(UserRole.ADMIN))):
            ...
    """
    from memexia_backend.routers.v1.auth import get_current_user

    def dependency(current_user=Depends(get_current_user)):
        user_role = getattr(current_user, "role", None)
        if user_role != role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}",
            )
        return current_user

    return dependency


def get_current_user_optional() -> Callable:
    """
    Get current user if authenticated, None otherwise.

    This is useful for endpoints that allow both authenticated and guest access.
    """
    from memexia_backend.routers.v1.auth import oauth2_scheme, get_user
    from memexia_backend.database import get_db
    from memexia_backend.config import settings
    from jose import JWTError, jwt
    from sqlalchemy.orm import Session

    def dependency(
        token: Optional[str] = Depends(oauth2_scheme),
        db: Session = Depends(get_db),
    ):
        if token is None:
            return None
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: str | None = payload.get("sub")
            if username is None:
                return None
            return get_user(db, username=username)
        except JWTError:
            return None

    return dependency
