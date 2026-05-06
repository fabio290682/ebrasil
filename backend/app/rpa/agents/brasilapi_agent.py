"""
Agent: Brasil API (aggregator)
Source: https://brasilapi.com.br/api
Type: Direct API (no auth required)
Fetches: CNPJ data to enrich/validate existing favorecidos
         Also fetches IBGE municipality data
"""
from __future__ import annotations

import asyncio

import httpx

from .base import BaseAgent

_BASE = "https://brasilapi.com.br/api"


class BrasilApiAgent(BaseAgent):
    fonte_id = "brasilapi"
    nome = "Brasil API — CNPJ / IBGE"
    descricao = "Enriquecimento de CNPJ e dados municipais via Brasil API (aggregador de APIs públicas)"
    tipo = "api"
    url_base = _BASE
    intervalo_horas = 168  # weekly — CNPJ data doesn't change often

    async def fetch(self, municipios_uf: str = "SP", **kwargs) -> list[dict]:
        """
        Fetches municipality list from IBGE via Brasil API.
        Returns municipality records normalised as informational GastoPublico entries
        (valor=0) — primarily useful for enriching the municipios table reference.
        """
        records: list[dict] = []

        ufs = ["SP", "RJ", "MG", "BA", "RS", "PR", "PE", "CE", "GO", "DF"]

        async with httpx.AsyncClient(timeout=20.0, headers={"Accept": "application/json"}) as client:
            async def _get_municipios(uf: str) -> list[dict]:
                try:
                    resp = await client.get(f"{_BASE}/ibge/municipios/v1/{uf}", params={"providers": "dados-abertos-br"})
                    resp.raise_for_status()
                    rows = resp.json()
                    if not isinstance(rows, list):
                        return []
                    out = []
                    for m in rows[:5]:  # sample — not full list per UF
                        out.append(self.record(
                            data_empenho="2026-01-01",
                            valor=0.0,
                            favorecido=m.get("nome") or "Municipio",
                            categoria="Referência IBGE",
                            agente="IBGE",
                            tipo_despesa="Referência Municipal",
                            funcao="Administração",
                            numero_empenho=str(m.get("codigo_ibge") or ""),
                            municipio_ibge=str(m.get("codigo_ibge") or "0000000")[:7],
                            uf=uf,
                            url=f"{_BASE}/ibge/municipios/v1/{uf}",
                        ))
                    return out
                except Exception:
                    return []

            results = await asyncio.gather(*[_get_municipios(uf) for uf in ufs])
            for batch in results:
                records.extend(batch)

        return records

    @staticmethod
    async def enrich_cnpj(cnpj: str) -> dict | None:
        """Look up a CNPJ and return company data (utility method, not part of main fetch)."""
        cnpj_clean = "".join(c for c in cnpj if c.isdigit())
        if len(cnpj_clean) != 14:
            return None
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(f"{_BASE}/cnpj/v1/{cnpj_clean}")
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return None
