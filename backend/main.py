"""
FastAPI 应用入口。
运行方式：在 backend/ 目录下执行  python main.py
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# 解决 torch 等库与 OpenMP 的 DLL 冲突
if "KMP_DUPLICATE_LIB_OK" not in os.environ:
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# 将 backend 目录和其父目录都加入 sys.path：
# - backend/ 本身：支持 "from api.schemas import ..." 等相对导入
# - backend 的父目录：支持 "from backend.config.settings import ..." 等绝对导入
_backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(_backend_dir))
sys.path.insert(0, str(_backend_dir.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

from backend.config.settings import settings

# 配置标准日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger("rag")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """应用启动与关闭生命周期管理。"""
    logger.info("RAG 服务器启动中：%s:%s", settings.APP_HOST, settings.APP_PORT)
    logger.info("Milvus：%s:%s", settings.MILVUS_HOST, settings.MILVUS_PORT)
    logger.info("MySQL：%s:%s", settings.MYSQL_HOST, settings.MYSQL_PORT)
    logger.info("嵌入模型：%s", settings.EMBED_MODEL_NAME)

    # ── 启动阶段 ───────────────────────────────────────────────────
    try:
        from backend.mysql_module.dao import init_db
        await init_db()
        logger.info("MySQL 表已校验/创建")
    except Exception as e:
        logger.warning("MySQL 初始化跳过（数据库可能不可用）：%s", e)

    try:
        from backend.rag_qa.milvus_store import is_available
        if is_available():
            try:
                from backend.offline_kb.indexer import _rebuild_bm25_from_all
                _rebuild_bm25_from_all()
            except Exception as e:
                logger.warning("BM25 startup rebuild skipped: %s", e)
            logger.info("Milvus 已连接")
        else:
            logger.warning("Milvus 不可用 — 检索功能已禁用")
    except Exception as e:
        logger.warning("Milvus 检查跳过：%s", e)

    try:
        from backend.rag_qa.embedder import get_model
        logger.info("正在预加载 BGE-M3 嵌入模型...")
        _ = get_model()  # pyright: ignore[reportUnknownVariableType]
        logger.info("BGE-M3 模型加载完成")
    except Exception as e:
        logger.warning("BGE-M3 预加载跳过：%s", e)
    yield

    # ── 关闭阶段 ──────────────────────────────────────────────────
    logger.info("RAG 服务器正在关闭")


app = FastAPI(
    title="RAG System",
    version="1.0.0",
    description="基于 Milvus、BGE-M3、MySQL 的 RAG 问答系统",
    lifespan=lifespan,
)

# CORS 跨域设置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 注册 API 路由 ───────────────────────────────────────────────
from backend.api.routes import router as api_router
from backend.api.auth import router as auth_router
from backend.api.conversations import router as conversations_router
from backend.api.model_config import router as model_config_router
from backend.api.admin import router as admin_router
from backend.api.tickets import router as tickets_router

app.include_router(api_router, prefix="/api")
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(model_config_router)
app.include_router(admin_router)
app.include_router(tickets_router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/debug/flagembedding")
async def debug_flagembedding() -> dict[str, object]:
    result: dict[str, object] = {}

    try:
        import FlagEmbedding  # pyright: ignore[reportMissingImports]
        _ = FlagEmbedding.BGEM3FlagModel  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        result["ok"] = True
        result["path"] = sys.path[:5]
    except Exception as e:
        result["ok"] = False
        result["error"] = str(e)
        result["path"] = sys.path[:5]

    # 检查模型加载状态，不直接访问私有变量
    try:
        from backend.rag_qa.embedder import get_model
        model = get_model()  # pyright: ignore[reportUnknownVariableType]
        result["model_loaded"] = model is not None
        result["import_error"] = None
    except Exception as e:
        result["model_loaded"] = False
        result["import_error"] = str(e)
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
