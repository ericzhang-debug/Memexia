"""
Knowledge Base service for CRUD operations.

This service handles all knowledge base related operations including
creation, retrieval, update, deletion, and copying.
"""

from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from memexia_backend.models import KnowledgeBase, User
from memexia_backend.schemas import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
)
from memexia_backend.enums import Permission
from memexia_backend.utils.permissions import check_permission
from memexia_backend.logger import logger


class KnowledgeBaseService:
    """Service for knowledge base operations."""

    def create(
        self,
        db: Session,
        kb_data: KnowledgeBaseCreate,
        owner: User,
    ) -> KnowledgeBase:
        """
        Create a new knowledge base.

        Args:
            db: Database session
            kb_data: Knowledge base creation data
            owner: Owner user

        Returns:
            Created KnowledgeBase instance
        """
        kb = KnowledgeBase(
            name=kb_data.name,
            description=kb_data.description,
            owner_id=owner.id,
            is_public=kb_data.is_public,
        )

        db.add(kb)
        db.commit()
        db.refresh(kb)

        logger.info(f"Created knowledge base: {kb.id} for user {owner.username}")

        # TODO: If seed_content is provided, create the seed node in Neo4j
        # and update kb.seed_node_id

        return kb

    def get_by_id(
        self,
        db: Session,
        kb_id: str,
        user: Optional[User] = None,
    ) -> Optional[KnowledgeBase]:
        """
        Get a knowledge base by ID with access control.

        Args:
            db: Database session
            kb_id: Knowledge base ID
            user: Current user (None for guest)

        Returns:
            KnowledgeBase if found and accessible, None otherwise
        """
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

        if not kb:
            return None

        # Check access permissions
        if not self._can_access(kb, user):
            return None

        return kb

    def get_list(
        self,
        db: Session,
        user: Optional[User] = None,
        page: int = 1,
        page_size: int = 20,
        owner_only: bool = False,
    ) -> tuple[list[KnowledgeBase], int]:
        """
        Get list of knowledge bases with pagination.

        Args:
            db: Database session
            user: Current user (None for guest)
            page: Page number (1-indexed)
            page_size: Number of items per page
            owner_only: If True, only return user's own knowledge bases

        Returns:
            Tuple of (list of knowledge bases, total count)
        """
        query = db.query(KnowledgeBase)

        if user is None:
            # Guest: only public knowledge bases
            query = query.filter(KnowledgeBase.is_public)
        elif owner_only:
            # Only user's own knowledge bases
            query = query.filter(KnowledgeBase.owner_id == user.id)
        elif check_permission(user, Permission.KB_READ_ALL):
            # Admin: all knowledge bases
            pass
        else:
            # Regular user: own + public
            query = query.filter(
                or_(
                    KnowledgeBase.owner_id == user.id,
                    KnowledgeBase.is_public,
                )
            )

        # Get total count
        total = query.count()

        # Apply pagination
        offset = (page - 1) * page_size
        items = (
            query.order_by(KnowledgeBase.created_at.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )

        return items, total

    def update(
        self,
        db: Session,
        kb: KnowledgeBase,
        update_data: KnowledgeBaseUpdate,
    ) -> KnowledgeBase:
        """
        Update a knowledge base.

        Args:
            db: Database session
            kb: Knowledge base to update
            update_data: Update data

        Returns:
            Updated KnowledgeBase instance
        """
        update_dict = update_data.model_dump(exclude_unset=True)

        for field, value in update_dict.items():
            setattr(kb, field, value)

        db.commit()
        db.refresh(kb)

        logger.info(f"Updated knowledge base: {kb.id}")

        return kb

    def delete(self, db: Session, kb: KnowledgeBase) -> None:
        """
        Delete a knowledge base.

        Args:
            db: Database session
            kb: Knowledge base to delete
        """
        kb_id = kb.id
        db.delete(kb)
        db.commit()

        # TODO: Delete associated nodes from Neo4j and ChromaDB

        logger.info(f"Deleted knowledge base: {kb_id}")

    def copy(
        self,
        db: Session,
        source_kb: KnowledgeBase,
        new_owner: User,
        new_name: Optional[str] = None,
    ) -> KnowledgeBase:
        """
        Copy a public knowledge base for a user.

        Args:
            db: Database session
            source_kb: Source knowledge base (must be public)
            new_owner: New owner user
            new_name: Optional new name (defaults to "Copy of {original}")

        Returns:
            New KnowledgeBase instance
        """
        if not source_kb.is_public:
            raise ValueError("Can only copy public knowledge bases")

        name = new_name or f"Copy of {source_kb.name}"

        new_kb = KnowledgeBase(
            name=name,
            description=source_kb.description,
            owner_id=new_owner.id,
            is_public=False,  # Copies are private by default
        )

        db.add(new_kb)
        db.commit()
        db.refresh(new_kb)

        # TODO: Copy nodes from Neo4j and ChromaDB

        logger.info(
            f"Copied knowledge base {source_kb.id} to {new_kb.id} for user {new_owner.username}"
        )

        return new_kb

    def _can_access(self, kb: KnowledgeBase, user: Optional[User]) -> bool:
        """
        Check if a user can access a knowledge base.

        Args:
            kb: Knowledge base
            user: Current user (None for guest)

        Returns:
            True if user can access the knowledge base
        """
        # Public knowledge bases are accessible to everyone
        if kb.is_public:
            return True

        # Guests can't access private knowledge bases
        if user is None:
            return False

        # Owners can access their own knowledge bases
        if kb.owner_id == user.id:
            return True

        # Admins can access all knowledge bases
        if check_permission(user, Permission.KB_READ_ALL):
            return True

        return False

    def can_modify(self, kb: KnowledgeBase, user: User) -> bool:
        """
        Check if a user can modify a knowledge base.

        Args:
            kb: Knowledge base
            user: Current user

        Returns:
            True if user can modify the knowledge base
        """
        # Owners can modify their own knowledge bases
        if kb.owner_id == user.id:
            return True

        # Admins can modify all knowledge bases
        if check_permission(user, Permission.KB_UPDATE_ALL):
            return True

        return False

    def can_delete(self, kb: KnowledgeBase, user: User) -> bool:
        """
        Check if a user can delete a knowledge base.

        Args:
            kb: Knowledge base
            user: Current user

        Returns:
            True if user can delete the knowledge base
        """
        # Owners can delete their own knowledge bases
        if kb.owner_id == user.id:
            return True

        # Admins can delete all knowledge bases
        if check_permission(user, Permission.KB_DELETE_ALL):
            return True

        return False


# Global service instance
knowledge_base_service = KnowledgeBaseService()
