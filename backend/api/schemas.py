"""Pydantic request / response schemas for the RAG API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Chat ────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096, description="User question")
    conversation_id: Optional[int] = Field(None, description="Conversation ID owned by current user")
    kb_only: bool = Field(False, description="Knowledge-base only mode")
    web_search: bool = Field(False, description="Enable web search augmentation")
    history: Optional[list[dict]] = Field(None, description="Conversation history")


class ChatResponse(BaseModel):
    answer: str
    intent: str
    sources: list[SourceItem] = []
    latency_ms: int = 0
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    need_handoff: bool = False
    ticket_no: Optional[str] = None


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
    status: str = "active"
    priority: int = 0
    similar_questions: list[str] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FAQCreateRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1024)
    answer: str = Field(..., min_length=1, max_length=8192)
    category: str = "general"
    status: Optional[str] = None
    priority: int = 0
    similar_questions: list[str] = Field(default_factory=list)


class FAQUpdateRequest(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = None
    similar_questions: Optional[list[str]] = None


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
    range: str = "7d"
    helpful_rate: float = 0.0
    unhelpful_rate: float = 0.0
    unresolved_count: int = 0
    handoff_rate: float = 0.0
    ticket_resolution_rate: float = 0.0
    faq_conversion_count: int = 0
    top_unresolved: list[dict] = []


class FeedbackRequest(BaseModel):
    rating: str = Field(..., description="helpful or unhelpful")
    reason: Optional[str] = Field(None, max_length=64)
    comment: Optional[str] = Field(None, max_length=1000)


class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    rating: str
    reason: Optional[str] = None
    comment: Optional[str] = None
    created_at: Optional[str] = None


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


# ── Authentication ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    login_type: str = Field(..., description="Login type: username, email, phone")
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=128)
    verification_code: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


# ── Conversations ───────────────────────────────────────────────

class ConversationCreateRequest(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: str
    updated_at: str


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int


# ── Messages ────────────────────────────────────────────────────

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    sources: Optional[str] = None
    intent: Optional[str] = None
    latency_ms: Optional[int] = None
    status: Optional[str] = None
    created_at: str


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int


class TicketResponse(BaseModel):
    id: int
    ticket_no: str
    user_id: int
    username: Optional[str] = None
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    category: str
    priority: str
    status: str
    summary: str
    user_question: str
    ai_answer: str
    public_sources: list[SourceItem] = Field(default_factory=list)
    debug_sources: list[SourceItem] = Field(default_factory=list)
    assigned_to: Optional[int] = None
    assigned_username: Optional[str] = None
    staff_note: Optional[str] = None
    created_at: str
    updated_at: str


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int


class TicketUpdateRequest(BaseModel):
    status: Optional[str] = Field(default=None, description="open/processing/resolved/closed")
    staff_note: Optional[str] = Field(default=None, max_length=4000)
    assigned_to: Optional[int] = None


class UnresolvedQuestionResponse(BaseModel):
    id: int
    normalized_question: str
    question: str
    user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    ai_answer: str = ""
    reason: str
    intent: Optional[str] = None
    confidence: float = 0.0
    sources: list[SourceItem] = Field(default_factory=list)
    status: str
    frequency: int
    last_seen_at: str
    created_at: str
    updated_at: str


class UnresolvedQuestionListResponse(BaseModel):
    items: list[UnresolvedQuestionResponse]
    total: int


class UnresolvedQuestionUpdateRequest(BaseModel):
    status: str = Field(..., description="pending/converted_to_faq/ignored/resolved")


class UnresolvedToFAQRequest(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    category: str = "general"
    similar_questions: list[str] = Field(default_factory=list)


# ── User Model Configs ──────────────────────────────────────────

class ModelConfigCreateRequest(BaseModel):
    provider: str = Field(..., description="openai, deepseek, claude, gemini, qwen, ernie")
    model_name: str = Field(..., min_length=1, max_length=100)
    api_key: str = Field(..., min_length=1)
    base_url: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 4096
    is_default: Optional[bool] = False


class ModelConfigUpdateRequest(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_default: Optional[bool] = None


class ModelConfigResponse(BaseModel):
    id: int
    user_id: int
    provider: str
    model_name: str
    api_key_masked: str = Field(..., description="Masked API key for display")
    base_url: Optional[str] = None
    temperature: float
    max_tokens: int
    is_default: bool
    created_at: str
    updated_at: str


class ModelConfigListResponse(BaseModel):
    items: list[ModelConfigResponse]
    total: int
