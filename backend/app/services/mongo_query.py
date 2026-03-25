from datetime import date
from math import ceil

from ..mongo import get_mongo_db


def _match_filters(
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
    match: dict = {}
    if data_inicio or data_fim:
        date_match: dict = {}
        if data_inicio:
            date_match["$gte"] = data_inicio.isoformat()
        if data_fim:
            date_match["$lte"] = data_fim.isoformat()
        match["data_empenho"] = date_match
    if uf:
        match["uf"] = uf.upper()
    if municipio_ibge:
        match["municipio_ibge"] = municipio_ibge
    if elemento_despesa:
        match["elemento_despesa"] = elemento_despesa
    if fornecedor:
        match["favorecido_nome"] = {"$regex": fornecedor, "$options": "i"}
    if categoria_origem:
        match["categoria_origem"] = categoria_origem
    if agente_publico:
        match["agente_publico"] = {"$regex": agente_publico, "$options": "i"}
    if partido:
        match["partido"] = partido.upper()
    return match


def _clean_doc(doc: dict):
    doc.pop("_id", None)
    return doc


def list_gastos(
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
    db = get_mongo_db()
    match = _match_filters(
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

    total = db.gastos_publicos.count_documents(match)
    total_pages = max(ceil(total / page_size), 1)
    rows = (
        db.gastos_publicos.find(match)
        .sort("data_empenho", -1)
        .skip((page - 1) * page_size)
        .limit(page_size)
    )
    return [_clean_doc(r) for r in rows], int(total), int(total_pages)


def resumo_gastos(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    uf: str | None = None,
    municipio_ibge: str | None = None,
    categoria_origem: str | None = None,
    agente_publico: str | None = None,
    partido: str | None = None,
):
    db = get_mongo_db()
    match = _match_filters(
        data_inicio=data_inicio,
        data_fim=data_fim,
        uf=uf,
        municipio_ibge=municipio_ibge,
        categoria_origem=categoria_origem,
        agente_publico=agente_publico,
        partido=partido,
    )
    agg = list(
        db.gastos_publicos.aggregate(
            [
                {"$match": match},
                {"$group": {"_id": None, "total": {"$sum": "$valor_empenhado"}, "qtd": {"$sum": 1}}},
            ]
        )
    )
    total = float(agg[0]["total"]) if agg else 0.0
    qtd = int(agg[0]["qtd"]) if agg else 0
    ticket = (total / qtd) if qtd else 0.0
    return total, qtd, ticket


def top_fornecedores(
    limit: int,
    data_inicio: date | None = None,
    data_fim: date | None = None,
    uf: str | None = None,
    categoria_origem: str | None = None,
):
    db = get_mongo_db()
    match = _match_filters(data_inicio=data_inicio, data_fim=data_fim, uf=uf, categoria_origem=categoria_origem)
    rows = list(
        db.gastos_publicos.aggregate(
            [
                {"$match": match},
                {
                    "$group": {
                        "_id": "$favorecido_nome",
                        "total_empenhado": {"$sum": "$valor_empenhado"},
                        "quantidade_empenhos": {"$sum": 1},
                    }
                },
                {"$sort": {"total_empenhado": -1}},
                {"$limit": limit},
            ]
        )
    )
    return rows


def list_municipios(uf: str | None = None):
    db = get_mongo_db()
    match = {"uf": uf.upper()} if uf else {}
    rows = db.municipios.find(match).sort("nome_municipio", 1)
    return [_clean_doc(r) for r in rows]


def get_municipio(codigo_ibge: str):
    db = get_mongo_db()
    row = db.municipios.find_one({"codigo_ibge": codigo_ibge})
    return _clean_doc(row) if row else None


def grouped_stats(group_field: str, label: str, data_inicio: date | None = None, data_fim: date | None = None, uf: str | None = None):
    db = get_mongo_db()
    match = _match_filters(data_inicio=data_inicio, data_fim=data_fim, uf=uf)
    rows = list(
        db.gastos_publicos.aggregate(
            [
                {"$match": match},
                {"$group": {"_id": f"${group_field}", "total": {"$sum": "$valor_empenhado"}, "qtd": {"$sum": 1}}},
                {"$sort": {"total": -1}},
            ]
        )
    )
    out = []
    for r in rows:
        out.append({label: r["_id"], "total": float(r.get("total", 0) or 0), "qtd": int(r.get("qtd", 0) or 0)})
    return out


def evolucao_mensal(data_inicio: date | None = None, data_fim: date | None = None, uf: str | None = None):
    db = get_mongo_db()
    match = _match_filters(data_inicio=data_inicio, data_fim=data_fim, uf=uf)
    rows = list(
        db.gastos_publicos.aggregate(
            [
                {"$match": match},
                {"$addFields": {"mes": {"$substr": ["$data_empenho", 0, 7]}}},
                {"$group": {"_id": "$mes", "total": {"$sum": "$valor_empenhado"}, "qtd": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]
        )
    )
    return [{"mes": r["_id"], "total": float(r.get("total", 0) or 0), "qtd": int(r.get("qtd", 0) or 0)} for r in rows]
