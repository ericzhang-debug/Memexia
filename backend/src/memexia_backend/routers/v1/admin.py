from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from memexia_backend.database import get_db
from memexia_backend.models import User
from memexia_backend.schemas import AuthSettings, GraphDBSettings
from memexia_backend.services.settings_service import SettingsService
from memexia_backend.routers.v1.auth import get_current_user

router = APIRouter(tags=["admin"], prefix="/api/v1/admin")


def check_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return current_user


@router.get("/settings/auth", response_model=AuthSettings)
def get_auth_settings(
    db: Session = Depends(get_db), current_user: User = Depends(check_admin)
):
    """Get current authentication and verification settings."""
    return SettingsService.get_auth_settings(db)


@router.put("/settings/auth", response_model=AuthSettings)
def update_auth_settings(
    settings: AuthSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin),
):
    """Update authentication and verification settings."""
    return SettingsService.update_auth_settings(db, settings)


@router.get("/settings/graph-db", response_model=GraphDBSettings)
def get_graph_db_settings(
    db: Session = Depends(get_db), current_user: User = Depends(check_admin)
):
    """
    Get current graph database settings.

    Returns the configuration for the graph database backend.
    Default is Kuzu (embedded), can be switched to NebulaGraph (remote).
    """
    return SettingsService.get_graph_db_settings(db)


@router.put("/settings/graph-db", response_model=GraphDBSettings)
def update_graph_db_settings(
    settings: GraphDBSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(check_admin),
):
    """
    Update graph database settings.

    **Important**: Changes require application restart to take effect.

    - **db_type**: "kuzu" (embedded, default) or "nebula" (remote)
    - **kuzu_db_path**: Path for Kuzu database storage
    - **nebula_***: NebulaGraph remote connection settings
    """
    # Validate db_type
    if settings.db_type not in ["kuzu", "nebula"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid db_type. Must be 'kuzu' or 'nebula'",
        )

    return SettingsService.update_graph_db_settings(db, settings)
