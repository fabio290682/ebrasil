import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "ebrasil_dev_secret_key_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# prefix is /auth — API_PREFIX (/api/v1) is applied in main.py
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


# Placeholder user store — replace with real DB lookup in production
_USERS: dict[str, dict] = {
    "admin@ebrasil.gov.br": {
        "username": "admin@ebrasil.gov.br",
        "hashed_password": "admin_secret",
        "email": "admin@ebrasil.gov.br",
        "full_name": "Administrador",
        "disabled": False,
    },
}


def _get_user(username: str) -> Optional[UserInDB]:
    data = _USERS.get(username)
    return UserInDB(**data) if data else None


def _verify_password(plain: str, hashed: str) -> bool:
    # TODO: replace with bcrypt in production
    return f"{plain}_secret" == hashed


def _create_token(data: dict, expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
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
