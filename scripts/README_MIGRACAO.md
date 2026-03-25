# Migração de Banco (SQLite <-> MongoDB)

Arquivo único:
- `scripts/db_migrate.py`

## Pré-requisito

Instale dependências do backend (inclui `pymongo`):

```powershell
cd d:\ebrasil\backend
pip install -r requirements.txt
```

## SQLite -> MongoDB

```powershell
cd d:\ebrasil
python scripts\db_migrate.py to-mongo --sqlite d:\ebrasil\backend\data\transparencia.db --mongo-uri mongodb://127.0.0.1:27017 --mongo-db transparencia
```

Dry-run (sem gravar no destino):

```powershell
python scripts\db_migrate.py to-mongo --dry-run
```

## MongoDB -> SQLite

```powershell
cd d:\ebrasil
python scripts\db_migrate.py to-sqlite --mongo-uri mongodb://127.0.0.1:27017 --mongo-db transparencia --sqlite d:\ebrasil\backend\data\transparencia.db
```

Dry-run (sem gravar no destino):

```powershell
python scripts\db_migrate.py to-sqlite --dry-run
```

## Observações

- O script usa upsert para evitar duplicação.
- `gastos_publicos` sincroniza por `id`.
- `municipios` sincroniza por `codigo_ibge`.
