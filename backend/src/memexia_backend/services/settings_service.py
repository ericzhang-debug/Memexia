import json
from sqlalchemy.orm import Session
from memexia_backend.models import SystemSetting
from memexia_backend.schemas import AuthSettings
from memexia_backend.utils.config import settings as env_settings

from typing import Any

class SettingsService:
    AUTH_SETTINGS_KEY = "auth_settings"

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
    def set_setting(db: Session, key: str, value: Any, description: str|None = None):
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
        # Default to env var for email if not set in DB, but for now let's stick to DB as source of truth for "enabled" status
        # If DB entry doesn't exist, we initialize it with defaults (False)
        
        data = cls.get_setting(db, cls.AUTH_SETTINGS_KEY)
        if not data:
            # Initialize with defaults
            default_settings = AuthSettings(
                enable_email=env_settings.ENABLE_EMAIL_VERIFICATION, # Use env var as initial seed
                enable_phone=False,
                enable_qq=False
            )
            cls.set_setting(db, cls.AUTH_SETTINGS_KEY, default_settings.model_dump(), "Authentication and Verification Settings")
            return default_settings
        
        return AuthSettings(**data)

    @classmethod
    def update_auth_settings(cls, db: Session, settings: AuthSettings) -> AuthSettings:
        cls.set_setting(db, cls.AUTH_SETTINGS_KEY, settings.model_dump(), "Authentication and Verification Settings")
        return settings

    @classmethod
    def is_verification_required(cls, db: Session) -> bool:
        auth = cls.get_auth_settings(db)
        return auth.enable_email or auth.enable_phone or auth.enable_qq
