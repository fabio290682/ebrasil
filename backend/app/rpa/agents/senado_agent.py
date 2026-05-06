"""
Agent: Senado Federal
Source: https://legis.senado.leg.br/dadosabertos/senador/lista/atual
Type: Direct API (no auth required)
Fetches: Senator list + CEAPS (parliamentary allowance) expenses
"""
from __future__ import annotations

import asyncio

import httpx

from .base import BaseAgent

_BASE = "https://legis.senado.leg.br/dadosabertos"
_CEAPS = "https://www.senado.leg.br/transparencia/LAI/verba"


class SenadoAgent(BaseAgent):
    fonte_id = "senado"
    nome = "Senado Federal"
    descricao = "Despesas dos senadores (CEAPS) via API dados abertos do Senado"
    tipo = "api"
    url_base = _BASE
    intervalo_horas = 24

    async def fetch(self, senadores_limit: int = 10, ano: int | None = None, **kwargs) -> list[dict]:
        from datetime import datetime
        ano = ano or datetime.now().year
        records: list[dict] = []

        async with httpx.AsyncClient(timeout=30.0, headers={"Accept": "application/json"}) as client:
            # 1. List current senators
            try:
                resp = await client.get(f"{_BASE}/senador/lista/atual.json")
                resp.raise_for_status()
                payload = resp.json()
                senadores_raw = (
                    payload.get("ListaParlamentarEmExercicio", {})
                    .get("Parlamentares", {})
                    .get("Parlamentar", [])
                )
                if isinstance(senadores_raw, dict):
                    senadores_raw = [senadores_raw]
                senadores = senadores_raw[:senadores_limit]
            except Exception:
                senadores = []

            # 2. Fetch expenses for each senator
            async def _get_despesas(sen: dict) -> list[dict]:
                try:
                    id_parlamentar = (
                        sen.get("IdentificacaoParlamentar", {}).get("CodigoParlamentar")
                        or sen.get("CodigoParlamentar")
                    )
                    nome = (
                        sen.get("IdentificacaoParlamentar", {}).get("NomeParlamentar")
                        or sen.get("NomeParlamentar")
                        or f"Senador {id_parlamentar}"
                    )
                    partido = (
                        sen.get("IdentificacaoParlamentar", {}).get("SiglaPartidoParlamentar")
                        or ""
                    )
                    uf_sen = (
                        sen.get("IdentificacaoParlamentar", {}).get("UfParlamentar")
                        or "DF"
                    )

                    r = await client.get(
                        f"{_BASE}/senador/{id_parlamentar}/despesas.json",
                        params={"ano": ano},
                    )
                    r.raise_for_status()
                    dados = r.json()
                    despesas = (
                        dados.get("CeapsSenador", {})
                        .get("Itens", {})
                        .get("Item", [])
                    )
                    if isinstance(despesas, dict):
                        despesas = [despesas]

                    out = []
                    for raw in despesas:
                        out.append(self.record(
                            data_empenho=raw.get("DataDocumento") or f"{ano}-01-01",
                            valor=raw.get("ValorReembolsado") or raw.get("ValorDocumento") or 0,
                            favorecido=raw.get("NomeFornecedor") or "NAO INFORMADO",
                            categoria="Legislativo Federal",
                            agente=str(nome),
                            partido=str(partido),
                            tipo_despesa=raw.get("DescricaoSubTipoDespesa") or "CEAPS",
                            cnpj_cpf=str(raw.get("CnpjCpf") or ""),
                            funcao="Legislativo",
                            numero_empenho=str(raw.get("NumeroDocumento") or ""),
                            uf=str(uf_sen),
                            url=f"{_BASE}/senador/{id_parlamentar}/despesas.json",
                        ))
                    return out
                except Exception:
                    return []

            results = await asyncio.gather(*[_get_despesas(s) for s in senadores])
            for batch in results:
                records.extend(batch)

        return records
