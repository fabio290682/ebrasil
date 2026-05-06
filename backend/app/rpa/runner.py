"""
RPA Runner — executes agents, persists records, and logs results.

Usage:
  runner = RpaRunner(db_session)
  await runner.run("camara", deputados_limit=10)
  await runner.run_pending()
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import structlog

from ..models import GastoPublico, RpaFonte, RpaLog
from .agents.base import BaseAgent
from .agents.betha_agent import BethaAgent
from .agents.brasilapi_agent import BrasilApiAgent
from .agents.camara_agent import CamaraAgent
from .agents.pncp_agent import PncpAgent
from .agents.portal_agent import PortalAgent
from .agents.senado_agent import SenadoAgent
from .agents.tce_agent import TceAgent

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()

# Registry of all available agents
_AGENTS: dict[str, BaseAgent] = {
    a.fonte_id: a
    for a in [
        CamaraAgent(),
        SenadoAgent(),
        PortalAgent(),
        PncpAgent(),
        BrasilApiAgent(),
        BethaAgent(),
        TceAgent(),
    ]
}

# In-memory lock so two parallel calls don't run the same fonte simultaneously
_RUNNING: set[str] = set()


def get_agent(fonte_id: str) -> BaseAgent | None:
    return _AGENTS.get(fonte_id)


def list_agents() -> list[BaseAgent]:
    return list(_AGENTS.values())


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


class RpaRunner:
    def __init__(self, db: "Session"):
        self.db = db

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def run(self, fonte_id: str, **fetch_kwargs) -> RpaLog:
        """Execute a single agent and persist its results."""
        if fonte_id in _RUNNING:
            raise RuntimeError(f"Fonte '{fonte_id}' já está em execução.")

        agent = get_agent(fonte_id)
        if agent is None:
            raise ValueError(f"Agente '{fonte_id}' não encontrado.")

        _RUNNING.add(fonte_id)
        log = self._start_log(fonte_id)
        try:
            records = await agent.fetch(**fetch_kwargs)
            saved, dupes = self._persist(records)
            self._finish_log(log, "success", len(records), saved, dupes)
            self._update_fonte(fonte_id, agent.intervalo_horas)
            logger.info("rpa_run_success", fonte=fonte_id, fetched=len(records), saved=saved, dupes=dupes)
        except Exception as exc:
            self._finish_log(log, "error", 0, 0, 0, mensagem=str(exc))
            logger.error("rpa_run_error", fonte=fonte_id, error=str(exc))
        finally:
            _RUNNING.discard(fonte_id)

        return log

    async def run_pending(self) -> list[str]:
        """Run all active fontes whose proxima_execucao has passed."""
        now = _now()
        fontes = (
            self.db.query(RpaFonte)
            .filter(RpaFonte.ativa == True)
            .filter(
                (RpaFonte.proxima_execucao == None) | (RpaFonte.proxima_execucao <= now)
            )
            .all()
        )
        ran: list[str] = []
        for fonte in fontes:
            if fonte.id in _RUNNING:
                continue
            try:
                await self.run(fonte.id)
                ran.append(fonte.id)
            except Exception as exc:
                logger.warning("rpa_pending_skip", fonte=fonte.id, reason=str(exc))
        return ran

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _persist(self, records: list[dict]) -> tuple[int, int]:
        saved = dupes = 0
        for rec in records:
            numero = rec.get("numero_empenho") or ""
            if numero:
                exists = (
                    self.db.query(GastoPublico)
                    .filter(
                        GastoPublico.numero_empenho == numero,
                        GastoPublico.fornecedor_sistema == rec.get("fornecedor_sistema"),
                    )
                    .first()
                )
                if exists:
                    dupes += 1
                    continue

            from datetime import date
            raw_date = rec.get("data_empenho") or ""
            try:
                empenho_date = date.fromisoformat(raw_date[:10])
            except (ValueError, TypeError):
                empenho_date = date.today()

            gasto = GastoPublico(
                id=rec["id"],
                categoria_origem=rec.get("categoria_origem"),
                agente_publico=rec.get("agente_publico"),
                partido=rec.get("partido"),
                tipo_despesa=rec.get("tipo_despesa"),
                data_empenho=empenho_date,
                valor_empenhado=float(rec.get("valor_empenhado") or 0),
                favorecido_nome=rec.get("favorecido_nome") or "NAO INFORMADO",
                favorecido_cnpj_cpf=rec.get("favorecido_cnpj_cpf"),
                elemento_despesa=rec.get("elemento_despesa"),
                fonte_recurso=rec.get("fonte_recurso"),
                funcao_governo=rec.get("funcao_governo"),
                numero_empenho=numero or None,
                municipio_ibge=rec.get("municipio_ibge") or "0000000",
                uf=rec.get("uf") or "DF",
                fornecedor_sistema=rec.get("fornecedor_sistema"),
                url_origem=rec.get("url_origem"),
            )
            self.db.add(gasto)
            saved += 1

        if saved > 0:
            self.db.commit()
        return saved, dupes

    def _start_log(self, fonte_id: str) -> RpaLog:
        log = RpaLog(
            id=str(uuid.uuid4()),
            fonte_id=fonte_id,
            status="running",
            registros_buscados=0,
            registros_salvos=0,
            registros_duplicados=0,
            iniciado_em=_now(),
        )
        self.db.add(log)
        self.db.commit()
        return log

    def _finish_log(
        self,
        log: RpaLog,
        status: str,
        buscados: int,
        salvos: int,
        dupes: int,
        mensagem: str | None = None,
    ) -> None:
        log.status = status
        log.registros_buscados = buscados
        log.registros_salvos = salvos
        log.registros_duplicados = dupes
        log.finalizado_em = _now()
        log.mensagem = mensagem
        self.db.commit()

    def _update_fonte(self, fonte_id: str, intervalo_horas: int) -> None:
        fonte = self.db.query(RpaFonte).filter(RpaFonte.id == fonte_id).first()
        if fonte:
            now = _now()
            fonte.ultima_execucao = now
            fonte.proxima_execucao = now + timedelta(hours=intervalo_horas)
            self.db.commit()


# ------------------------------------------------------------------
# DB seed helpers (called at startup)
# ------------------------------------------------------------------

def seed_fontes(db: "Session") -> None:
    """Ensure all agents have a matching RpaFonte row in the database."""
    for agent in list_agents():
        exists = db.query(RpaFonte).filter(RpaFonte.id == agent.fonte_id).first()
        if not exists:
            db.add(RpaFonte(
                id=agent.fonte_id,
                nome=agent.nome,
                descricao=agent.descricao,
                tipo=agent.tipo,
                url_base=agent.url_base,
                ativa=True,
                intervalo_horas=agent.intervalo_horas,
            ))
    db.commit()
