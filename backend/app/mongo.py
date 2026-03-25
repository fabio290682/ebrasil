from .config import MONGODB_DB, MONGODB_URL

MongoClientType = object
_client: MongoClientType | None = None


def _import_pymongo():
    try:
        from pymongo import ASCENDING, DESCENDING, MongoClient
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pymongo nao instalado. Rode: pip install -r requirements.txt para usar MongoDB."
        ) from exc
    return ASCENDING, DESCENDING, MongoClient


def get_mongo_client():
    global _client
    if _client is None:
        _, _, MongoClient = _import_pymongo()
        _client = MongoClient(MONGODB_URL)
    return _client


def get_mongo_db():
    return get_mongo_client()[MONGODB_DB]


def init_mongo():
    ASCENDING, DESCENDING, _ = _import_pymongo()
    db = get_mongo_db()
    db.gastos_publicos.create_index([("id", ASCENDING)], unique=True)
    db.gastos_publicos.create_index([("data_empenho", DESCENDING)])
    db.gastos_publicos.create_index([("uf", ASCENDING)])
    db.gastos_publicos.create_index([("municipio_ibge", ASCENDING)])
    db.gastos_publicos.create_index([("categoria_origem", ASCENDING)])
    db.gastos_publicos.create_index([("agente_publico", ASCENDING)])
    db.gastos_publicos.create_index([("partido", ASCENDING)])

    db.municipios.create_index([("codigo_ibge", ASCENDING)], unique=True)
    db.municipios.create_index([("uf", ASCENDING)])
    db.municipios.create_index([("nome_municipio", ASCENDING)])
