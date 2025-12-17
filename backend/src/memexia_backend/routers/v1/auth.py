from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from memexia_backend.database import get_db
from memexia_backend.models import User
from memexia_backend.schemas import (
    UserCreate,
    Token,
    TokenData,
    User as UserSchema,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from memexia_backend.utils.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token_and_get_user,
)
from memexia_backend.utils.config import settings
from memexia_backend.utils.email import (
    send_verification_email,
    send_password_reset_email,
)
from memexia_backend.services.settings_service import SettingsService

router = APIRouter(tags=["auth"], prefix="/api/v1")

# tokenUrl should be an absolute path from the API root
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user(db, username=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if not payload:
            raise credentials_exception
        sub = payload.get("sub")
        if sub is None or not isinstance(sub, str):
            raise credentials_exception
        username: str = sub
        token_data = TokenData(username=username)
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        raise credentials_exception

    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


@router.post("/auth/register", response_model=UserSchema)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = get_user(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user.password)

    # Check if any verification is required
    auth_settings = SettingsService.get_auth_settings(db)
    is_verification_required = (
        auth_settings.enable_email
        or auth_settings.enable_phone
        or auth_settings.enable_qq
    )

    # If verification is required, user starts as unverified. Otherwise, verified.
    is_verified = not is_verification_required

    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        is_verified=is_verified,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    if auth_settings.enable_email:
        # Generate verification token (valid for 24 hours)
        expires_delta = timedelta(hours=24)
        verification_token = create_access_token(
            data={"sub": db_user.username, "type": "email_verification"},
            expires_delta=expires_delta,
        )
        send_verification_email(user.email, verification_token)


@router.post("/auth/verify-email")
def verify_email(token: str, db: Session = Depends(get_db)):
    user = verify_token_and_get_user(token, "email_verification", db)

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/auth/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    auth_settings = SettingsService.get_auth_settings(db)

    user = None
    if request.email and auth_settings.enable_email:
        user = db.query(User).filter(User.email == request.email).first()
        if user:
            expires_delta = timedelta(hours=1)
            reset_token = create_access_token(
                data={"sub": user.username, "type": "password_reset"},
                expires_delta=expires_delta,
            )
            send_password_reset_email(user.email, reset_token)
            return {"message": "Password reset email sent"}

    # Add Phone/QQ logic here when implemented

    # Always return success to prevent user enumeration
    return {"message": "If the account exists, a reset link has been sent."}


@router.post("/auth/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = verify_token_and_get_user(request.token, "password_reset", db)

    user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password reset successfully"}


@router.post("/auth/token", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Use authenticate_user helper for clarity
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if SettingsService.is_verification_required(db) and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account not verified",
            headers={"WWW-Authenticate": "Bearer"},
        )

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=expires_delta
    )

    expires_at = (datetime.now(timezone.utc) + expires_delta).isoformat() + "Z"

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at,
    }


@router.get("/users/me", response_model=UserSchema)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
