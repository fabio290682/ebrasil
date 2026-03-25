#!/usr/bin/env python3
"""CLI unificado para migracao de banco entre SQLite e MongoDB.

Comandos:
  python scripts/db_migrate.py to-mongo
  python scripts/db_migrate.py to-sqlite
"""

from __future__ import annotations

import argparse
import sqlite3
from datetime import UTC, date, datetime
from pathlib import Path


def _import_pymongo():
    try:
        from pymongo import MongoClient
    except ModuleNotFoundError as exc:
        raise RuntimeError("pymongo nao instalado. Rode: pip install -r backend/requirements.txt") from exc
    return MongoClient


def _to_iso_date(value):
    if value is None:
        return None
    if isinstance(value, date):
        return value.isoformat()
    text = str(value).strip()
    if not text:
        return None
    return text[:10]


def _to_iso_datetime(value):
    if value is None:
        return datetime.now(UTC).isoformat()
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat()
    text = str(value).strip()
    return text if text else datetime.now(UTC).isoformat()


def _table_cols(cur: sqlite3.Cursor, table: str) -> list[str]:
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def _upsert_sql(table: str, cols: list[str], conflict_col: str) -> str:
    placeholders = ",".join(["?"] * len(cols))
    updates = ", ".join([f"{c}=excluded.{c}" for c in cols if c != conflict_col])
    return f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({placeholders}) ON CONFLICT({conflict_col}) DO UPDATE SET {updates}"


def migrate_to_mongo(sqlite_path: Path, mongo_uri: str, mongo_db_name: str, dry_run: bool = False):
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    client = None
    db = None
    if not dry_run:
        MongoClient = _import_pymongo()
        client = MongoClient(mongo_uri)
        db = client[mongo_db_name]

    gastos_read = 0
    gastos_upserted = 0
    municipios_read = 0
    municipios_upserted = 0

    cur.execute("SELECT * FROM gastos_publicos")
    for row in cur.fetchall():
        gastos_read += 1
        doc = dict(row)
        doc["data_empenho"] = _to_iso_date(doc.get("data_empenho"))
        doc["atualizado_em"] = _to_iso_datetime(doc.get("atualizado_em"))
        if doc.get("valor_empenhado") is not None:
            doc["valor_empenhado"] = float(doc["valor_empenhado"])

        if dry_run:
            gastos_upserted += 1
        else:
            result = db.gastos_publicos.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
            if result.acknowledged:
                gastos_upserted += 1

    cur.execute("SELECT * FROM municipios")
    for row in cur.fetchall():
        municipios_read += 1
        doc = dict(row)
        if doc.get("criado_em") is not None:
            doc["criado_em"] = _to_iso_datetime(doc.get("criado_em"))

        if dry_run:
            municipios_upserted += 1
        else:
            result = db.municipios.update_one({"codigo_ibge": doc["codigo_ibge"]}, {"$set": doc}, upsert=True)
            if result.acknowledged:
                municipios_upserted += 1

    if not dry_run:
        db.gastos_publicos.create_index("id", unique=True)
        db.gastos_publicos.create_index("data_empenho")
        db.gastos_publicos.create_index("uf")
        db.gastos_publicos.create_index("municipio_ibge")

        db.municipios.create_index("codigo_ibge", unique=True)
        db.municipios.create_index("uf")

    conn.close()
    if client is not None:
        client.close()

    return {
        "gastos_read": gastos_read,
        "gastos_upserted": gastos_upserted,
        "municipios_read": municipios_read,
        "municipios_upserted": municipios_upserted,
    }


