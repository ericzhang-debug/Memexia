"""
KnowledgeBase model.

A KnowledgeBase is a user-owned collection of thought nodes that form a knowledge graph.
Each knowledge base has a seed node (the starting point) and can be public or private.
"""
import uuid

from datetime import datetime

from sqlalchemy import  Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship,Mapped, mapped_column
from typing import Optional

from ..database import Base


def generate_uuid():
    """Generate a UUID string for knowledge base ID."""
    return str(uuid.uuid4())


class KnowledgeBase(Base):
    """Knowledge base model - a collection of related thought nodes."""

    __tablename__ = "knowledge_bases"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=generate_uuid
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    seed_node_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # Neo4j node ID
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    owner = relationship("User", back_populates="knowledge_bases")

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name}, owner_id={self.owner_id})>"
