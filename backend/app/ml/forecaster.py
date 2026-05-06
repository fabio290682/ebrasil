"""
Time series forecasting for public spending.

Uses a trend-adjusted moving average when numpy is available,
or a plain mean otherwise.
"""
from __future__ import annotations


def forecast_next_months(
    monthly_data: list[dict],
    periods: int = 3,
) -> list[dict]:
    """
    Project spending for the next `periods` months.

    monthly_data: list of {"mes": "YYYY-MM", "total": float}, sorted ascending.
    Returns list of {"mes": "YYYY-MM", "total": float, "tipo": "previsao"}.
    """
    if len(monthly_data) < 3:
        return []

    sorted_data = sorted(monthly_data, key=lambda x: str(x.get("mes") or ""))
    values = [float(d.get("total") or 0) for d in sorted_data]

    window = min(6, len(values))

    try:
        import numpy as np
        recent = np.array(values[-window:])
        ma = float(np.mean(recent))
        trend = float((values[-1] - values[-window]) / window) if window > 1 else 0.0
    except ImportError:
        recent_slice = values[-window:]
        ma = sum(recent_slice) / len(recent_slice)
        trend = (values[-1] - values[-window]) / window if window > 1 else 0.0

    last_mes = str(sorted_data[-1].get("mes") or "2026-01")
    year, month = int(last_mes[:4]), int(last_mes[5:7])

    forecasts: list[dict] = []
    for i in range(1, periods + 1):
        month += 1
        if month > 12:
            month = 1
            year += 1
        forecasts.append({
            "mes": f"{year}-{month:02d}",
            "total": round(max(0.0, ma + trend * i), 2),
            "tipo": "previsao",
        })

    return forecasts
