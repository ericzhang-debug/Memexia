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
