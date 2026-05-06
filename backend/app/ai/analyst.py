"""
Claude AI analyst for public spending data.
Uses anthropic SDK with prompt caching and streaming.
All responses are in Brazilian Portuguese.
"""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta
from typing import Any

import anthropic
import structlog

from ..database import SessionLocal
from ..models import GastoPublico, RpaLog

logger = structlog.get_logger()

_client: anthropic.Anthropic | None = None

SYSTEM_PROMPT = """Você é um analista especializado em transparência e gastos públicos brasileiros.
Analise os dados fornecidos e produza insights objetivos, identificando:
- Padrões de gastos irregulares ou anômalos
- Fornecedores com comportamento suspeito
- Tendências relevantes por categoria ou região
- Riscos de superfaturamento ou desvios

Responda sempre em português do Brasil, de forma clara e direta.
Use linguagem acessível ao cidadão comum, mas com rigor técnico.
Formate listas com bullet points e destaque valores em reais (R$).
"""

_SYSTEM_WITH_CACHE = [
    {
        "type": "text",
        "text": SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }
]


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY não configurada.")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def _records_to_text(records: list[dict[str, Any]], limit: int = 50) -> str:
    lines = []
    for r in records[:limit]:
        linha = (
            f"- {r.get('data_empenho', '?')} | "
            f"{r.get('agente_publico', 'N/A')} ({r.get('partido', '-')}) | "
            f"R$ {r.get('valor_empenhado', 0):,.2f} | "
            f"{r.get('favorecido_nome', 'N/A')} | "
            f"{r.get('tipo_despesa', 'N/A')} | "
            f"UF: {r.get('uf', '?')}"
        )
        if r.get("is_anomaly"):
            linha += f" [ANOMALIA score={r.get('anomaly_score', 0):.2f}]"
        lines.append(linha)
    return "\n".join(lines)


def analyze_anomalies(records: list[dict[str, Any]]) -> str:
    """Ask Claude to analyze a set of flagged anomalous records."""
    client = _get_client()
    anomalias = [r for r in records if r.get("is_anomaly")]
    total = len(anomalias)
    if total == 0:
        return "Nenhuma anomalia detectada no conjunto de dados analisado."

    user_msg = (
        f"Analise as seguintes {total} transações classificadas como anômalas "
        f"pelo modelo de detecção de anomalias (Isolation Forest).\n\n"
        f"{_records_to_text(anomalias)}\n\n"
        "Por favor:\n"
        "1. Identifique os padrões mais preocupantes\n"
        "2. Aponte os fornecedores/agentes com maior risco\n"
        "3. Sugira ações investigativas prioritárias\n"
        "4. Estime o impacto financeiro potencial"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=_SYSTEM_WITH_CACHE,
        messages=[{"role": "user", "content": user_msg}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    return response.content[0].text


def classify_batch(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ask Claude to classify risk level for each record. Returns records with 'ai_classificacao' field."""
    if not records:
        return []

    client = _get_client()
    sample = records[:20]
    linhas = _records_to_text(sample, limit=20)

    user_msg = (
        "Para cada transação abaixo, classifique o risco como: BAIXO, MÉDIO, ALTO ou CRÍTICO.\n"
        "Responda no formato JSON: [{\"indice\": 0, \"risco\": \"ALTO\", \"motivo\": \"...\"}]\n\n"
        f"{linhas}"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=_SYSTEM_WITH_CACHE,
        messages=[{"role": "user", "content": user_msg}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )

    import json, re
    raw = response.content[0].text
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    classifications: list[dict] = []
    if match:
        try:
            classifications = json.loads(match.group())
        except json.JSONDecodeError:
            logger.warning("ai_classify_json_error", raw=raw[:200])

    lookup = {c["indice"]: c for c in classifications}
    result = []
    for i, rec in enumerate(sample):
        entry = dict(rec)
        cl = lookup.get(i, {})
        entry["ai_classificacao"] = cl.get("risco", "INDEFINIDO")
        entry["ai_motivo"] = cl.get("motivo", "")
        result.append(entry)
    return result


def generate_daily_report() -> str:
    """Generate a daily summary of public spending from the last 7 days."""
    client = _get_client()

    with SessionLocal() as db:
        cutoff = date.today() - timedelta(days=7)
        gastos = (
            db.query(GastoPublico)
            .filter(GastoPublico.data_empenho >= cutoff)
            .order_by(GastoPublico.valor_empenhado.desc())
            .limit(100)
            .all()
        )
        logs = (
            db.query(RpaLog)
            .filter(RpaLog.iniciado_em >= datetime.combine(cutoff, datetime.min.time()))
            .order_by(RpaLog.iniciado_em.desc())
            .limit(10)
            .all()
        )

    if not gastos:
        return "Nenhum dado de gasto público disponível para o período dos últimos 7 dias."

    total_valor = sum(g.valor_empenhado for g in gastos)
    por_categoria: dict[str, float] = {}
    for g in gastos:
        cat = g.categoria_origem or "Outros"
        por_categoria[cat] = por_categoria.get(cat, 0) + g.valor_empenhado

    top_cat = sorted(por_categoria.items(), key=lambda x: x[1], reverse=True)[:5]
    top_cat_str = "\n".join(f"  - {c}: R$ {v:,.2f}" for c, v in top_cat)

    top_gastos = gastos[:10]
    top_gastos_str = _records_to_text(
        [
            {
                "data_empenho": str(g.data_empenho),
                "agente_publico": g.agente_publico,
                "partido": g.partido,
                "valor_empenhado": g.valor_empenhado,
                "favorecido_nome": g.favorecido_nome,
                "tipo_despesa": g.tipo_despesa,
                "uf": g.uf,
            }
            for g in top_gastos
        ]
    )

    rpa_summary = ""
    if logs:
        rpa_lines = []
        for log in logs[:5]:
            dur = ""
            if log.finalizado_em and log.iniciado_em:
                dur = f" ({round((log.finalizado_em - log.iniciado_em).total_seconds())}s)"
            rpa_lines.append(
                f"  - {log.fonte_id}: {log.status}, {log.registros_salvos} registros salvos{dur}"
            )
        rpa_summary = "Coletas RPA recentes:\n" + "\n".join(rpa_lines) + "\n\n"

    user_msg = (
        f"Gere um relatório diário de transparência pública referente aos últimos 7 dias.\n\n"
        f"Total de transações analisadas: {len(gastos)}\n"
        f"Valor total empenhado: R$ {total_valor:,.2f}\n\n"
        f"Top categorias de gasto:\n{top_cat_str}\n\n"
        f"{rpa_summary}"
        f"Maiores transações:\n{top_gastos_str}\n\n"
        "Por favor, produza um relatório estruturado com:\n"
        "1. Resumo executivo (3-4 linhas)\n"
        "2. Destaques positivos e negativos\n"
        "3. Alertas e pontos de atenção\n"
        "4. Recomendações para o cidadão fiscalizar"
    )

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=_SYSTEM_WITH_CACHE,
        messages=[{"role": "user", "content": user_msg}],
        extra_headers={"anthropic-beta": "prompt-caching-2024-07-31"},
    )
    return response.content[0].text


def get_status() -> dict:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return {
        "configurado": bool(api_key),
        "modelo": "claude-sonnet-4-6",
        "prompt_caching": True,
        "funcionalidades": [
            "analisar-anomalias",
            "classificar-lote",
            "relatorio-diario",
        ],
    }
