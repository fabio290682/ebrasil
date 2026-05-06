"""
Base class and shared helpers for all RPA agents.
Each agent must implement: fonte_id, nome, tipo, url_base, fetch().
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any


class BaseAgent:
    fonte_id: str = ""
    nome: str = ""
    descricao: str = ""
    tipo: str = "api"          # "api" | "scraper"
    url_base: str = ""
    intervalo_horas: int = 24

    async def fetch(self, **kwargs) -> list[dict]:
        """Fetch and return normalized GastoPublico records."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Shared normalisation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def new_id() -> str:
        return str(uuid.uuid4())

    @staticmethod
    def parse_float(value: Any) -> float:
        if value is None:
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).replace("R$", "").replace(".", "").replace(",", ".").strip()
        try:
            return float(text)
        except ValueError:
            return 0.0

    @staticmethod
    def safe_date(raw: str | None, fallback_year: int | None = None) -> str:
        year = fallback_year or datetime.now().year
        if not raw:
            return f"{year}-01-01"
        raw = str(raw).strip()
        if len(raw) >= 10 and raw[4] == "-":
            return raw[:10]
        if len(raw) == 7 and raw[4] == "-":
            return f"{raw}-01"
        if "/" in raw:
            parts = raw.split("/")
            if len(parts) == 3:
                d, m, y = parts
                if len(y) == 4:
                    return f"{y}-{m.zfill(2)}-{d.zfill(2)}"
        return f"{year}-01-01"

    def record(
        self,
        data_empenho: str,
        valor: float,
        favorecido: str,
        *,
        categoria: str = "",
        agente: str = "",
        partido: str = "",
        tipo_despesa: str = "",
        cnpj_cpf: str = "",
        elemento: str = "",
        fonte_recurso: str = "",
        funcao: str = "",
        numero_empenho: str = "",
        municipio_ibge: str = "5300108",
        uf: str = "DF",
        url: str = "",
    ) -> dict:
        return {
            "id": self.new_id(),
            "categoria_origem": categoria or self.nome,
            "agente_publico": agente,
            "partido": partido,
            "tipo_despesa": tipo_despesa,
            "data_empenho": self.safe_date(data_empenho),
            "valor_empenhado": self.parse_float(valor),
            "favorecido_nome": favorecido or "NAO INFORMADO",
            "favorecido_cnpj_cpf": cnpj_cpf,
            "elemento_despesa": elemento,
            "fonte_recurso": fonte_recurso,
            "funcao_governo": funcao,
            "numero_empenho": numero_empenho or self.new_id(),
            "municipio_ibge": municipio_ibge,
            "uf": uf,
            "fornecedor_sistema": self.fonte_id,
            "url_origem": url or self.url_base,
        }
