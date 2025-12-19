import json
from sqlalchemy.orm import Session
from memexia_backend.models import SystemSetting
from memexia_backend.schemas import AuthSettings, GraphDBSettings
from memexia_backend.config import settings as env_settings

from typing import Any


class SettingsService:
    AUTH_SETTINGS_KEY = "auth_settings"
    GRAPH_DB_SETTINGS_KEY = "graph_db_settings"

    @staticmethod
    def get_setting(db: Session, key: str, default: Any = None) -> Any:
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        if setting:
            try:
                return json.loads(setting.value)
            except json.JSONDecodeError:
                return setting.value
        return default

    @staticmethod
    def set_setting(db: Session, key: str, value: Any, description: str | None = None):
        setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
        json_value = json.dumps(value)

        if setting:
            setting.value = json_value
            if description:
                setting.description = description
        else:
            setting = SystemSetting(key=key, value=json_value, description=description)
            db.add(setting)

        db.commit()
        db.refresh(setting)
        return setting

    @classmethod
    def get_auth_settings(cls, db: Session) -> AuthSettings:
        data = cls.get_setting(db, cls.AUTH_SETTINGS_KEY)
        if not data:
            # Initialize with defaults
            default_settings = AuthSettings(
                enable_email=env_settings.ENABLE_EMAIL_VERIFICATION,
                enable_phone=False,
                enable_qq=False,
            )
            cls.set_setting(
                db,
                cls.AUTH_SETTINGS_KEY,
                default_settings.model_dump(),
                "Authentication and Verification Settings",
            )
            return default_settings

        return AuthSettings(**data)

    @classmethod
    def update_auth_settings(cls, db: Session, settings: AuthSettings) -> AuthSettings:
        cls.set_setting(
            db,
            cls.AUTH_SETTINGS_KEY,
            settings.model_dump(),
            "Authentication and Verification Settings",
        )
        return settings

    @classmethod
    def is_verification_required(cls, db: Session) -> bool:
        auth = cls.get_auth_settings(db)
        return auth.enable_email or auth.enable_phone or auth.enable_qq

    @classmethod
    def get_graph_db_settings(cls, db: Session) -> GraphDBSettings:
        """
        Get graph database settings.

        Priority: Database settings > Environment variables > Defaults
        """
        data = cls.get_setting(db, cls.GRAPH_DB_SETTINGS_KEY)
        if not data:
            # Initialize with environment variables as defaults
            default_settings = GraphDBSettings(
                db_type=env_settings.GRAPH_DB_TYPE,
                kuzu_db_path=env_settings.KUZU_DB_PATH,
                nebula_host=env_settings.NEBULA_HOST,
                nebula_port=env_settings.NEBULA_PORT,
                nebula_user=env_settings.NEBULA_USER,
                nebula_password="",  # Don't store password from env in DB
            )
            cls.set_setting(
                db,
                cls.GRAPH_DB_SETTINGS_KEY,
                default_settings.model_dump(),
                "Graph Database Settings",
            )
            return default_settings

        return GraphDBSettings(**data)

    @classmethod
    def update_graph_db_settings(
        cls, db: Session, settings: GraphDBSettings
    ) -> GraphDBSettings:
        """
        Update graph database settings.

        Note: Changes require application restart to take effect.
        """
        cls.set_setting(
            db,
            cls.GRAPH_DB_SETTINGS_KEY,
            settings.model_dump(),
            "Graph Database Settings",
        )
        return settings

    @classmethod
    def get_current_graph_db_type(cls, db: Session) -> str:
        """Get the currently configured graph database type."""
        settings = cls.get_graph_db_settings(db)
        return settings.db_type


settings_service = SettingsService()
