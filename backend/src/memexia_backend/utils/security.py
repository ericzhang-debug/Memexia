from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from .config import settings
from ..models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_token_and_get_user(token: str, token_type: str, db: Session) -> User:
    """
    Verify JWT token and retrieve the associated user.

    Args:
        token: The JWT token string
        token_type: Expected token type (e.g., 'email_verification', 'password_reset')
        db: Database session

    Returns:
        User: The user object if token is valid and user exists

    Raises:
        HTTPException: If token is invalid, expired, wrong type, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: Optional[str] = payload.get("sub")
        type_in_token: Optional[str] = payload.get("type")

        if username is None or type_in_token != token_type:
            raise credentials_exception

    except (JWTError, ExpiredSignatureError):
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
