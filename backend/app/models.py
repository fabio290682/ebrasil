from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .database import Base


class Municipio(Base):
    __tablename__ = "municipios"

    codigo_ibge: Mapped[str] = mapped_column(String(7), primary_key=True, index=True)
    nome_municipio: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    uf: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    nome_estado: Mapped[str | None] = mapped_column(String(80))
    nome_regiao: Mapped[str | None] = mapped_column(String(30))
    populacao_estimada: Mapped[int | None] = mapped_column(Integer)
    porte_municipio: Mapped[str | None] = mapped_column(String(40))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class GastoPublico(Base):
    __tablename__ = "gastos_publicos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    categoria_origem: Mapped[str | None] = mapped_column(String(80), index=True)
    agente_publico: Mapped[str | None] = mapped_column(String(255), index=True)
    partido: Mapped[str | None] = mapped_column(String(20), index=True)
    tipo_despesa: Mapped[str | None] = mapped_column(String(120), index=True)
    data_empenho: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    valor_empenhado: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    favorecido_nome: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    favorecido_cnpj_cpf: Mapped[str | None] = mapped_column(String(18), index=True)
    elemento_despesa: Mapped[str | None] = mapped_column(String(20), index=True)
    fonte_recurso: Mapped[str | None] = mapped_column(String(100))
    funcao_governo: Mapped[str | None] = mapped_column(String(120))
    numero_empenho: Mapped[str | None] = mapped_column(String(80), index=True)
    municipio_ibge: Mapped[str] = mapped_column(String(7), nullable=False, index=True)
    uf: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    fornecedor_sistema: Mapped[str | None] = mapped_column(String(50))
    url_origem: Mapped[str | None] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
