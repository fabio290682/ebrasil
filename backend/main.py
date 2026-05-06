from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware as GZIPMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import os
import structlog
import logging
from contextlib import asynccontextmanager

from app.config import API_PREFIX
from app.database import SessionLocal, init_db
from app.mongo import init_mongo
from app.routers.camara import router as camara_router
from app.routers.gastos import router as gastos_router
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.integracoes import router as integracoes_router
from app.routers.ml import router as ml_router
from app.routers.rpa import router as rpa_router
from app.routers.municipios import router as municipios_router
from app.routers.stats import router as stats_router
from app.routers.ai import router as ai_router
from app.seed import seed_if_empty, seed_mongo_if_empty
from app.config import DATABASE_BACKEND
from app.rpa import scheduler as rpa_scheduler
from app.rpa.runner import seed_fontes

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)
logger = structlog.get_logger()

# Setup limiter
limiter = Limiter(key_func=get_remote_address)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting application", version=app.version)
    if DATABASE_BACKEND == "mongo":
        init_mongo()
        seed_mongo_if_empty()
        logger.info("MongoDB initialized")
    else:
        init_db()
        with SessionLocal() as db:
            seed_if_empty(db)
            seed_fontes(db)
        logger.info("SQL database initialized")
    rpa_scheduler.start()
    logger.info("RPA scheduler started")
    yield
    # Shutdown
    rpa_scheduler.stop()
    logger.info("Shutting down application")

app = FastAPI(
    title="IIIbrasil — Transparência BR API",
    version="2.0.0",
    description="Plataforma de consulta de gastos públicos integrados — Schema Único.",
    docs_url="/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT") == "development" else None,
    lifespan=lifespan,
    openapi_url="/openapi.json" if os.getenv("ENVIRONMENT") == "development" else None,
)

# Security: Trusted Host
_allowed_hosts = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)

# Compression (must be after security middleware)
app.add_middleware(GZIPMiddleware, minimum_size=1000, compresslevel=6)

# CORS
raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173")
allow_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "Origin", "X-Requested-With"],
)

# Rate limiting
app.state.limiter = limiter

# Global exception handler for rate limiting
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    logger.warning("Rate limit exceeded", path=request.url.path, client=request.client.host)
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )

# Routers
app.include_router(health_router)
app.include_router(gastos_router, prefix=API_PREFIX)
app.include_router(municipios_router, prefix=API_PREFIX)
app.include_router(stats_router, prefix=API_PREFIX)
app.include_router(integracoes_router, prefix=API_PREFIX)
app.include_router(ml_router, prefix=API_PREFIX)
app.include_router(rpa_router, prefix=API_PREFIX)
app.include_router(camara_router, prefix=API_PREFIX)
app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "IIIbrasil — Transparência BR API",
        "version": app.version,
        "docs": "/docs" if os.getenv("ENVIRONMENT") == "development" else None,
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("ENVIRONMENT") == "development",
        workers=int(os.getenv("WORKERS", 1)),
    )
