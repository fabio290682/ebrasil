"""
Agent: Portal da Transparência — CGU
Source: https://api.portaldatransparencia.gov.br
Type: Direct API (requires PORTAL_TRANSPARENCIA_API_KEY env var)
Fetches: Federal government despesas (empenhos, pagamentos)
"""
from __future__ import annotations

import os

import httpx

from .base import BaseAgent

_BASE = "https://api.portaldatransparencia.gov.br"


class PortalAgent(BaseAgent):
    fonte_id = "portal_transparencia"
    nome = "Portal da Transparência"
    descricao = "Despesas do Executivo Federal via API do Portal da Transparência (CGU). Requer chave API."
    tipo = "api"
    url_base = _BASE
    intervalo_horas = 12

    async def fetch(self, paginas: int = 3, ano: int | None = None, **kwargs) -> list[dict]:
        from datetime import datetime
        ano = ano or datetime.now().year
        api_key = os.getenv("PORTAL_TRANSPARENCIA_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "PORTAL_TRANSPARENCIA_API_KEY não configurada. "
                "Registre em https://portaldatransparencia.gov.br/api-de-dados/cadastrar-email"
            )

        records: list[dict] = []
        headers = {"chave-api-dados": api_key, "Accept": "application/json"}

        async with httpx.AsyncClient(timeout=40.0, headers=headers) as client:
            for pagina in range(1, paginas + 1):
                try:
                    resp = await client.get(
                        f"{_BASE}/api-de-dados/despesas",
                        params={
                            "pagina": pagina,
                            "dataInicial": f"01/01/{ano}",
                            "dataFinal": f"31/12/{ano}",
                        },
                    )
                    resp.raise_for_status()
                    rows = resp.json()
                    if not isinstance(rows, list):
                        rows = rows.get("dados", [])
                    if not rows:
                        break
                    for raw in rows:
                        records.append(self.record(
                            data_empenho=raw.get("dataDocumento") or raw.get("data") or f"{ano}-01-01",
                            valor=raw.get("valor") or raw.get("valorDocumento") or 0,
                            favorecido=raw.get("nomeFornecedor") or raw.get("nomeFavorecido") or "NAO INFORMADO",
                            categoria="Executivo Federal",
                            agente=raw.get("nomeOrgaoSuperior") or raw.get("nomeUnidadeGestora") or "Executivo Federal",
                            tipo_despesa=raw.get("elemento") or "Despesa",
                            cnpj_cpf=str(raw.get("cpfCnpj") or ""),
                            elemento=raw.get("elemento") or "",
                            funcao=raw.get("funcao") or "Executivo",
                            numero_empenho=str(raw.get("numero") or ""),
                            uf=raw.get("uf") or "DF",
                            url=f"{_BASE}/api-de-dados/despesas",
                        ))
                except Exception:
                    break

        return records
