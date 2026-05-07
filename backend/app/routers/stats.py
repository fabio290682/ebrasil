from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import DATABASE_BACKEND
from ..database import get_db
from ..models import GastoPublico
from ..services.query import apply_gasto_filters, month_label

router = APIRouter(prefix="/stats", tags=["stats"])


def _mongo_query():
    from ..services import mongo_query
    return mongo_query


@router.get("/por-funcao")
def gastos_por_funcao(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        mq = _mongo_query()
        rows = mq.grouped_stats("funcao_governo", "funcao", data_inicio=data_inicio, data_fim=data_fim, uf=uf)
        return [{"funcao": r.get("funcao") or "Nao informado", "total": r["total"], "qtd": r["qtd"]} for r in rows]

    stmt = select(
        GastoPublico.funcao_governo,
        func.sum(GastoPublico.valor_empenhado).label("total"),
        func.count(GastoPublico.id).label("qtd"),
    ).group_by(GastoPublico.funcao_governo)
    stmt = apply_gasto_filters(stmt, data_inicio=data_inicio, data_fim=data_fim, uf=uf)
    rows = db.execute(stmt.order_by(func.sum(GastoPublico.valor_empenhado).desc())).all()
    return [{"funcao": r[0] or "Não informado", "total": float(r[1] or 0), "qtd": int(r[2] or 0)} for r in rows]


@router.get("/por-uf")
def gastos_por_uf(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        mq = _mongo_query()
        rows = mq.grouped_stats("uf", "uf", data_inicio=data_inicio, data_fim=data_fim)
        return [{"uf": r.get("uf") or "N/A", "total": r["total"], "qtd": r["qtd"]} for r in rows]

    stmt = select(
        GastoPublico.uf,
        func.sum(GastoPublico.valor_empenhado).label("total"),
        func.count(GastoPublico.id).label("qtd"),
    ).group_by(GastoPublico.uf)
    stmt = apply_gasto_filters(stmt, data_inicio=data_inicio, data_fim=data_fim)
    rows = db.execute(stmt.order_by(func.sum(GastoPublico.valor_empenhado).desc())).all()
    return [{"uf": r[0] or "N/A", "total": float(r[1] or 0), "qtd": int(r[2] or 0)} for r in rows]


@router.get("/por-categoria")
def gastos_por_categoria(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        mq = _mongo_query()
        rows = mq.grouped_stats("categoria_origem", "categoria", data_inicio=data_inicio, data_fim=data_fim, uf=uf)
        return [{"categoria": r.get("categoria") or "Municipal", "total": r["total"], "qtd": r["qtd"]} for r in rows]

    stmt = select(
        GastoPublico.categoria_origem,
        func.sum(GastoPublico.valor_empenhado).label("total"),
        func.count(GastoPublico.id).label("qtd"),
    ).group_by(GastoPublico.categoria_origem)
    stmt = apply_gasto_filters(stmt, data_inicio=data_inicio, data_fim=data_fim, uf=uf)
    rows = db.execute(stmt.order_by(func.sum(GastoPublico.valor_empenhado).desc())).all()
    return [{"categoria": r[0] or "Municipal", "total": float(r[1] or 0), "qtd": int(r[2] or 0)} for r in rows]


@router.get("/evolucao-mensal")
def evolucao_mensal(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        mq = _mongo_query()
        return mq.evolucao_mensal(data_inicio=data_inicio, data_fim=data_fim, uf=uf)

    mes_expr = month_label(GastoPublico.data_empenho)
    stmt = select(
        mes_expr.label("mes"),
        func.sum(GastoPublico.valor_empenhado).label("total"),
        func.count(GastoPublico.id).label("qtd"),
    ).group_by(mes_expr)
    stmt = apply_gasto_filters(stmt, data_inicio=data_inicio, data_fim=data_fim, uf=uf)
    rows = db.execute(stmt.order_by("mes")).all()
    return [{"mes": r[0], "total": float(r[1] or 0), "qtd": int(r[2] or 0)} for r in rows]


@router.get("/por-elemento")
def gastos_por_elemento(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        mq = _mongo_query()
        rows = mq.grouped_stats("elemento_despesa", "elemento", data_inicio=data_inicio, data_fim=data_fim, uf=uf)
        return [{"elemento": r.get("elemento") or "Nao informado", "total": r["total"], "qtd": r["qtd"]} for r in rows]

    stmt = select(
        GastoPublico.elemento_despesa,
        func.sum(GastoPublico.valor_empenhado).label("total"),
        func.count(GastoPublico.id).label("qtd"),
    ).group_by(GastoPublico.elemento_despesa)
    stmt = apply_gasto_filters(stmt, data_inicio=data_inicio, data_fim=data_fim, uf=uf)
    rows = db.execute(stmt.order_by(func.sum(GastoPublico.valor_empenhado).desc())).all()
    return [{"elemento": r[0] or "Não informado", "total": float(r[1] or 0), "qtd": int(r[2] or 0)} for r in rows]


@router.get("/por-partido")
def gastos_por_partido(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        mq = _mongo_query()
        rows = mq.grouped_stats("partido", "partido", data_inicio=data_inicio, data_fim=data_fim)
        return [{"partido": r.get("partido"), "total": r["total"], "qtd": r["qtd"]} for r in rows if r.get("partido")]

    stmt = select(
        GastoPublico.partido,
        func.sum(GastoPublico.valor_empenhado).label("total"),
        func.count(GastoPublico.id).label("qtd"),
    ).where(GastoPublico.partido.isnot(None)).group_by(GastoPublico.partido)
    stmt = apply_gasto_filters(stmt, data_inicio=data_inicio, data_fim=data_fim)
    rows = db.execute(stmt.order_by(func.sum(GastoPublico.valor_empenhado).desc())).all()
    return [{"partido": r[0], "total": float(r[1] or 0), "qtd": int(r[2] or 0)} for r in rows]
