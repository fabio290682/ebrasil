import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel

# Configurações de Segurança (Devem vir de variáveis de ambiente em produção)
# Reutilizando as mesmas chaves e algoritmos definidos em audit_router.py
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sua_chave_secreta_muito_longa_aqui")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

router = APIRouter(prefix="/api/v1/auth", tags=["Autenticação"])

# 1. Modelo Pydantic para a resposta do token
class Token(BaseModel):
    access_token: str
    token_type: str

# 2. Simulação de um banco de dados de usuários
# Em um cenário real, você buscaria isso de um banco de dados
class UserInDB(BaseModel):
    username: str
    hashed_password: str # Senha já hashed
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None

fake_users_db = {
    "admin@ebrasil.gov.br": {
        "username": "admin@ebrasil.gov.br",
        "hashed_password": "hashed_password_admin", # Use um hash real em produção (ex: bcrypt)
        "email": "admin@ebrasil.gov.br",
        "full_name": "Administrador E-Brasil",
        "disabled": False,
    },
    "user@ebrasil.gov.br": {
        "username": "user@ebrasil.gov.br",
        "hashed_password": "hashed_password_user", # Use um hash real em produção
        "email": "user@ebrasil.gov.br",
        "full_name": "Usuário Comum",
        "disabled": False,
    },
}

def get_user(username: str):
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Em um cenário real, você usaria uma biblioteca de hashing (ex: bcrypt)
    # para comparar a senha em texto puro com a senha hashed.
    # Ex: return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    return plain_password + "_secret" == hashed_password # Simulação

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nome de usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}