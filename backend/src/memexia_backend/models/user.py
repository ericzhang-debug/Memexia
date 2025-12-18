from sqlalchemy import Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from typing import Optional, TYPE_CHECKING
from datetime import datetime


from ..database import Base
from ..enums import UserRole
from ..utils.security import get_password_hash


if TYPE_CHECKING:
    from .knowledge_base import KnowledgeBase

class User(Base):
    """User model with role-based access control."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(
        String, unique=True, index=True, nullable=False
    )
    phone_number: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    qq_openid: Mapped[Optional[str]] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(
        String, default=UserRole.USER.value, nullable=False
    )
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    knowledge_bases: Mapped[list["KnowledgeBase"]] = relationship(
        "KnowledgeBase", back_populates="owner", cascade="all, delete-orphan"
    )

    @property
    def is_admin(self) -> bool:
        """Check if user is admin or superuser."""
        return bool((self.role == UserRole.ADMIN.value) or self.is_superuser)

    @property
    def password(self) -> str:
        raise AttributeError("Password is write-only.")

    @password.setter
    def password(self, password: str) -> None:
        self.hashed_password = get_password_hash(password)
