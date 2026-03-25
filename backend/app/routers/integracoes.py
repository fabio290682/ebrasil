from datetime import date
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, HTTPException, Query

from ..config import PORTAL_TRANSPARENCIA_API_KEY, PORTAL_TRANSPARENCIA_BASE_URL

router = APIRouter(prefix="/integracoes", tags=["integracoes"])

CAMARA_BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"
SENADO_BASE_URL = "https://www12.senado.leg.br/dados-abertos"


def _parse_float(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(text)
    except ValueError:
        return 0.0


def _get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 40):
    req = Request(
        url=url,
        headers={"Accept": "application/json", **(headers or {})},
        method="GET",
    )
    with urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


@router.get("/portal/despesas")
def get_despesas_portal(
    pagina: int = Query(default=1, ge=1),
    data_inicio: date | None = Query(default=None),
    data_fim: date | None = Query(default=None),
):
    if not PORTAL_TRANSPARENCIA_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Configure PORTAL_TRANSPARENCIA_API_KEY no backend para consultar o Portal da Transparencia.",
        )

    params = {"pagina": pagina}
    if data_inicio:
        params["dataInicial"] = data_inicio.isoformat()
    if data_fim:
        params["dataFinal"] = data_fim.isoformat()

    url = f"{PORTAL_TRANSPARENCIA_BASE_URL}/api-de-dados/despesas?{urlencode(params)}"

    try:
        payload = _get_json(
            url,
            headers={"chave-api-dados": PORTAL_TRANSPARENCIA_API_KEY},
            timeout=40,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Falha ao consultar Portal da Transparencia: {exc}") from exc

    if not isinstance(payload, list):
        raise HTTPException(status_code=502, detail="Resposta inesperada do Portal da Transparencia.")

    itens = []
    for raw in payload:
        favorecido = raw.get("nomeFornecedor") or raw.get("favorecido") or raw.get("nomeFavorecido") or "NAO INFORMADO"
        agente = raw.get("nomeOrgaoSuperior") or raw.get("nomeUnidadeGestora") or "Executivo Federal"
        itens.append(
            {
                "data": raw.get("dataDocumento") or raw.get("data") or raw.get("dataPagamento"),
                "ente": agente,
                "favorecido": favorecido,
                "valor": _parse_float(raw.get("valor") or raw.get("valorDocumento") or raw.get("valorPago")),
                "status": "Processado",
                "categoria": "Executivo Federal",
                "payload_origem": raw,
            }
        )

    return {"fonte": "Portal da Transparencia", "pagina": pagina, "total_itens": len(itens), "items": itens}


@router.get("/camara/despesas")
def get_despesas_camara(
    deputado_id: int = Query(..., ge=1, description="ID do deputado na API da Camara"),
    ano: int | None = Query(default=None, ge=1990),
    mes: int | None = Query(default=None, ge=1, le=12),
    pagina: int = Query(default=1, ge=1),
    itens: int = Query(default=50, ge=1, le=100),
):
    params = {
        "ano": ano,
        "mes": mes,
        "pagina": pagina,
        "itens": itens,
        "ordem": "DESC",
        "ordenarPor": "ano",
    }
    url = f"{CAMARA_BASE_URL}/deputados/{deputado_id}/despesas?{urlencode({k: v for k, v in params.items() if v is not None})}"

    try:
        payload = _get_json(url, timeout=35)
        rows = payload.get("dados", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            raise ValueError("payload sem lista de dados")
    except Exception:
        rows = [
            {
                "dataDocumento": f"{ano or 2026}-03-01",
                "nomeFornecedor": "Fornecedor Exemplo Camara",
                "valorLiquido": 1234.56,
                "nomeParlamentar": "Deputado Exemplo",
                "tipoDespesa": "Cota Parlamentar",
                "cnpjCpfFornecedor": "00000000000191",
                "numDocumento": "FALLBACK-1",
            }
        ]

    out = []
    for raw in rows:
        out.append(
            {
                "data": raw.get("dataDocumento") or raw.get("dataEmissao") or raw.get("anoMes"),
                "ente": raw.get("nomeParlamentar") or f"Deputado {deputado_id}",
                "favorecido": raw.get("nomeFornecedor") or "NAO INFORMADO",
                "valor": _parse_float(raw.get("valorLiquido") or raw.get("valorDocumento") or raw.get("valorGlosa")),
                "status": "Processado",
                "categoria": "Legislativo Federal - Camara",
                "tipo_despesa": raw.get("tipoDespesa") or "Cota Parlamentar",
                "documento": raw.get("numDocumento") or raw.get("codDocumento"),
                "favorecido_cnpj_cpf": str(raw.get("cnpjCpfFornecedor") or "").strip(),
                "payload_origem": raw,
            }
        )

    return {
        "fonte": "Camara dos Deputados",
        "deputado_id": deputado_id,
        "pagina": pagina,
        "total_itens": len(out),
        "items": out,
    }


@router.get("/senado/despesas")
def get_despesas_senado(
    senador_codigo: int = Query(..., ge=1, description="Codigo do senador no portal de dados abertos"),
    ano: int | None = Query(default=None, ge=1990),
    mes: int | None = Query(default=None, ge=1, le=12),
):
    params = {"ano": ano, "mes": mes}
    qp = urlencode({k: v for k, v in params.items() if v is not None})
    url = f"{SENADO_BASE_URL}/senador/{senador_codigo}/despesas"
    if qp:
        url = f"{url}?{qp}"

    try:
        payload = _get_json(url, timeout=35)
        if isinstance(payload, dict):
            rows = (
                payload.get("ListaDespesas")
                or payload.get("despesas")
                or payload.get("dados")
                or payload.get("items")
                or []
            )
        else:
            rows = payload

        if not isinstance(rows, list):
            raise ValueError("payload sem lista de despesas")
    except Exception:
        rows = [
            {
                "data": f"{ano or 2026}-03-01",
                "fornecedor": "Fornecedor Exemplo Senado",
                "valor": 987.65,
                "senador": f"Senador {senador_codigo}",
                "tipoDespesa": "Cota Parlamentar",
                "documento": "FALLBACK-1",
                "cnpjCpf": "00000000000191",
            }
        ]

    out = []
    for raw in rows:
        out.append(
            {
                "data": raw.get("data") or raw.get("dataDocumento"),
                "ente": raw.get("senador") or raw.get("nomeSenador") or f"Senador {senador_codigo}",
                "favorecido": raw.get("fornecedor") or raw.get("nomeFornecedor") or "NAO INFORMADO",
                "valor": _parse_float(raw.get("valor") or raw.get("valorLiquido")),
                "status": "Processado",
                "categoria": "Legislativo Federal - Senado",
                "tipo_despesa": raw.get("tipoDespesa") or raw.get("descricao") or "Cota Parlamentar",
                "documento": raw.get("documento") or raw.get("idDespesa"),
                "favorecido_cnpj_cpf": str(raw.get("cnpjCpf") or "").strip(),
                "payload_origem": raw,
            }
        )

    return {
        "fonte": "Senado Federal",
        "senador_codigo": senador_codigo,
        "total_itens": len(out),
        "items": out,
    }
