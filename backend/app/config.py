from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{(DATA_DIR / 'transparencia.db').as_posix()}"
DATABASE_BACKEND = os.getenv("DATABASE_BACKEND", "sqlite").strip().lower()
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://127.0.0.1:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "transparencia")
API_PREFIX = "/api/v1"
PORTAL_TRANSPARENCIA_BASE_URL = os.getenv("PORTAL_TRANSPARENCIA_BASE_URL", "https://api.portaldatransparencia.gov.br")
PORTAL_TRANSPARENCIA_API_KEY = os.getenv("PORTAL_TRANSPARENCIA_API_KEY", "")
