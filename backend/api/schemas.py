"""Pydantic request / response schemas for the RAG API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Chat ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096, description="User question")
    kb_only: bool = Field(False, description="Knowledge-base only mode")
    web_search: bool = Field(False, description="Enable web search augmentation")
    history: Optional[list[dict]] = Field(None, description="Conversation history")


class ChatResponse(BaseModel):
    answer: str
    intent: str
    sources: list[SourceItem] = []
    latency_ms: int = 0


class SourceItem(BaseModel):
    text: str
    source: str = ""
    score: float = 0.0
    chunk_index: int = -1


# ── Knowledge Base ──────────────────────────────────────────────────

class KBUploadResponse(BaseModel):
    status: str
    file: str = ""
    parent_chunks: int = 0
    child_chunks: int = 0
    inserted: int = 0
    error: str = ""


class KBListRequest(BaseModel):
    """No request body — uses query params."""


class KBDocumentItem(BaseModel):
    file_name: str
    file_type: str
    status: str                     # indexed / indexing / error
    chunk_count: int = 0
    created_at: Optional[str] = None


class KBListResponse(BaseModel):
    items: list[KBDocumentItem]
    total: int


class KBIndexProgress(BaseModel):
    file_name: str
    total_chunks: int
    processed_chunks: int
    progress_pct: float


class KBDeleteRequest(BaseModel):
    file_name: str


class KBDeleteResponse(BaseModel):
    status: str
    file_name: str
    chunks_removed: int


# ── FAQ ─────────────────────────────────────────────────────────────

class FAQItem(BaseModel):
    id: str
    question: str
    answer: str
    frequency: int = 0
    category: str = "general"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FAQCreateRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1024)
    answer: str = Field(..., min_length=1, max_length=8192)
    category: str = "general"


class FAQUpdateRequest(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None


class FAQListResponse(BaseModel):
    items: list[FAQItem]
    total: int


class FAQBatchImportRequest(BaseModel):
    items: list[FAQCreateRequest]


class FAQBatchImportResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str] = []


# ── Dashboard ───────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_queries: int
    avg_latency_ms: float
    hit_rate: float
    intent_distribution: dict[str, int]
    daily_trend: list[dict]
    top_faqs: list[FAQItem] = []
    milvus_stats: dict = {}


# ── Settings ────────────────────────────────────────────────────────

class SettingsUpdateRequest(BaseModel):
    llm_api_base: Optional[str] = None
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    llm_temperature: Optional[float] = None
    llm_max_tokens: Optional[int] = None
    dense_top_k: Optional[int] = None
    sparse_top_k: Optional[int] = None
    reranker_top_n: Optional[int] = None
    bm25_threshold: Optional[float] = None
    redis_faq_ttl: Optional[int] = None
    redis_hot_threshold: Optional[int] = None


class SettingsResponse(BaseModel):
    llm: dict
    retrieval: dict
    cache: dict
