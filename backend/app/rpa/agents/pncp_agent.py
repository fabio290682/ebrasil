"""
Agent: PNCP — Portal Nacional de Contratações Públicas
Source: https://pncp.gov.br/api/pncp/v1
Type: Direct API (no auth required)
Fetches: Public procurement contracts (compras governamentais)
"""
from __future__ import annotations

import httpx

from .base import BaseAgent

_BASE = "https://pncp.gov.br/api/pncp/v1"


class PncpAgent(BaseAgent):
    fonte_id = "pncp"
    nome = "PNCP — Contratações Públicas"
    descricao = "Contratos e licitações via Portal Nacional de Contratações Públicas (livre acesso)"
    tipo = "api"
    url_base = _BASE
    intervalo_horas = 48

    async def fetch(self, paginas: int = 3, **kwargs) -> list[dict]:
        from datetime import datetime, date, timedelta
        records: list[dict] = []

        hoje = date.today()
        data_fim = hoje.strftime("%Y%m%d")
        data_ini = (hoje - timedelta(days=30)).strftime("%Y%m%d")

        async with httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json"}) as client:
            for pagina in range(1, paginas + 1):
                try:
                    resp = await client.get(
                        f"{_BASE}/contratacoes/publicacoes",
                        params={
                            "dataInicial": data_ini,
                            "dataFinal": data_fim,
                            "pagina": pagina,
                            "tamanhoPagina": 50,
                        },
                    )
                    resp.raise_for_status()
                    payload = resp.json()
                    rows = payload.get("data", payload) if isinstance(payload, dict) else payload
                    if not isinstance(rows, list) or not rows:
                        break

                    for raw in rows:
                        orgao = raw.get("orgaoEntidade", {}) or {}
                        records.append(self.record(
                            data_empenho=raw.get("dataPublicacaoPncp") or raw.get("dataAberturaProposta") or datetime.now().strftime("%Y-%m-%d"),
                            valor=raw.get("valorTotalEstimado") or raw.get("valorTotalHomologado") or 0,
                            favorecido=raw.get("razaoSocial") or raw.get("nomeFantasia") or "NAO INFORMADO",
                            categoria="Contratações Públicas",
                            agente=orgao.get("razaoSocial") or orgao.get("nomeFantasia") or "Órgão Público",
                            tipo_despesa=raw.get("modalidadeNome") or "Licitação",
                            cnpj_cpf=str(raw.get("cnpj") or orgao.get("cnpj") or ""),
                            funcao="Compras e Licitações",
                            numero_empenho=str(raw.get("numeroCompra") or raw.get("sequencialCompra") or ""),
                            uf=raw.get("ufNome") or raw.get("uf") or "DF",
                            url=f"{_BASE}/contratacoes/publicacoes",
                        ))
                except Exception:
                    break

        return records
