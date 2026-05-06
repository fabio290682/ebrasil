"""
Agent: TCE (Tribunais de Contas Estaduais) — conexão indireta
Source: APIs abertas dos TCEs estaduais (SP, RJ, MG, RS, PR)
Type: Scraper/API híbrido (alguns têm API, outros requerem scraping)
Fetches: Dados de prestação de contas e julgamentos disponíveis publicamente
"""
from __future__ import annotations

import asyncio

import httpx

from .base import BaseAgent

# TCE portals with known open data endpoints
_TCE_FONTES = [
    {
        "id": "tce_sp",
        "nome": "TCE-SP",
        "uf": "SP",
        "api_url": "https://www.tce.sp.gov.br/transparencia/api",
        "dados_url": "https://transparencia.tce.sp.gov.br/municipio",
        "tipo": "api",
    },
    {
        "id": "tce_pr",
        "nome": "TCE-PR",
        "uf": "PR",
        "api_url": "https://servicos.tce.pr.gov.br/portal",
        "dados_url": "https://www1.tce.pr.gov.br/multimidia/2022/3",
        "tipo": "scraper",
    },
    {
        "id": "tcm_rj",
        "nome": "TCM-RJ",
        "uf": "RJ",
        "api_url": "https://apidados.tcm.rj.gov.br/api",
        "dados_url": "https://apidados.tcm.rj.gov.br/api/despesas",
        "tipo": "api",
    },
]


class TceAgent(BaseAgent):
    fonte_id = "tce"
    nome = "TCEs Estaduais"
    descricao = "Dados de prestação de contas via Tribunais de Contas Estaduais (conexão indireta)"
    tipo = "scraper"
    url_base = "https://tce.sp.gov.br"
    intervalo_horas = 72

    async def fetch(self, ano: int | None = None, **kwargs) -> list[dict]:
        from datetime import datetime
        ano = ano or datetime.now().year
        records: list[dict] = []

        async with httpx.AsyncClient(
            timeout=25.0,
            headers={
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (compatible; TransparenciaBR-RPA/2.0)",
            },
            follow_redirects=True,
        ) as client:
            tasks = [self._fetch_tce(client, tce, ano) for tce in _TCE_FONTES]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, list):
                    records.extend(result)

        return records

    async def _fetch_tce(self, client: httpx.AsyncClient, tce: dict, ano: int) -> list[dict]:
        """Try known endpoints for a specific TCE."""
        if tce["tipo"] == "api":
            return await self._fetch_api(client, tce, ano)
        return await self._fetch_scraper(client, tce, ano)

    async def _fetch_api(self, client: httpx.AsyncClient, tce: dict, ano: int) -> list[dict]:
        """Try direct API endpoints."""
        urls = [
            f"{tce['api_url']}/despesas?ano={ano}",
            f"{tce['api_url']}/empenhos?exercicio={ano}&pagina=1&quantidade=50",
            f"{tce['dados_url']}?ano={ano}&formato=json",
        ]
        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code == 200:
                    payload = resp.json()
                    rows = payload if isinstance(payload, list) else payload.get("data", payload.get("dados", []))
                    if isinstance(rows, list) and rows:
                        return [self._normalize_tce(r, tce, ano) for r in rows[:50]]
            except Exception:
                continue
        return []

    async def _fetch_scraper(self, client: httpx.AsyncClient, tce: dict, ano: int) -> list[dict]:
        """Indirect: try to extract JSON from HTML pages."""
        try:
            resp = await client.get(tce["dados_url"], params={"ano": ano})
            if resp.status_code != 200:
                return []
            # Try JSON first
            try:
                payload = resp.json()
                rows = payload if isinstance(payload, list) else payload.get("data", [])
                if isinstance(rows, list) and rows:
                    return [self._normalize_tce(r, tce, ano) for r in rows[:50]]
            except Exception:
                pass
        except Exception:
            pass
        return []

    def _normalize_tce(self, raw: dict, tce: dict, ano: int) -> dict:
        return self.record(
            data_empenho=raw.get("data") or raw.get("dataEmpenho") or raw.get("DataEmpenho") or f"{ano}-01-01",
            valor=raw.get("valor") or raw.get("valorEmpenho") or raw.get("ValorEmpenhado") or 0,
            favorecido=raw.get("favorecido") or raw.get("nomeFavorecido") or raw.get("NomeFavorecido") or "NAO INFORMADO",
            categoria=f"Controle Externo — {tce['nome']}",
            agente=raw.get("orgao") or raw.get("nomeOrgao") or tce["nome"],
            tipo_despesa=raw.get("natureza") or raw.get("tipoDespesa") or "Prestação de Contas",
            cnpj_cpf=str(raw.get("cnpjCpf") or raw.get("cpfCnpj") or ""),
            funcao="Controle Externo",
            numero_empenho=str(raw.get("numero") or raw.get("numeroEmpenho") or ""),
            uf=tce["uf"],
            url=tce["dados_url"],
        )
