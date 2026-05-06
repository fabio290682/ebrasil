"""
AI analysis endpoints using Claude:
  GET  /api/v1/ai/status               — check if API key is configured
  POST /api/v1/ai/analisar-anomalias   — Claude analysis of anomalous records
  POST /api/v1/ai/classificar-lote     — Claude risk classification for a batch
  GET  /api/v1/ai/relatorio-diario     — Claude daily spending report
"""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel

from ..ai import analyst

router = APIRouter(prefix="/ai", tags=["ai"])


class RecordsPayload(BaseModel):
    registros: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

@router.get("/status")
def ai_status():
    return analyst.get_status()


# ---------------------------------------------------------------------------
# Anomaly analysis
# ---------------------------------------------------------------------------

@router.post("/analisar-anomalias")
def analisar_anomalias(payload: RecordsPayload):
    if not payload.registros:
        raise HTTPException(status_code=422, detail="Nenhum registro fornecido.")
    try:
        analise = analyst.analyze_anomalies(payload.registros)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"analise": analise, "total_registros": len(payload.registros)}


# ---------------------------------------------------------------------------
# Batch classification
# ---------------------------------------------------------------------------

@router.post("/classificar-lote")
def classificar_lote(payload: RecordsPayload):
    if not payload.registros:
        raise HTTPException(status_code=422, detail="Nenhum registro fornecido.")
    try:
        resultado = analyst.classify_batch(payload.registros)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"registros": resultado, "total": len(resultado)}


# ---------------------------------------------------------------------------
# Daily report (may be slow — runs synchronously, suitable for cron/admin use)
# ---------------------------------------------------------------------------

@router.get("/relatorio-diario")
def relatorio_diario():
    try:
        relatorio = analyst.generate_daily_report()
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"relatorio": relatorio}
