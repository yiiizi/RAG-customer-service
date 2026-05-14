"""
Global configuration via Pydantic Settings.

All values can be overridden by environment variables (e.g. MYSQL_HOST, REDIS_URL, etc.)
"""

import os
from typing import ClassVar

# Force offline mode for HuggingFace — must happen BEFORE any HF imports
_ = os.environ.setdefault("HF_HUB_OFFLINE", "1")
_ = os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
# Workaround for OpenMP DLL conflict on Windows
_ = os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config: ClassVar[SettingsConfigDict] = {
        "env_file": str(Path(__file__).resolve().parent / ".env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }

    # ── Application ──────────────────────────────────────────────
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True
    PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
    LOG_LEVEL: str = "INFO"

    # ── MySQL ────────────────────────────────────────────────────
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "rag_db"
    MYSQL_POOL_SIZE: int = 20
    MYSQL_POOL_RECYCLE: int = 3600

    @property
    def mysql_url(self) -> str:
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def mysql_sync_url(self) -> str:
        return self.mysql_url.replace("+aiomysql", "+pymysql")

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    REDIS_POOL_SIZE: int = 20
    REDIS_FAQ_TTL: int = 86_400            # 24h for normal FAQ
    REDIS_FAQ_HOT_TTL: int = 604_800       # 7d for hot FAQ
    REDIS_FAQ_HOT_THRESHOLD: int = 10      # frequency > this => hot
    REDIS_BM25_TTL: int = 3_600            # 1h for BM25 cache

    # ── Milvus ───────────────────────────────────────────────────
    MILVUS_HOST: str = "127.0.0.1"
    MILVUS_PORT: int = 19530
    MILVUS_DB_NAME: str = "default"
    MILVUS_COLLECTION: str = "knowledge_base"
    MILVUS_DIM: int = 1024                # BGE-M3 dimension
    MILVUS_INDEX_TYPE: str = "IVF_FLAT"
    MILVUS_NLIST: int = 1024
    MILVUS_METRIC_TYPE: str = "IP"        # Inner Product (BGE-M3 uses normalised vectors)

    # ── Embedding (BGE-M3) ───────────────────────────────────────
    EMBED_MODEL_NAME: str = "BAAI/bge-m3"
    EMBED_DEVICE: str = "cuda"            # "cpu" or "cuda"
    EMBED_BATCH_SIZE: int = 32
    EMBED_MAX_LENGTH: int = 8192          # BGE-M3 max input length

    # ── Reranker (BGE-Reranker) ─────────────────────────────────
    RERANKER_MODEL_NAME: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_DEVICE: str = "cuda"
    RERANKER_TOP_N: int = 5

    # ── Retrieval ─────────────────────────────────────────────────
    DENSE_TOP_K: int = 10                 # Milvus ANN top-k
    SPARSE_TOP_K: int = 10                # BM25 top-k
    RRF_K: int = 60                       # Reciprocal Rank Fusion constant
    BM25_SCORE_THRESHOLD: float = 0.5     # BM25 confidence threshold

    # ── Chunking ──────────────────────────────────────────────────
    PARENT_CHUNK_SIZE: int = 1024         # tokens
    CHILD_CHUNK_SIZE: int = 256           # tokens
    CHUNK_OVERLAP: int = 64               # tokens

    # ── LLM ───────────────────────────────────────────────────────
    LLM_API_BASE: str = "https://api.openai.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096
    LLM_TIMEOUT: int = 60                 # seconds

    # ── Intent Recognition ────────────────────────────────────────
    INTENT_LLM_MODEL: str = ""            # fallback to LLM_MODEL if empty
    INTENT_RULE_THRESHOLD: float = 0.6    # keyword-rule confidence floor

    # ── Knowledge Base ────────────────────────────────────────────
    KB_UPLOAD_DIR: Path = Path(__file__).resolve().parent.parent / "data" / "uploads"
    KB_SUPPORTED_EXTENSIONS: set[str] = {
        ".pdf", ".docx", ".txt", ".md", ".html", ".htm",
        ".csv", ".xlsx", ".pptx", ".json", ".epub",
        ".png", ".jpg", ".jpeg",
        ".py", ".java", ".go", ".js", ".ts", ".cpp", ".c",
    }
    KB_MAX_FILE_SIZE_MB: int = 50
    KB_OCR_ENABLED: bool = True

    # ── FAQ ───────────────────────────────────────────────────────
    FAQ_CACHE_MAX_SIZE: int = 10_000      # max cached FAQ entries in Redis

    # ── Web Search (Tavily) ───────────────────────────────────────
    TAVILY_API_KEY: str = ""

    # ── JWT Authentication ──────────────────────────────────────
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7


settings = Settings()
