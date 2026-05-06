"""
Agent: Câmara dos Deputados
Source: https://dadosabertos.camara.leg.br/api/v2
Type: Direct API (no auth required)
Fetches: Deputy expenses (CEAP — Cota para Exercício da Atividade Parlamentar)
"""
from __future__ import annotations

import asyncio

import httpx

from .base import BaseAgent

_BASE = "https://dadosabertos.camara.leg.br/api/v2"


class CamaraAgent(BaseAgent):
    fonte_id = "camara"
    nome = "Câmara dos Deputados"
    descricao = "Despesas parlamentares (CEAP) dos deputados federais via API dados abertos"
    tipo = "api"
    url_base = _BASE
    intervalo_horas = 24

    async def fetch(self, deputados_limit: int = 10, ano: int | None = None, **kwargs) -> list[dict]:
        from datetime import datetime
        ano = ano or datetime.now().year
        records: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json"}) as client:
            # 1. List deputies
            resp = await client.get(
                f"{_BASE}/deputados",
                params={"itens": deputados_limit, "ordem": "ASC", "ordenarPor": "nome"},
            )
            resp.raise_for_status()
            deputados = resp.json().get("dados", [])

            # 2. Fetch expenses concurrently
            async def _get_despesas(dep: dict) -> list[dict]:
                dep_id = dep.get("id")
                dep_nome = dep.get("nome", f"Deputado {dep_id}")
                try:
                    r = await client.get(
                        f"{_BASE}/deputados/{dep_id}/despesas",
                        params={"ano": ano, "itens": 100, "pagina": 1},
                    )
                    r.raise_for_status()
                    dados = r.json().get("dados", [])
                    out = []
                    for raw in dados:
                        a = raw.get("ano", ano)
                        m = raw.get("mes", 1)
                        out.append(self.record(
                            data_empenho=raw.get("dataDocumento") or f"{a}-{m:02d}-01",
                            valor=raw.get("valorLiquido") or raw.get("valorDocumento") or 0,
                            favorecido=raw.get("nomeFornecedor") or "NAO INFORMADO",
                            categoria="Legislativo Federal",
                            agente=dep_nome,
                            partido=str(raw.get("siglaPartido") or ""),
                            tipo_despesa=raw.get("tipoDespesa") or "Cota Parlamentar",
                            cnpj_cpf=str(raw.get("cnpjCpfFornecedor") or ""),
                            funcao="Legislativo",
                            numero_empenho=str(raw.get("numDocumento") or raw.get("codDocumento") or ""),
                            url=f"{_BASE}/deputados/{dep_id}/despesas",
                        ))
                    return out
                except Exception:
                    return []

            results = await asyncio.gather(*[_get_despesas(d) for d in deputados])
            for batch in results:
                records.extend(batch)

        return records
