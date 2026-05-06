"""
ML endpoints:
  GET  /api/v1/ml/status               — model training status
  POST /api/v1/ml/treinar              — train model on DB records
  GET  /api/v1/ml/anomalias            — top anomalous spending records
  GET  /api/v1/ml/previsao             — monthly spending forecast
  GET  /api/v1/ml/risco-fornecedores   — supplier risk ranking
  POST /api/v1/ml/buscar-dados         — fetch fresh data from gov APIs
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import GastoPublico
from ..ml import anomaly_detector, data_fetcher, forecaster, risk_scorer

router = APIRouter(prefix="/ml", tags=["ml"])


def _get_db():
    with SessionLocal() as db:
        yield db


def _records_to_dicts(rows: list[GastoPublico]) -> list[dict]:
    return [
        {
            "id": r.id,
            "data_empenho": str(r.data_empenho),
            "valor_empenhado": r.valor_empenhado,
            "favorecido_nome": r.favorecido_nome,
            "favorecido_cnpj_cpf": r.favorecido_cnpj_cpf,
            "uf": r.uf,
            "funcao_governo": r.funcao_governo,
            "agente_publico": r.agente_publico,
            "categoria_origem": r.categoria_origem,
            "numero_empenho": r.numero_empenho,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

@router.get("/status")
def get_status():
    return {
        "status": "ok",
        "detector": anomaly_detector.get_status(),
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# Train
# ---------------------------------------------------------------------------

@router.post("/treinar")
def treinar(db: Session = Depends(_get_db)):
    """Train the anomaly detection model on records in the database."""
    rows = db.query(GastoPublico).limit(5000).all()
    if not rows:
        raise HTTPException(status_code=400, detail="Sem dados no banco para treinar o modelo.")

    result = anomaly_detector.train(_records_to_dicts(rows))
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result["message"])
    return result


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

@router.get("/anomalias")
def get_anomalias(
    limit: int = Query(default=50, ge=1, le=200),
    uf: Optional[str] = Query(default=None),
    apenas_anomalias: bool = Query(default=True),
    db: Session = Depends(_get_db),
):
    """Detect and return anomalous spending records."""
    q = db.query(GastoPublico)
    if uf:
        q = q.filter(GastoPublico.uf == uf.upper())
    rows = q.order_by(GastoPublico.valor_empenhado.desc()).limit(1000).all()

    if not rows:
        return {"anomalias": [], "total": 0, "total_analisados": 0, "modelo": anomaly_detector.get_status()}

    data = _records_to_dicts(rows)

    # Auto-train when no model exists yet
    if anomaly_detector._model is None:
        anomaly_detector.train(data)

    detected = anomaly_detector.detect(data)

    if apenas_anomalias:
        detected = [r for r in detected if r.get("is_anomaly")]

    detected.sort(key=lambda x: x.get("anomaly_score", 0), reverse=True)

    return {
        "anomalias": detected[:limit],
        "total": len(detected),
        "total_analisados": len(rows),
        "modelo": anomaly_detector.get_status(),
    }


# ---------------------------------------------------------------------------
# Forecast
# ---------------------------------------------------------------------------

@router.get("/previsao")
def get_previsao(
    periodos: int = Query(default=3, ge=1, le=12),
    db: Session = Depends(_get_db),
):
    """Forecast spending for the next N months using a trend-adjusted moving average."""
    rows = (
        db.query(
            func.strftime("%Y-%m", GastoPublico.data_empenho).label("mes"),
            func.sum(GastoPublico.valor_empenhado).label("total"),
        )
        .group_by(func.strftime("%Y-%m", GastoPublico.data_empenho))
        .order_by("mes")
        .all()
    )

    historico = [
        {"mes": r.mes, "total": float(r.total or 0), "tipo": "historico"}
        for r in rows
        if r.mes
    ]

    if len(historico) < 3:
        return {
            "historico": historico,
            "previsao": [],
            "periodos": periodos,
            "mensagem": "Dados insuficientes para previsão (mínimo 3 meses).",
        }

    previsao = forecaster.forecast_next_months(historico, periods=periodos)

    return {
        "historico": historico,
        "previsao": previsao,
        "periodos": periodos,
    }


# ---------------------------------------------------------------------------
# Supplier risk
# ---------------------------------------------------------------------------

@router.get("/risco-fornecedores")
def get_risco_fornecedores(
    limit: int = Query(default=20, ge=1, le=100),
    min_score: float = Query(default=0.0, ge=0, le=100),
    db: Session = Depends(_get_db),
):
    """Rank suppliers by composite risk score."""
    rows = db.query(GastoPublico).limit(5000).all()
    data = _records_to_dicts(rows)

    if data:
        if anomaly_detector._model is None:
            anomaly_detector.train(data)
        data = anomaly_detector.detect(data)

    scored = risk_scorer.score_suppliers(data)
    filtered = [s for s in scored if s["risk_score"] >= min_score]

    return {
        "fornecedores": filtered[:limit],
        "total": len(filtered),
    }


# ---------------------------------------------------------------------------
# Data fetch from external sources
# ---------------------------------------------------------------------------

@router.post("/buscar-dados")
async def buscar_dados(
    fonte: str = Query(default="camara", enum=["camara", "todas"]),
    ano: Optional[int] = Query(default=None),
    deputados_limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(_get_db),
):
    """
    Fetch spending data directly from government APIs and persist to the database.
    Skips duplicate records (matched by numero_empenho).
    """
    import os

    portal_key = os.getenv("PORTAL_TRANSPARENCIA_API_KEY") if fonte == "todas" else None

    result = await data_fetcher.fetch_all_sources(
        deputados_limit=deputados_limit,
        ano=ano,
        portal_api_key=portal_key,
    )

    saved = 0
    erros: list[str] = []

    all_registros = (
        result.get("camara", {}).get("registros", [])
        + result.get("portal", {}).get("registros", [])
    )

    for reg in all_registros:
        try:
            numero = reg.get("numero_empenho") or ""
            if numero:
                existing = (
                    db.query(GastoPublico)
                    .filter(GastoPublico.numero_empenho == numero)
                    .first()
                )
                if existing:
                    continue

            raw_date = reg.get("data_empenho") or ""
            try:
                empenho_date = date.fromisoformat(raw_date[:10])
            except (ValueError, TypeError):
                empenho_date = date.today()

            gasto = GastoPublico(
                id=reg["id"],
                categoria_origem=reg.get("categoria_origem"),
                agente_publico=reg.get("agente_publico"),
                partido=reg.get("partido"),
                tipo_despesa=reg.get("tipo_despesa"),
                data_empenho=empenho_date,
                valor_empenhado=float(reg.get("valor_empenhado") or 0),
                favorecido_nome=reg.get("favorecido_nome") or "NAO INFORMADO",
                favorecido_cnpj_cpf=reg.get("favorecido_cnpj_cpf"),
                elemento_despesa=reg.get("elemento_despesa"),
                fonte_recurso=reg.get("fonte_recurso"),
                funcao_governo=reg.get("funcao_governo"),
                numero_empenho=numero or None,
                municipio_ibge=reg.get("municipio_ibge") or "0000000",
                uf=reg.get("uf") or "DF",
                fornecedor_sistema=reg.get("fornecedor_sistema"),
                url_origem=reg.get("url_origem"),
            )
            db.add(gasto)
            saved += 1
        except Exception as exc:
            erros.append(str(exc))

    if saved > 0:
        db.commit()

        # Invalidate model so next anomaly call retrains on fresh data
        anomaly_detector._model = None

    return {
        "status": "ok",
        "fonte": fonte,
        "ano": result.get("ano"),
        "registros_buscados": result.get("total", 0),
        "registros_salvos": saved,
        "erros": erros[:10],
        "fontes_erros": {
            "camara": result.get("camara", {}).get("erros", []),
            "portal": result.get("portal", {}).get("erros", []),
        },
        "timestamp": result.get("timestamp"),
    }
