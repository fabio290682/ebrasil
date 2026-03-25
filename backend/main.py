from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.config import API_PREFIX
from app.database import SessionLocal, init_db
from app.mongo import init_mongo
from app.routers.camara import router as camara_router
from app.routers.gastos import router as gastos_router
from app.routers.health import router as health_router
from app.routers.integracoes import router as integracoes_router
from app.routers.municipios import router as municipios_router
from app.routers.stats import router as stats_router
from app.seed import seed_if_empty, seed_mongo_if_empty
from app.config import DATABASE_BACKEND


app = FastAPI(
    title="IIIbrasil — Transparência BR API",
    version="2.0.0",
    description="Plataforma de consulta de gastos públicos integrados — Schema Único.",
    docs_url="/docs",
    redoc_url="/redoc",
)

raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(gastos_router, prefix=API_PREFIX)
app.include_router(municipios_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)
app.include_router(integracoes_router, prefix=API_PREFIX)
app.include_router(camara_router, prefix=API_PREFIX)


@app.on_event("startup")
def startup():
    if DATABASE_BACKEND == "mongo":
        init_mongo()
        seed_mongo_if_empty()
        return

    init_db()
    with SessionLocal() as db:
        seed_if_empty(db)
