#!/usr/bin/env python3
"""Importa CSVs de exports para o banco SQLite do sistema com upsert por id.

Uso:
  python scripts/import_exports.py
  python scripts/import_exports.py --db d:\\ebrasil\\backend\\data\\transparencia.db --exports-dir d:\\ebrasil\\exports
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


DEFAULT_FILES = [
    "gastos_camara.csv",
    "gastos_senado.csv",
    "gastos_executivo.csv",
    "gastos_export.csv",
]


def detect_table(cur: sqlite3.Cursor) -> str:
    for name in ("gastos_publicos", "gastos_publicos_unificados"):
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
        if cur.fetchone():
            return name
    raise RuntimeError("Nenhuma tabela alvo encontrada (gastos_publicos/gastos_publicos_unificados).")


def import_exports(db_path: Path, exports_dir: Path) -> tuple[str, int, int]:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    table = detect_table(cur)

    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]

    required = ["id", "data_empenho", "valor_empenhado", "favorecido_nome", "municipio_ibge", "uf"]
    missing = [c for c in required if c not in cols]
    if missing:
        raise RuntimeError(f"Tabela {table} sem colunas esperadas: {missing}")

    mutable_cols = [
        "data_empenho",
        "favorecido_nome",
        "favorecido_cnpj_cpf",
        "valor_empenhado",
        "funcao_governo",
        "elemento_despesa",
        "fonte_recurso",
        "uf",
        "municipio_ibge",
        "categoria_origem",
        "agente_publico",
        "partido",
        "numero_empenho",
        "fornecedor_sistema",
        "url_origem",
        "tipo_despesa",
    ]
    mutable_cols = [c for c in mutable_cols if c in cols]

    insert_cols = ["id"] + mutable_cols
    if "atualizado_em" in cols:
        insert_cols.append("atualizado_em")

    placeholders = ",".join(["?"] * len(insert_cols))
    update_cols = [f"{c}=excluded.{c}" for c in mutable_cols]
    if "atualizado_em" in cols:
        update_cols.append("atualizado_em=excluded.atualizado_em")

    sql = f"""
    INSERT INTO {table} ({', '.join(insert_cols)})
    VALUES ({placeholders})
    ON CONFLICT(id) DO UPDATE SET {', '.join(update_cols)}
    """

    processed = 0
    for filename in DEFAULT_FILES:
        path = exports_dir / filename
        if not path.exists():
            continue

        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get("id"):
                    continue

                vals = []
                for c in insert_cols:
                    if c == "atualizado_em":
                        vals.append(datetime.now(UTC).isoformat())
                        continue

                    value = row.get(c)
                    if c == "valor_empenhado":
                        try:
                            value = float(value) if value not in (None, "") else 0.0
                        except Exception:
                            value = 0.0

                    vals.append(value if value != "" else None)

                cur.execute(sql, vals)
                processed += 1

    conn.commit()
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    total = int(cur.fetchone()[0])
    conn.close()

    return table, processed, total


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default=r"d:\ebrasil\backend\data\transparencia.db")
    parser.add_argument("--exports-dir", default=r"d:\ebrasil\exports")
    args = parser.parse_args()

    table, processed, total = import_exports(Path(args.db), Path(args.exports_dir))
    print(f"table={table}")
    print(f"processed_rows={processed}")
    print(f"total_rows_now={total}")


if __name__ == "__main__":
    main()
