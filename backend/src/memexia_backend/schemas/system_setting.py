from pydantic import BaseModel
from typing import Optional, Any, Dict

class SystemSettingBase(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None

class SystemSettingCreate(SystemSettingBase):
    pass

class SystemSettingUpdate(BaseModel):
    value: Any
    description: Optional[str] = None

class SystemSetting(SystemSettingBase):
    class Config:
        from_attributes = True

class AuthSettings(BaseModel):
    enable_email: bool = False
    enable_phone: bool = False
    enable_qq: bool = False

    # We can add more specific configs here later if needed
    # e.g. qq_app_id, etc.


class GraphDBSettings(BaseModel):
    """Graph database configuration settings."""

    # Database type: "kuzu" (embedded, default) or "nebula" (remote)
    db_type: str = "kuzu"

    # Kuzu settings (embedded graph database)
    kuzu_db_path: str = "./data/kuzu_db"

    # NebulaGraph settings (remote graph database)
    nebula_host: str = "127.0.0.1"
    nebula_port: int = 9669
    nebula_user: str = "root"
    nebula_password: str = ""  # Empty by default for security
