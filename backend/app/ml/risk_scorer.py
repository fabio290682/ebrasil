"""
Supplier risk scoring based on spending patterns.

Score components (each 0-100, weighted):
  - value_variance: high coefficient of variation signals inconsistent pricing
  - anomaly_rate:   fraction of transactions flagged as anomalous
  - burst_pattern:  many transactions on very few distinct dates
  - geo_concentration: single-state supplier with many transactions and no CNPJ
"""
from __future__ import annotations

import math
from collections import defaultdict


def score_suppliers(records: list[dict]) -> list[dict]:
    """
    Returns a list of supplier risk profiles sorted by risk_score descending.
    Each element has:
      fornecedor, cnpj_cpf, total_transacoes, total_valor, risk_score,
      anomalias_detectadas, estados_atuacao, componentes
    """
    buckets: dict[str, dict] = defaultdict(lambda: {
        "nome": "",
        "cnpj": "",
        "valores": [],
        "ufs": set(),
        "datas": set(),
        "anomalias": 0,
        "total": 0.0,
    })

    for r in records:
        nome = str(r.get("favorecido_nome") or "NAO INFORMADO")
        cnpj = str(r.get("favorecido_cnpj_cpf") or "").strip()
        # Group by CNPJ when available; otherwise by name
        key = cnpj if cnpj and cnpj not in {"", "00000000000000", "00000000000191"} else nome

        b = buckets[key]
        b["nome"] = nome
        b["cnpj"] = cnpj
        b["valores"].append(float(r.get("valor_empenhado") or 0))
        b["ufs"].add(str(r.get("uf") or ""))
        b["datas"].add(str(r.get("data_empenho") or ""))
        b["total"] += float(r.get("valor_empenhado") or 0)
        if r.get("is_anomaly"):
            b["anomalias"] += 1

    results: list[dict] = []
    for b in buckets.values():
        vals = b["valores"]
        n = len(vals)
        if n == 0:
            continue

        mean_val = b["total"] / n

        # 1. Value variance (coefficient of variation)
        if mean_val > 0 and n > 1:
            variance = sum((v - mean_val) ** 2 for v in vals) / (n - 1)
            cv = math.sqrt(variance) / mean_val
            variance_score = min(100.0, cv * 50)
        else:
            variance_score = 0.0

        # 2. Anomaly rate
        anomaly_score = (b["anomalias"] / n) * 100

        # 3. Burst pattern (many transactions on few dates)
        unique_dates = max(1, len(b["datas"]))
        burst_ratio = n / unique_dates
        burst_score = min(100.0, (burst_ratio - 1) * 20) if burst_ratio > 1 else 0.0

        # 4. Geographic concentration (single UF, high tx count, no CNPJ)
        no_cnpj = not b["cnpj"] or b["cnpj"] in {"00000000000000", "00000000000191"}
        geo_score = 30.0 if (len(b["ufs"]) == 1 and n > 5 and no_cnpj) else 0.0

        risk = (
            variance_score * 0.35
            + anomaly_score * 0.35
            + burst_score * 0.15
            + geo_score * 0.15
        )

        results.append({
            "fornecedor": b["nome"],
            "cnpj_cpf": b["cnpj"],
            "total_transacoes": n,
            "total_valor": round(b["total"], 2),
            "risk_score": round(min(100.0, risk), 1),
            "anomalias_detectadas": b["anomalias"],
            "estados_atuacao": sorted(b["ufs"]),
            "componentes": {
                "variacao_valor": round(variance_score, 1),
                "taxa_anomalia": round(anomaly_score, 1),
                "padrao_burst": round(burst_score, 1),
                "concentracao_geo": round(geo_score, 1),
            },
        })

    results.sort(key=lambda x: x["risk_score"], reverse=True)
    return results
