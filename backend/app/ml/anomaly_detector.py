"""
Anomaly detection for public spending using Isolation Forest (scikit-learn).
Falls back to a percentile-based heuristic when scikit-learn is unavailable.

Module state is intentionally in-process: the model is trained once and reused
across requests. This is sufficient for a single-worker deployment.
"""
from __future__ import annotations

import math
from datetime import datetime
from typing import Any

import structlog

logger = structlog.get_logger()

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import LabelEncoder
    _HAS_SKLEARN = True
except ImportError:  # pragma: no cover
    _HAS_SKLEARN = False
    logger.warning("scikit-learn not installed — usando detecção heurística de anomalias")

# ---------------------------------------------------------------------------
# Module-level model state
# ---------------------------------------------------------------------------
_model: Any = None
_uf_encoder: Any = None
_funcao_encoder: Any = None
_trained_at: str | None = None
_training_size: int = 0


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------

def _encode_column(values: list[str], encoder: Any | None, fit: bool) -> tuple[list[float], Any]:
    if not _HAS_SKLEARN:
        # Simple integer hash fallback
        unique = {v: i for i, v in enumerate(sorted(set(values)))}
        return [float(unique.get(v, 0)) for v in values], None

    import numpy as np
    enc = encoder if (encoder is not None and not fit) else LabelEncoder()
    if fit:
        enc.fit(values)
    known = set(enc.classes_)
    safe = [v if v in known else enc.classes_[0] for v in values]
    return enc.transform(safe).astype(float).tolist(), enc


def _build_features(records: list[dict], fit: bool) -> "list[list[float]]":
    """Return a 2-D list of [log_valor, uf_enc, funcao_enc] for each record."""
    global _uf_encoder, _funcao_encoder

    import math as _math

    log_vals = [_math.log1p(max(0.0, float(r.get("valor_empenhado") or 0))) for r in records]
    ufs = [str(r.get("uf") or "XX") for r in records]
    funcoes = [str(r.get("funcao_governo") or "Outros") for r in records]

    uf_enc, new_uf_enc = _encode_column(ufs, _uf_encoder, fit=fit)
    func_enc, new_func_enc = _encode_column(funcoes, _funcao_encoder, fit=fit)

    if fit:
        _uf_encoder = new_uf_enc
        _funcao_encoder = new_func_enc

    return [[lv, ue, fe] for lv, ue, fe in zip(log_vals, uf_enc, func_enc)]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def train(records: list[dict]) -> dict:
    """Train the Isolation Forest model on spending records."""
    global _model, _trained_at, _training_size

    if len(records) < 10:
        return {"status": "error", "message": "Mínimo de 10 registros para treinar o modelo."}

    features = _build_features(records, fit=True)

    if _HAS_SKLEARN:
        import numpy as np
        X = np.array(features, dtype=float)
        _model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42,
            n_jobs=-1,
        )
        _model.fit(X)
        logger.info("isolation_forest_trained", n=len(records))
    else:
        # Heuristic: flag top 5% by value — store threshold
        values = [r.get("valor_empenhado", 0) for r in records]
        cutoff_idx = max(0, int(len(values) * 0.95))
        _model = {"threshold": sorted(values)[cutoff_idx]}
        logger.info("heuristic_threshold_set", threshold=_model["threshold"])

    _trained_at = datetime.now().isoformat()
    _training_size = len(records)

    return {
        "status": "success",
        "trained_at": _trained_at,
        "training_size": _training_size,
        "backend": "sklearn" if _HAS_SKLEARN else "heuristic",
    }


def detect(records: list[dict]) -> list[dict]:
    """
    Run anomaly detection.
    Each returned record gains two extra keys:
      - anomaly_score: float 0-1 (1 = most anomalous)
      - is_anomaly: bool
    """
    if not records:
        return []

    # Heuristic fallback (no model or no sklearn)
    if not _HAS_SKLEARN or _model is None:
        threshold: float
        if isinstance(_model, dict):
            threshold = float(_model.get("threshold", 0))
        else:
            values = sorted(float(r.get("valor_empenhado", 0)) for r in records)
            threshold = values[max(0, int(len(values) * 0.95))]
        return [
            {
                **r,
                "anomaly_score": round(
                    min(1.0, float(r.get("valor_empenhado", 0)) / max(threshold, 1)), 4
                ),
                "is_anomaly": float(r.get("valor_empenhado", 0)) >= threshold,
            }
            for r in records
        ]

    import numpy as np

    features = _build_features(records, fit=False)
    X = np.array(features, dtype=float)

    predictions = _model.predict(X)         # -1 = anomaly, 1 = normal
    raw_scores = _model.score_samples(X)    # more negative = more anomalous

    s_min, s_max = raw_scores.min(), raw_scores.max()
    rng = s_max - s_min if s_max != s_min else 1.0
    normalized = 1.0 - (raw_scores - s_min) / rng  # 0=normal, 1=anomalous

    return [
        {
            **r,
            "anomaly_score": float(round(normalized[i], 4)),
            "is_anomaly": bool(predictions[i] == -1),
        }
        for i, r in enumerate(records)
    ]


def get_status() -> dict:
    return {
        "backend": "sklearn" if _HAS_SKLEARN else "heuristic",
        "model_trained": _model is not None,
        "trained_at": _trained_at,
        "training_size": _training_size,
    }
