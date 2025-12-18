"""
Application initialization services.

This module handles startup tasks like creating the default superuser.
"""

import logging
import secrets
from sqlalchemy.orm import Session

from memexia_backend.models import User
from memexia_backend.enums import UserRole
from memexia_backend.config import settings
from memexia_backend.utils.security import verify_password


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

    # Determine password
    password = settings.SUPERUSER_PASSWORD
    password_was_generated = False

    if existing_superuser:
        logger.info(
            f"Superuser already exists: {existing_superuser.username}"
        )
        if verify_password(password, existing_superuser.hashed_password):
            logger.info("Superuser password is correct")
        else:
            existing_superuser.password = password
        return


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
    superuser = User(
        email=settings.SUPERUSER_EMAIL,
        username=settings.SUPERUSER_USERNAME,
        password=password,
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


def init_all_services() -> None:
    """
    Initialize all required services including NebulaGraph deployment.

    This function is called during FastAPI startup and handles:
    - NebulaGraph auto-deployment
    - Database schema initialization
    - Superuser creation
    """
    import sys

    logger.info("🚀 Initializing all services...")

    try:
        from ..database import SessionLocal
        from ..services.nebula_deployer import NebulaDeployer

        # Initialize NebulaGraph
        nebula_deployer = NebulaDeployer()
        nebula_deployer.deploy()

        db = SessionLocal()
        try:
            init_database(db)
        finally:
            db.close()

        logger.info("✅ All services initialized successfully")

    except Exception as e:
        logger.error(f"❌ Service initialization failed: {e}")
        sys.exit(1)
