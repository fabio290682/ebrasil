import os
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Assumindo a estrutura padrão de database.py do projeto
from .database import Base, get_db 

# Configurações de Segurança (Devem vir de variáveis de ambiente em produção)
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "sua_chave_secreta_muito_longa_aqui")
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

async def get_current_user_email(token: str = Depends(oauth2_scheme)) -> str:
    """
    Valida o JWT e extrai o e-mail do campo 'sub'.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        return email
    except JWTError:
        raise credentials_exception

# 1. Modelo de Banco de Dados (SQLAlchemy)
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_email = Column(String)
    action = Column(String) # Ex: "EXPORT_CSV"
    filters_applied = Column(JSON)
    ip_address = Column(String)

# 2. Schemas para API (Pydantic)
class AuditLogSchema(BaseModel):
    id: int
    timestamp: datetime
    user_email: str
    action: str
    filters_applied: dict
    ip_address: str

    class Config:
        from_attributes = True

# 3. Router e Endpoints
router = APIRouter(prefix="/api/v1/audit", tags=["Auditoria"])

@router.get("/exports", response_model=List[AuditLogSchema], dependencies=[Depends(get_current_user_email)])
async def list_audit_logs(
    db: Session = Depends(get_db), 
    limit: int = 50
):
    """
    Retorna os logs de auditoria mais recentes de exportação.
    Requer autenticação via token Bearer.
    """
    return db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit).all()

def record_export_log(db: Session, user_email: str, filters: dict, ip: str):
    """
    Função utilitária para registrar um log. 
    Deve ser chamada dentro da lógica de exportação de gastos.
    """
    new_log = AuditLog(
        user_email=user_email,
        action="EXPORT_CSV",
        filters_applied=filters,
        ip_address=ip
    )
    db.add(new_log)
    db.commit()