def migrate_to_sqlite(mongo_uri: str, mongo_db_name: str, sqlite_path: Path, dry_run: bool = False):
    MongoClient = _import_pymongo()

    client = MongoClient(mongo_uri)
    mdb = client[mongo_db_name]

    conn = sqlite3.connect(sqlite_path)
    cur = conn.cursor()

    gastos_cols = _table_cols(cur, "gastos_publicos")
    municipios_cols = _table_cols(cur, "municipios")

    gastos_insert_cols = [
        c
        for c in [
            "id",
            "categoria_origem",
            "agente_publico",
            "partido",
            "tipo_despesa",
            "data_empenho",
            "valor_empenhado",
            "favorecido_nome",
            "favorecido_cnpj_cpf",
            "elemento_despesa",
            "fonte_recurso",
            "funcao_governo",
            "numero_empenho",
            "municipio_ibge",
            "uf",
            "fornecedor_sistema",
            "url_origem",
            "atualizado_em",
        ]
        if c in gastos_cols
    ]

    municipios_insert_cols = [
        c
        for c in [
            "codigo_ibge",
            "nome_municipio",
            "uf",
            "nome_estado",
            "nome_regiao",
            "populacao_estimada",
            "porte_municipio",
            "latitude",
            "longitude",
            "criado_em",
        ]
        if c in municipios_cols
    ]

    sql_gastos = _upsert_sql("gastos_publicos", gastos_insert_cols, "id")
    sql_municipios = _upsert_sql("municipios", municipios_insert_cols, "codigo_ibge")

    gastos_read = 0
    gastos_upserted = 0
    municipios_read = 0
    municipios_upserted = 0

    for doc in mdb.gastos_publicos.find({}, {"_id": 0}):
        gastos_read += 1
        row = [doc.get(c) for c in gastos_insert_cols]
        if dry_run:
            gastos_upserted += 1
        else:
            cur.execute(sql_gastos, row)
            gastos_upserted += 1

    for doc in mdb.municipios.find({}, {"_id": 0}):
        municipios_read += 1
        row = [doc.get(c) for c in municipios_insert_cols]
        if dry_run:
            municipios_upserted += 1
        else:
            cur.execute(sql_municipios, row)
            municipios_upserted += 1

    if not dry_run:
        conn.commit()
    conn.close()
    client.close()

    return {
        "gastos_read": gastos_read,
        "gastos_upserted": gastos_upserted,
        "municipios_read": municipios_read,
        "municipios_upserted": municipios_upserted,
    }


def cmd_to_mongo(args):
    stats = migrate_to_mongo(Path(args.sqlite), args.mongo_uri, args.mongo_db, dry_run=args.dry_run)
    print("Dry-run SQLite -> Mongo concluido" if args.dry_run else "Migracao SQLite -> Mongo concluida")
    for k, v in stats.items():
        print(f"{k}={v}")


def cmd_to_sqlite(args):
    stats = migrate_to_sqlite(args.mongo_uri, args.mongo_db, Path(args.sqlite), dry_run=args.dry_run)
    print("Dry-run Mongo -> SQLite concluido" if args.dry_run else "Migracao Mongo -> SQLite concluida")
    for k, v in stats.items():
        print(f"{k}={v}")


def build_parser():
    parser = argparse.ArgumentParser(description="Migracao entre SQLite e MongoDB")
    sub = parser.add_subparsers(dest="command", required=True)

    p_to_mongo = sub.add_parser("to-mongo", help="Migrar dados de SQLite para MongoDB")
    p_to_mongo.add_argument("--sqlite", default=r"d:\ebrasil\backend\data\transparencia.db")
    p_to_mongo.add_argument("--mongo-uri", default="mongodb://127.0.0.1:27017")
    p_to_mongo.add_argument("--mongo-db", default="transparencia")
    p_to_mongo.add_argument("--dry-run", action="store_true", help="Simula sem gravar no Mongo")
    p_to_mongo.set_defaults(func=cmd_to_mongo)

    p_to_sqlite = sub.add_parser("to-sqlite", help="Migrar dados de MongoDB para SQLite")
    p_to_sqlite.add_argument("--mongo-uri", default="mongodb://127.0.0.1:27017")
    p_to_sqlite.add_argument("--mongo-db", default="transparencia")
    p_to_sqlite.add_argument("--sqlite", default=r"d:\ebrasil\backend\data\transparencia.db")
    p_to_sqlite.add_argument("--dry-run", action="store_true", help="Simula sem gravar no SQLite")
    p_to_sqlite.set_defaults(func=cmd_to_sqlite)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
