"""
Permission definitions for the Memexia application.

This module defines all available permissions as an enum.
The design allows for easy extension to a database-driven RBAC system in the future.
"""

from enum import Enum


class Permission(str, Enum):
    """
    All system permissions.

    Naming convention: RESOURCE_ACTION or RESOURCE_ACTION_SCOPE
    - RESOURCE: The resource type (KB, USER, etc.)
    - ACTION: The action (CREATE, READ, UPDATE, DELETE)
    - SCOPE: Optional scope modifier (OWN, PUBLIC, ALL)
    """

    # Knowledge Base permissions
    KB_CREATE = "kb:create"
    KB_READ_OWN = "kb:read:own"
    KB_READ_PUBLIC = "kb:read:public"
    KB_READ_ALL = "kb:read:all"
    KB_UPDATE_OWN = "kb:update:own"
    KB_UPDATE_ALL = "kb:update:all"
    KB_DELETE_OWN = "kb:delete:own"
    KB_DELETE_ALL = "kb:delete:all"
    KB_COPY_PUBLIC = "kb:copy:public"

    # Node permissions (within knowledge base)
    NODE_CREATE = "node:create"
    NODE_READ = "node:read"
    NODE_UPDATE = "node:update"
    NODE_DELETE = "node:delete"

    # User management permissions
    USER_READ_ALL = "user:read:all"
    USER_UPDATE_ROLE = "user:update:role"
    USER_DELETE = "user:delete"

    # System permissions
    SYSTEM_ADMIN = "system:admin"
