"""
Role definitions and role-permission mappings.

This module defines user roles and their associated permissions.
The static mapping can be replaced with database queries for full RBAC support.
"""

from enum import Enum
from typing import Set

from .permissions import Permission


class UserRole(str, Enum):
    """User roles in the system."""

    ADMIN = "admin"
    USER = "user"


# Role-Permission mapping
# This static mapping can be migrated to a database table for dynamic RBAC
ROLE_PERMISSIONS: dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # Admin has all permissions
        Permission.KB_CREATE,
        Permission.KB_READ_OWN,
        Permission.KB_READ_PUBLIC,
        Permission.KB_READ_ALL,
        Permission.KB_UPDATE_OWN,
        Permission.KB_UPDATE_ALL,
        Permission.KB_DELETE_OWN,
        Permission.KB_DELETE_ALL,
        Permission.KB_COPY_PUBLIC,
        Permission.NODE_CREATE,
        Permission.NODE_READ,
        Permission.NODE_UPDATE,
        Permission.NODE_DELETE,
        Permission.USER_READ_ALL,
        Permission.USER_UPDATE_ROLE,
        Permission.USER_DELETE,
        Permission.SYSTEM_ADMIN,
    },
    UserRole.USER: {
        # Regular user permissions
        Permission.KB_CREATE,
        Permission.KB_READ_OWN,
        Permission.KB_READ_PUBLIC,
        Permission.KB_UPDATE_OWN,
        Permission.KB_DELETE_OWN,
        Permission.KB_COPY_PUBLIC,
        Permission.NODE_CREATE,
        Permission.NODE_READ,
        Permission.NODE_UPDATE,
        Permission.NODE_DELETE,
    },
}


def get_permissions_for_role(role: UserRole) -> Set[Permission]:
    """Get all permissions for a given role."""
    return ROLE_PERMISSIONS.get(role, set())


def role_has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if a role has a specific permission."""
    return permission in ROLE_PERMISSIONS.get(role, set())
