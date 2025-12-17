from typing import Optional
from pydantic import BaseModel, Field, EmailStr

class PasswordResetRequest(BaseModel):
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    # qq_openid: Optional[str] = None # Usually you don't reset password via QQ ID directly, but maybe via linked QQ login

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)
