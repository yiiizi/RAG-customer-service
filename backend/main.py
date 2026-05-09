"""
FastAPI application entry point.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Workaround for OpenMP DLL conflict between torch and other libs
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Ensure backend is on sys.path so that sibling packages are importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info(f"Starting RAG server on {settings.APP_HOST}:{settings.APP_PORT}")
    logger.info(f"Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    logger.info(f"MySQL: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    logger.info(f"Embed model: {settings.EMBED_MODEL_NAME}")

    # ── Startup ───────────────────────────────────────────────────
    try:
        from mysql_module.dao import init_db
        await init_db()
        logger.info("MySQL tables verified / created")
    except Exception as e:
        logger.warning(f"MySQL init skipped (DB may be unavailable): {e}")

    try:
        from rag_qa.milvus_store import is_available
        if is_available():
            logger.info("Milvus connected")
        else:
            logger.warning("Milvus not available — retrieval disabled")
    except Exception as e:
        logger.warning(f"Milvus check skipped: {e}")

    try:
        from rag_qa.embedder import get_model
        logger.info("Pre-loading BGE-M3 embedding model...")
        get_model()
        logger.info("BGE-M3 model loaded")
    except Exception as e:
        logger.warning(f"BGE-M3 preload skipped: {e}")
    yield

    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("Shutting down RAG server")


app = FastAPI(
    title="RAG System",
    version="1.0.0",
    description="RAG QA system with Milvus, BGE-M3, MySQL, Redis",
    lifespan=lifespan,
)

# CORS — allow frontend dev-server origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dev mode — restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routes ───────────────────────────────────────────
from api.routes import router as api_router

app.include_router(api_router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/debug/flagembedding")
async def debug_flagembedding():
    import sys
    try:
        from FlagEmbedding import BGEM3FlagModel
        result = {"ok": True, "path": sys.path[:5]}
    except Exception as e:
        result = {"ok": False, "error": str(e), "path": sys.path[:5]}

    # Also check model state
    from rag_qa.embedder import _model, _import_error
    result["model_loaded"] = _model is not None
    result["import_error"] = _import_error
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
