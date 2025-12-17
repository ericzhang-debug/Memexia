"""
Application initialization services.

This module handles startup tasks like creating the default superuser.
"""

import logging
import secrets
from sqlalchemy.orm import Session

from memexia_backend.models import User
from memexia_backend.enums import UserRole
from memexia_backend.utils.config import settings
from memexia_backend.utils.security import get_password_hash


logger = logging.getLogger(__name__)


def generate_random_password(length: int = 16) -> str:
    """Generate a secure random password."""
    return secrets.token_urlsafe(length)


def init_superuser(db: Session) -> None:
    """
    Initialize the default superuser account.

    This function checks if any superuser exists in the database.
    If not, it creates one using the configured credentials.

    The superuser password can be set via:
    1. SUPERUSER_PASSWORD environment variable (recommended for production)
    2. Auto-generated if not provided (password will be logged - for development only)

    Args:
        db: SQLAlchemy database session
    """
    # Check if any superuser already exists
    existing_superuser = db.query(User).filter(User.is_superuser).first()

    if existing_superuser:
        logger.info(
            f"Superuser already exists: {existing_superuser.username}"
        )
        return

    # Determine password
    password = settings.SUPERUSER_PASSWORD
    password_was_generated = False

    if not password:
        password = generate_random_password()
        password_was_generated = True
        logger.warning(
            "=" * 60 + "\n"
            "⚠️  SUPERUSER PASSWORD AUTO-GENERATED!\n"
            f"    Username: {settings.SUPERUSER_USERNAME}\n"
            f"    Password: {password}\n"
            "    \n"
            "    Please save this password and set SUPERUSER_PASSWORD\n"
            "    environment variable in production!\n"
            + "=" * 60
        )

    # Create superuser
    hashed_password = get_password_hash(password)

    superuser = User(
        email=settings.SUPERUSER_EMAIL,
        username=settings.SUPERUSER_USERNAME,
        hashed_password=hashed_password,
        role=UserRole.ADMIN.value,
        is_superuser=True,
        is_active=True,
        is_verified=True,
    )

    db.add(superuser)
    db.commit()
    db.refresh(superuser)

    logger.info(
        f"Superuser created successfully: {superuser.username} (id={superuser.id})"
    )

    if not password_was_generated:
        logger.info("Superuser password was set from environment variable")


def init_database(db: Session) -> None:
    """
    Run all database initialization tasks.

    Call this function during application startup.

    Args:
        db: SQLAlchemy database session
    """
    logger.info("Running database initialization...")

    # Initialize superuser
    init_superuser(db)

    logger.info("Database initialization complete")
