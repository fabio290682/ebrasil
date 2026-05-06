import logging
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel

_logger = logging.getLogger(__name__)

_raw_secret = os.getenv("JWT_SECRET_KEY", "")
if not _raw_secret:
    _raw_secret = secrets.token_hex(32)
    _logger.warning("JWT_SECRET_KEY not set — using ephemeral key. Tokens will be invalidated on restart.")

SECRET_KEY = _raw_secret
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

_pwd_ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

router = APIRouter(prefix="/auth", tags=["auth"])


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInDB(BaseModel):
    username: str
    hashed_password: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


def _build_users() -> dict[str, dict]:
    admin_email = os.getenv("ADMIN_EMAIL", "admin@ebrasil.gov.br")
    admin_pass = os.getenv("ADMIN_PASSWORD", "")
    if not admin_pass:
        admin_pass = secrets.token_urlsafe(16)
        _logger.warning("ADMIN_PASSWORD not set — generated temporary password: %s", admin_pass)
    return {
        admin_email: {
            "username": admin_email,
            "hashed_password": _pwd_ctx.hash(admin_pass),
            "email": admin_email,
            "full_name": "Administrador",
            "disabled": False,
        }
    }


_USERS = _build_users()


def _get_user(username: str) -> Optional[UserInDB]:
    data = _USERS.get(username)
    return UserInDB(**data) if data else None


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(plain, hashed)


def _create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload["exp"] = expire
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = _get_user(form_data.username)
    if not user or not _verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = _create_token(
        {"sub": user.email},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": token, "token_type": "bearer"}
