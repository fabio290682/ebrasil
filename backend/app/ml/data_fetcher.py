"""
Fetches spending data directly from Brazilian government open data APIs
and normalizes records to the unified GastoPublico schema.

Sources:
  - Câmara dos Deputados (dadosabertos.camara.leg.br) — no auth required
  - Portal da Transparência (api.portaldatransparencia.gov.br) — requires API key
"""
import asyncio
import uuid
from datetime import datetime, date
from typing import Any, Optional
import structlog

import httpx

logger = structlog.get_logger()

CAMARA_BASE = "https://dadosabertos.camara.leg.br/api/v2"
PORTAL_BASE = "https://api.portaldatransparencia.gov.br"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_float(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def _safe_date(raw: str | None, fallback_year: int = 2026) -> str:
    if not raw:
        return f"{fallback_year}-01-01"
    # Accept YYYY-MM-DD, YYYY-MM, or DD/MM/YYYY
    raw = raw.strip()
    if len(raw) == 10 and raw[4] == "-":
        return raw  # already YYYY-MM-DD
    if len(raw) == 7 and raw[4] == "-":
        return f"{raw}-01"
    if "/" in raw:
        parts = raw.split("/")
        if len(parts) == 3:
            return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return f"{fallback_year}-01-01"


# ---------------------------------------------------------------------------
# Câmara dos Deputados
# ---------------------------------------------------------------------------

async def _fetch_camara_deputados(client: httpx.AsyncClient, limit: int) -> list[dict]:
    resp = await client.get(
        f"{CAMARA_BASE}/deputados",
        params={"itens": limit, "ordem": "ASC", "ordenarPor": "nome"},
    )
    resp.raise_for_status()
    return resp.json().get("dados", [])


async def _fetch_camara_despesas(
    client: httpx.AsyncClient, deputado_id: int, ano: int
) -> list[dict]:
    resp = await client.get(
        f"{CAMARA_BASE}/deputados/{deputado_id}/despesas",
        params={"ano": ano, "itens": 100, "pagina": 1, "ordem": "DESC", "ordenarPor": "ano"},
    )
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("dados", payload) if isinstance(payload, dict) else payload


def _normalize_camara(raw: dict, deputado_nome: str, deputado_id: int) -> dict:
    ano = raw.get("ano", datetime.now().year)
    mes = raw.get("mes", 1)
    data_str = _safe_date(raw.get("dataDocumento") or raw.get("anoMes") or f"{ano}-{mes:02d}-01")
    return {
        "id": str(uuid.uuid4()),
        "categoria_origem": "Legislativo Federal",
        "agente_publico": deputado_nome,
        "partido": str(raw.get("siglaPartido") or ""),
        "tipo_despesa": raw.get("tipoDespesa") or "Cota Parlamentar",
        "data_empenho": data_str,
        "valor_empenhado": _parse_float(raw.get("valorLiquido") or raw.get("valorDocumento")),
        "favorecido_nome": raw.get("nomeFornecedor") or "NAO INFORMADO",
        "favorecido_cnpj_cpf": str(raw.get("cnpjCpfFornecedor") or "").strip(),
        "elemento_despesa": raw.get("tipoDespesa") or "",
        "fonte_recurso": "Cota Parlamentar",
        "funcao_governo": "Legislativo",
        "numero_empenho": str(raw.get("numDocumento") or raw.get("codDocumento") or uuid.uuid4()),
        "municipio_ibge": "5300108",  # Brasília-DF
        "uf": "DF",
        "fornecedor_sistema": "Camara",
        "url_origem": f"{CAMARA_BASE}/deputados/{deputado_id}/despesas",
    }


async def _collect_camara(deputados_limit: int, ano: int) -> dict:
    registros: list[dict] = []
    erros: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            deputados = await _fetch_camara_deputados(client, deputados_limit)
            tasks = [_fetch_camara_despesas(client, dep["id"], ano) for dep in deputados if dep.get("id")]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for dep, result in zip(deputados, results):
                dep_nome = dep.get("nome", f"Deputado {dep.get('id')}")
                if isinstance(result, Exception):
                    erros.append(f"{dep_nome}: {result}")
                else:
                    for raw in result:
                        registros.append(_normalize_camara(raw, dep_nome, dep.get("id", 0)))
    except Exception as exc:
        erros.append(f"Falha ao buscar deputados: {exc}")
    return {"registros": registros, "erros": erros}


# ---------------------------------------------------------------------------
# Portal da Transparência
# ---------------------------------------------------------------------------

async def _collect_portal(api_key: str | None, data_inicio: str, data_fim: str) -> dict:
    registros: list[dict] = []
    erros: list[str] = []
    if not api_key:
        erros.append("PORTAL_TRANSPARENCIA_API_KEY não configurada — fonte ignorada.")
        return {"registros": registros, "erros": erros}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{PORTAL_BASE}/api-de-dados/despesas",
                params={"pagina": 1, "dataInicial": data_inicio, "dataFinal": data_fim},
                headers={"chave-api-dados": api_key, "Accept": "application/json"},
            )
            resp.raise_for_status()
            payload = resp.json()
            rows = payload if isinstance(payload, list) else payload.get("dados", [])
            for raw in rows:
                favorecido = (
                    raw.get("nomeFornecedor")
                    or raw.get("nomeFavorecido")
                    or "NAO INFORMADO"
                )
                registros.append({
                    "id": str(uuid.uuid4()),
                    "categoria_origem": "Executivo Federal",
                    "agente_publico": raw.get("nomeOrgaoSuperior") or "Executivo Federal",
                    "partido": "",
                    "tipo_despesa": raw.get("elemento") or "Despesa",
                    "data_empenho": _safe_date(raw.get("dataDocumento") or raw.get("data")),
                    "valor_empenhado": _parse_float(raw.get("valor") or raw.get("valorDocumento")),
                    "favorecido_nome": favorecido,
                    "favorecido_cnpj_cpf": str(raw.get("cpfCnpj") or "").strip(),
                    "elemento_despesa": raw.get("elemento") or "",
                    "fonte_recurso": raw.get("fonteRecurso") or "",
                    "funcao_governo": raw.get("funcao") or "Executivo",
                    "numero_empenho": str(raw.get("numero") or uuid.uuid4()),
                    "municipio_ibge": "5300108",
                    "uf": raw.get("uf") or "DF",
                    "fornecedor_sistema": "Portal",
                    "url_origem": f"{PORTAL_BASE}/api-de-dados/despesas",
                })
    except Exception as exc:
        erros.append(f"Portal da Transparência: {exc}")
    return {"registros": registros, "erros": erros}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def fetch_all_sources(
    deputados_limit: int = 5,
    ano: int | None = None,
    portal_api_key: str | None = None,
) -> dict:
    """
    Fetch data from all available government APIs concurrently.
    Returns a normalized dict ready to be persisted to the database.
    """
    if ano is None:
        ano = datetime.now().year

    data_inicio = f"{ano}-01-01"
    data_fim = f"{ano}-12-31"

    camara_task = _collect_camara(deputados_limit, ano)
    portal_task = _collect_portal(portal_api_key, data_inicio, data_fim)

    camara_result, portal_result = await asyncio.gather(camara_task, portal_task)

    total = len(camara_result["registros"]) + len(portal_result["registros"])
    logger.info("data_fetch_complete", total=total, ano=ano)

    return {
        "camara": camara_result,
        "portal": portal_result,
        "total": total,
        "ano": ano,
        "timestamp": datetime.now().isoformat(),
    }
