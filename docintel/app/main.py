"""
DocIntel — Agentic RAG platform. Application entrypoint.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging_config import configure_logging, logger
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware




@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode")

    from app.services.embedding_service import get_embedding_model
    from app.core.qdrant_db import ensure_collection_exists
    from app.core.redis_client import get_redis_client

    get_embedding_model()
    logger.info("Embedding model loaded")

    ensure_collection_exists()
    logger.info("Qdrant collection ready")

    get_redis_client()
    logger.info("Redis client initialized")

    yield

    logger.info("Shutting down DocIntel")


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-tenant Agentic RAG platform — bring any document, ask any question.",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else [],  # tighten to real frontend origin(s) in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RateLimitMiddleware)


app.add_middleware(RateLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}