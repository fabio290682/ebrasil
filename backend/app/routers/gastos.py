import csv
import io
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..config import DATABASE_BACKEND
from ..database import get_db
from ..schemas import GastoListResponse, PageMeta, ResumoGastosResponse, TopFornecedorItem
from ..services import mongo_query
from ..services.query import list_gastos, resumo_gastos, top_fornecedores

router = APIRouter(prefix="/gastos", tags=["gastos"])


def _getv(obj, key):
    if isinstance(obj, dict):
        return obj.get(key)
    return getattr(obj, key, None)


@router.get("", response_model=GastoListResponse)
def get_gastos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=200),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    municipio_ibge: str | None = Query(default=None, min_length=7, max_length=7),
    elemento_despesa: str | None = Query(default=None),
    fornecedor: str | None = Query(default=None),
    categoria_origem: str | None = Query(default=None),
    agente_publico: str | None = Query(default=None),
    partido: str | None = Query(default=None, min_length=2, max_length=20),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        items, total, total_pages = mongo_query.list_gastos(
            page=page,
            page_size=page_size,
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
    else:
        items, total, total_pages = list_gastos(
            db,
            page=page,
            page_size=page_size,
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

    return GastoListResponse(
        items=items,
        meta=PageMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


@router.get("/resumo", response_model=ResumoGastosResponse)
def get_resumo(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    municipio_ibge: str | None = Query(default=None, min_length=7, max_length=7),
    categoria_origem: str | None = Query(default=None),
    agente_publico: str | None = Query(default=None),
    partido: str | None = Query(default=None, min_length=2, max_length=20),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        total, quantidade, ticket = mongo_query.resumo_gastos(
            data_inicio=data_inicio,
            data_fim=data_fim,
            uf=uf,
            municipio_ibge=municipio_ibge,
            categoria_origem=categoria_origem,
            agente_publico=agente_publico,
            partido=partido,
        )
    else:
        total, quantidade, ticket = resumo_gastos(
            db,
            data_inicio=data_inicio,
            data_fim=data_fim,
            uf=uf,
            municipio_ibge=municipio_ibge,
            categoria_origem=categoria_origem,
            agente_publico=agente_publico,
            partido=partido,
        )

    return ResumoGastosResponse(total_empenhado=total, quantidade_registros=quantidade, ticket_medio=ticket)


@router.get("/top-fornecedores", response_model=list[TopFornecedorItem])
def get_top_fornecedores(
    limit: int = Query(default=10, ge=1, le=100),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    categoria_origem: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        rows = mongo_query.top_fornecedores(
            limit=limit,
            data_inicio=data_inicio,
            data_fim=data_fim,
            uf=uf,
            categoria_origem=categoria_origem,
        )
        return [
            TopFornecedorItem(
                favorecido_nome=r.get("_id") or "NAO INFORMADO",
                total_empenhado=float(r.get("total_empenhado") or 0.0),
                quantidade_empenhos=int(r.get("quantidade_empenhos") or 0),
            )
            for r in rows
        ]

    rows = top_fornecedores(
        db,
        limit=limit,
        data_inicio=data_inicio,
        data_fim=data_fim,
        uf=uf,
        categoria_origem=categoria_origem,
    )
    return [
        TopFornecedorItem(
            favorecido_nome=row[0],
            total_empenhado=float(row[1] or 0.0),
            quantidade_empenhos=int(row[2] or 0),
        )
        for row in rows
    ]


@router.get("/export/csv")
def export_csv(
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
    uf: str | None = Query(default=None, min_length=2, max_length=2),
    municipio_ibge: str | None = Query(default=None, min_length=7, max_length=7),
    elemento_despesa: str | None = Query(default=None),
    fornecedor: str | None = Query(default=None),
    categoria_origem: str | None = Query(default=None),
    agente_publico: str | None = Query(default=None),
    partido: str | None = Query(default=None, min_length=2, max_length=20),
    db: Session = Depends(get_db),
):
    if DATABASE_BACKEND == "mongo":
        items, _, _ = mongo_query.list_gastos(
            page=1,
            page_size=10000,
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
    else:
        items, _, _ = list_gastos(
            db,
            page=1,
            page_size=10000,
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

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "data_empenho",
        "favorecido_nome",
        "favorecido_cnpj_cpf",
        "valor_empenhado",
        "funcao_governo",
        "elemento_despesa",
        "fonte_recurso",
        "uf",
        "municipio_ibge",
        "categoria_origem",
        "agente_publico",
        "partido",
        "numero_empenho",
        "fornecedor_sistema",
        "url_origem",
    ])
    for g in items:
        writer.writerow([
            _getv(g, "id"),
            _getv(g, "data_empenho"),
            _getv(g, "favorecido_nome"),
            _getv(g, "favorecido_cnpj_cpf"),
            _getv(g, "valor_empenhado"),
            _getv(g, "funcao_governo"),
            _getv(g, "elemento_despesa"),
            _getv(g, "fonte_recurso"),
            _getv(g, "uf"),
            _getv(g, "municipio_ibge"),
            _getv(g, "categoria_origem"),
            _getv(g, "agente_publico"),
            _getv(g, "partido"),
            _getv(g, "numero_empenho"),
            _getv(g, "fornecedor_sistema"),
            _getv(g, "url_origem"),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue().encode("utf-8-sig")]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gastos_iiibrasil.csv"},
    )
