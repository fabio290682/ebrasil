from __future__ import annotations

import threading
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import RpaFonte, RpaLog
from ..rpa import runner as rpa_runner_module
from ..rpa import scheduler as rpa_scheduler

router = APIRouter(prefix="/rpa", tags=["rpa"])

_run_lock = threading.Lock()


class FontePatch(BaseModel):
    ativa: Optional[bool] = None
    intervalo_horas: Optional[int] = None


def _fonte_to_dict(f: RpaFonte, is_running: bool = False) -> dict:
    return {
        "id": f.id,
        "nome": f.nome,
        "descricao": f.descricao,
        "tipo": f.tipo,
        "url_base": f.url_base,
        "ativa": f.ativa,
        "intervalo_horas": f.intervalo_horas,
        "ultima_execucao": f.ultima_execucao.isoformat() if f.ultima_execucao else None,
        "proxima_execucao": f.proxima_execucao.isoformat() if f.proxima_execucao else None,
        "em_execucao": is_running,
    }


def _log_to_dict(log: RpaLog) -> dict:
    return {
        "id": log.id,
        "fonte_id": log.fonte_id,
        "status": log.status,
        "registros_buscados": log.registros_buscados,
        "registros_salvos": log.registros_salvos,
        "registros_duplicados": log.registros_duplicados,
        "iniciado_em": log.iniciado_em.isoformat() if log.iniciado_em else None,
        "finalizado_em": log.finalizado_em.isoformat() if log.finalizado_em else None,
        "mensagem": log.mensagem,
        "duracao_segundos": (
            round((log.finalizado_em - log.iniciado_em).total_seconds(), 1)
            if log.finalizado_em and log.iniciado_em else None
        ),
    }


@router.get("/fontes")
def list_fontes(db: Session = Depends(get_db)):
    fontes = db.query(RpaFonte).order_by(RpaFonte.nome).all()
    return {
        "fontes": [_fonte_to_dict(f, f.id in rpa_runner_module._RUNNING) for f in fontes],
        "total": len(fontes),
    }


@router.get("/fontes/{fonte_id}")
def get_fonte(fonte_id: str, db: Session = Depends(get_db)):
    fonte = db.query(RpaFonte).filter(RpaFonte.id == fonte_id).first()
    if not fonte:
        raise HTTPException(status_code=404, detail=f"Fonte '{fonte_id}' não encontrada.")
    logs = (
        db.query(RpaLog)
        .filter(RpaLog.fonte_id == fonte_id)
        .order_by(RpaLog.iniciado_em.desc())
        .limit(10)
        .all()
    )
    return {
        **_fonte_to_dict(fonte, fonte_id in rpa_runner_module._RUNNING),
        "historico_recente": [_log_to_dict(lg) for lg in logs],
    }


@router.patch("/fontes/{fonte_id}")
def patch_fonte(fonte_id: str, body: FontePatch, db: Session = Depends(get_db)):
    fonte = db.query(RpaFonte).filter(RpaFonte.id == fonte_id).first()
    if not fonte:
        raise HTTPException(status_code=404, detail=f"Fonte '{fonte_id}' não encontrada.")
    if body.ativa is not None:
        fonte.ativa = body.ativa
    if body.intervalo_horas is not None:
        if body.intervalo_horas < 1:
            raise HTTPException(status_code=422, detail="intervalo_horas deve ser >= 1")
        fonte.intervalo_horas = body.intervalo_horas
    db.commit()
    return _fonte_to_dict(fonte)


async def _bg_run(fonte_id: str, kwargs: dict):
    from ..database import SessionLocal
    with SessionLocal() as db:
        runner = rpa_runner_module.RpaRunner(db)
        await runner.run(fonte_id, **kwargs)


@router.post("/fontes/{fonte_id}/executar")
async def executar_fonte(
    fonte_id: str,
    background_tasks: BackgroundTasks,
    ano: Optional[int] = Query(default=None),
    deputados_limit: int = Query(default=10, ge=1, le=50),
    paginas: int = Query(default=3, ge=1, le=10),
    db: Session = Depends(get_db),
):
    fonte = db.query(RpaFonte).filter(RpaFonte.id == fonte_id).first()
    if not fonte:
        raise HTTPException(status_code=404, detail=f"Fonte '{fonte_id}' não encontrada.")
    if not fonte.ativa:
        raise HTTPException(status_code=400, detail="Fonte desativada. Ative-a antes de executar.")

    with _run_lock:
        if fonte_id in rpa_runner_module._RUNNING:
            raise HTTPException(status_code=409, detail=f"Fonte '{fonte_id}' já está em execução.")
        rpa_runner_module._RUNNING.add(fonte_id)

    kwargs: dict = {"paginas": paginas}
    if ano:
        kwargs["ano"] = ano
    if fonte_id in {"camara", "senado"}:
        kwargs["deputados_limit"] = deputados_limit
        kwargs["senadores_limit"] = deputados_limit

    background_tasks.add_task(_bg_run, fonte_id, kwargs)
    return {"status": "iniciado", "fonte_id": fonte_id, "mensagem": "Execução iniciada em background."}


@router.post("/executar-pendentes")
async def executar_pendentes(background_tasks: BackgroundTasks):
    async def _run_all():
        from ..database import SessionLocal
        with SessionLocal() as db:
            runner = rpa_runner_module.RpaRunner(db)
            await runner.run_pending()

    background_tasks.add_task(_run_all)
    return {"status": "iniciado", "mensagem": "Verificação de fontes pendentes iniciada."}


@router.get("/logs")
def list_logs(
    fonte_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(RpaLog)
    if fonte_id:
        q = q.filter(RpaLog.fonte_id == fonte_id)
    if status:
        q = q.filter(RpaLog.status == status)
    logs = q.order_by(RpaLog.iniciado_em.desc()).limit(limit).all()
    return {"logs": [_log_to_dict(lg) for lg in logs], "total": len(logs)}


@router.get("/logs/{log_id}")
def get_log(log_id: str, db: Session = Depends(get_db)):
    log = db.query(RpaLog).filter(RpaLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Log não encontrado.")
    return _log_to_dict(log)


@router.get("/status")
def get_rpa_status():
    task = rpa_scheduler._task
    return {
        "scheduler_ativo": task is not None and not task.done(),
        "em_execucao": list(rpa_runner_module._RUNNING),
        "check_interval_segundos": rpa_scheduler.CHECK_INTERVAL_SECONDS,
        "agentes_registrados": [a.fonte_id for a in rpa_runner_module.list_agents()],
    }
