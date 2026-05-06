"""
Agent: Betha — Portais municipais (conexão indireta via scraping HTTP)
Source: portais de municípios que usam o sistema Betha Sistemas
Type: Scraper (indirect — HTML/JSON extraction from municipal portals)
Fetches: Municipal public spending from Betha-based portals

Betha portals expose a REST-like JSON endpoint even without official API.
Pattern: https://<municipio>.betha.cloud/contabilidade-services/api/empenhos
"""
from __future__ import annotations

import httpx

from .base import BaseAgent

# Sample municipal portals using Betha — connection is indirect (no official API)
_PORTAIS = [
    {
        "municipio": "Blumenau",
        "uf": "SC",
        "municipio_ibge": "4202404",
        "base_url": "https://transparencia.blumenau.sc.gov.br/portaltransparencia",
    },
    {
        "municipio": "Joinville",
        "uf": "SC",
        "municipio_ibge": "4209102",
        "base_url": "https://transparencia.joinville.sc.gov.br/portaltransparencia",
    },
    {
        "municipio": "Chapecó",
        "uf": "SC",
        "municipio_ibge": "4204202",
        "base_url": "https://transparencia.chapeco.sc.gov.br/portaltransparencia",
    },
]

# Betha cloud indirect endpoint pattern
_BETHA_CLOUD_PATTERN = "https://{slug}.betha.cloud/contabilidade-cloud-services/resources/empenhos"


class BethaAgent(BaseAgent):
    fonte_id = "betha"
    nome = "Betha — Portais Municipais"
    descricao = "Empenhos municipais via portais de transparência (sistema Betha Sistemas, conexão indireta)"
    tipo = "scraper"
    url_base = "https://betha.cloud"
    intervalo_horas = 48

    async def fetch(self, ano: int | None = None, **kwargs) -> list[dict]:
        from datetime import datetime
        ano = ano or datetime.now().year
        records: list[dict] = []

        async with httpx.AsyncClient(
            timeout=20.0,
            headers={
                "Accept": "application/json, text/html",
                "User-Agent": "Mozilla/5.0 (compatible; TransparenciaBR-RPA/2.0)",
            },
            follow_redirects=True,
        ) as client:
            for portal in _PORTAIS:
                slug = portal["municipio"].lower().replace(" ", "").replace("ó", "o").replace("ã", "a")
                url = _BETHA_CLOUD_PATTERN.format(slug=slug)
                rows = await self._try_betha_cloud(client, url, ano)

                if not rows:
                    rows = await self._try_portal_html(client, portal["base_url"], ano, portal)

                for raw in rows:
                    records.append(self.record(
                        data_empenho=raw.get("data") or raw.get("dataEmpenho") or f"{ano}-01-01",
                        valor=raw.get("valor") or raw.get("valorEmpenho") or 0,
                        favorecido=raw.get("favorecido") or raw.get("nomeFavorecido") or "NAO INFORMADO",
                        categoria="Executivo Municipal",
                        agente=f"Prefeitura de {portal['municipio']}",
                        tipo_despesa=raw.get("tipoDespesa") or raw.get("natureza") or "Empenho Municipal",
                        cnpj_cpf=str(raw.get("cnpjCpf") or ""),
                        funcao=raw.get("funcao") or "Administração Municipal",
                        numero_empenho=str(raw.get("numero") or raw.get("numeroEmpenho") or ""),
                        municipio_ibge=portal["municipio_ibge"],
                        uf=portal["uf"],
                        url=url,
                    ))

        return records

    async def _try_betha_cloud(self, client: httpx.AsyncClient, url: str, ano: int) -> list[dict]:
        """Try the Betha Cloud JSON endpoint directly."""
        try:
            resp = await client.get(url, params={"exercicio": ano, "pageNumber": 0, "pageSize": 50})
            if resp.status_code == 200 and "application/json" in resp.headers.get("content-type", ""):
                payload = resp.json()
                return payload.get("content", payload) if isinstance(payload, dict) else payload
        except Exception:
            pass
        return []

    async def _try_portal_html(
        self, client: httpx.AsyncClient, base_url: str, ano: int, portal: dict
    ) -> list[dict]:
        """
        Fallback: try the portal's own transparency endpoint.
        Many Betha-powered portals expose /despesas or /empenhos as JSON.
        """
        for path in ["/despesas", "/empenhos", "/api/empenhos"]:
            try:
                resp = await client.get(
                    f"{base_url}{path}",
                    params={"ano": ano, "pagina": 1},
                )
                if resp.status_code == 200:
                    try:
                        return resp.json() if isinstance(resp.json(), list) else []
                    except Exception:
                        pass
            except Exception:
                continue
        return []
