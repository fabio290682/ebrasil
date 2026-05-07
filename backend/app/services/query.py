from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import DATABASE_URL
from ..models import GastoPublico, Municipio


def month_label(col):
    """YYYY-MM grouping expression compatible with both SQLite and PostgreSQL."""
    if DATABASE_URL.startswith("sqlite"):
        return func.strftime("%Y-%m", col)
    return func.to_char(col, "YYYY-MM")


def apply_gasto_filters(
    stmt,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    uf: str | None = None,
    municipio_ibge: str | None = None,
    elemento_despesa: str | None = None,
    fornecedor: str | None = None,
    categoria_origem: str | None = None,
    agente_publico: str | None = None,
    partido: str | None = None,
):
    if data_inicio:
        stmt = stmt.where(GastoPublico.data_empenho >= data_inicio)
    if data_fim:
        stmt = stmt.where(GastoPublico.data_empenho <= data_fim)
    if uf:
        stmt = stmt.where(GastoPublico.uf == uf.upper())
    if municipio_ibge:
        stmt = stmt.where(GastoPublico.municipio_ibge == municipio_ibge)
    if elemento_despesa:
        stmt = stmt.where(GastoPublico.elemento_despesa == elemento_despesa)
    if fornecedor:
        stmt = stmt.where(GastoPublico.favorecido_nome.ilike(f"%{fornecedor}%"))
    if categoria_origem:
        stmt = stmt.where(GastoPublico.categoria_origem == categoria_origem)
    if agente_publico:
        stmt = stmt.where(GastoPublico.agente_publico.ilike(f"%{agente_publico}%"))
    if partido:
        stmt = stmt.where(GastoPublico.partido == partido.upper())
    return stmt


def list_gastos(
    db: Session,
    page: int,
    page_size: int,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    uf: str | None = None,
    municipio_ibge: str | None = None,
    elemento_despesa: str | None = None,
    fornecedor: str | None = None,
    categoria_origem: str | None = None,
    agente_publico: str | None = None,
    partido: str | None = None,
):
    base_stmt = select(GastoPublico)
    base_stmt = apply_gasto_filters(
        base_stmt,
        data_inicio=data_inicio,
        data_fim=data_fim,
        uf=uf,
        municipio_ibge=municipio_ibge,
        elemento_despesa=elemento_despesa,
        fornecedor=fornecedor,
        categoria_origem=categoria_origem,
        agente_publico=agente_publico,
        partido=partido,
    )

    total_stmt = select(func.count()).select_from(base_stmt.subquery())
    total = db.scalar(total_stmt) or 0
    total_pages = max((total + page_size - 1) // page_size, 1)
    offset = (page - 1) * page_size

    rows = db.scalars(
        base_stmt.order_by(GastoPublico.data_empenho.desc()).offset(offset).limit(page_size)
    ).all()
    return rows, total, total_pages


def resumo_gastos(
    db: Session,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    uf: str | None = None,
    municipio_ibge: str | None = None,
    categoria_origem: str | None = None,
    agente_publico: str | None = None,
    partido: str | None = None,
):
    stmt = select(
        func.coalesce(func.sum(GastoPublico.valor_empenhado), 0.0),
        func.count(GastoPublico.id),
    )
    stmt = apply_gasto_filters(
        stmt,
        data_inicio=data_inicio,
        data_fim=data_fim,
        uf=uf,
        municipio_ibge=municipio_ibge,
        categoria_origem=categoria_origem,
        agente_publico=agente_publico,
        partido=partido,
    )
    total_empenhado, quantidade = db.execute(stmt).one()
    ticket_medio = float(total_empenhado / quantidade) if quantidade else 0.0
    return float(total_empenhado), int(quantidade), ticket_medio


def top_fornecedores(
    db: Session,
    limit: int,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    uf: str | None = None,
    categoria_origem: str | None = None,
):
    stmt = select(
        GastoPublico.favorecido_nome,
        func.sum(GastoPublico.valor_empenhado).label("total_empenhado"),
        func.count(GastoPublico.id).label("quantidade_empenhos"),
    ).group_by(GastoPublico.favorecido_nome)

    stmt = apply_gasto_filters(
        stmt,
        data_inicio=data_inicio,
        data_fim=data_fim,
        uf=uf,
        categoria_origem=categoria_origem,
    )

    return db.execute(stmt.order_by(func.sum(GastoPublico.valor_empenhado).desc()).limit(limit)).all()


def list_municipios(db: Session, uf: str | None = None):
    stmt = select(Municipio)
    if uf:
        stmt = stmt.where(Municipio.uf == uf.upper())
    return db.scalars(stmt.order_by(Municipio.nome_municipio.asc())).all()
