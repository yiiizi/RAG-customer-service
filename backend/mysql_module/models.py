"""
SQLAlchemy 2.0 async ORM models for the MySQL module.

Tables
------
- faq_pairs      High-frequency Q&A pairs
- bm25_scores    BM25 scoring records for sparse retrieval reference
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# ── FAQ Pairs ──────────────────────────────────────────────────────

class FAQPair(Base):
    __tablename__ = "faq_pairs"

    id: Mapped[str] = mapped_column(
        VARCHAR(36), primary_key=True, default=lambda: uuid.uuid4().hex
    )
    question: Mapped[str] = mapped_column(String(191), nullable=False, index=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, default=0, comment="Hit count for ranking")
    category: Mapped[str] = mapped_column(
        String(64), default="general", comment="User-defined category tag"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    semantic_index: Mapped[Optional["FAQSemanticIndex"]] = relationship(
        "FAQSemanticIndex", back_populates="faq", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<FAQPairs(id={self.id!r}, question={self.question[:40]!r}, freq={self.frequency})>"


class FAQSemanticIndex(Base):
    """Extended FAQ metadata for semantic search and review workflow."""

    __tablename__ = "faq_semantic_index"
    __table_args__ = (UniqueConstraint("faq_id", name="uq_faq_semantic_faq_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    faq_id: Mapped[str] = mapped_column(VARCHAR(36), ForeignKey("faq_pairs.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(16), default="active", nullable=False, index=True)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    similar_questions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score_threshold: Mapped[float] = mapped_column(Float, default=0.72)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    faq: Mapped["FAQPair"] = relationship("FAQPair", back_populates="semantic_index")

    def __repr__(self) -> str:
        return f"<FAQSemanticIndex(faq_id={self.faq_id!r}, status={self.status!r})>"


# ── BM25 Scores ────────────────────────────────────────────────────

class BM25Score(Base):
    __tablename__ = "bm25_scores"

    id: Mapped[str] = mapped_column(
        VARCHAR(36), primary_key=True, default=lambda: uuid.uuid4().hex
    )
    query_text: Mapped[str] = mapped_column(String(191), nullable=False, index=True)
    doc_text: Mapped[str] = mapped_column(Text, nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    doc_source: Mapped[str] = mapped_column(
        String(512), default="", comment="Source document path"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<BM25Score(id={self.id!r}, query={self.query_text[:30]!r}, score={self.score:.3f})>"


# ── Dashboard Stats (lightweight analytics) ────────────────────────

class QALog(Base):
    """Per-query log for dashboard analytics."""

    __tablename__ = "qa_logs"

    id: Mapped[str] = mapped_column(
        VARCHAR(36), primary_key=True, default=lambda: uuid.uuid4().hex
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="chat / faq / knowledge_qa"
    )
    answer_text: Mapped[str] = mapped_column(Text, default="")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    hit_faq: Mapped[bool] = mapped_column(Integer, default=0)   # 0/1
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )

    def __repr__(self) -> str:
        return f"<QALog(id={self.id!r}, intent={self.intent!r}, latency={self.latency_ms}ms)>"


class UnresolvedQuestion(Base):
    """Deduplicated unresolved user question for later FAQ/KB improvement."""

    __tablename__ = "unresolved_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    normalized_question: Mapped[str] = mapped_column(String(191), unique=True, nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=True, index=True)
    message_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    ai_answer: Mapped[str] = mapped_column(Text, default="", nullable=False)
    reason: Mapped[str] = mapped_column(String(64), default="low_confidence", nullable=False, index=True)
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(24), default="pending", nullable=False, index=True)
    frequency: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<UnresolvedQuestion(id={self.id!r}, freq={self.frequency!r}, status={self.status!r})>"


# ── Users ────────────────────────────────────────────────────────

class User(Base):
    """User table for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", comment="user, admin")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    conversations: Mapped[List["Conversation"]] = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    model_configs: Mapped[List["UserModelConfig"]] = relationship(
        "UserModelConfig", back_populates="user", cascade="all, delete-orphan"
    )
    tickets: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket",
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="SupportTicket.user_id",
    )
    assigned_tickets: Mapped[List["SupportTicket"]] = relationship(
        "SupportTicket",
        back_populates="assignee",
        foreign_keys="SupportTicket.assigned_to",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id!r}, username={self.username!r}, role={self.role!r})>"


# ── Conversations ─────────────────────────────────────────────────

class Conversation(Base):
    """Conversation session table."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id!r}, user_id={self.user_id!r}, title={self.title[:30]!r})>"


# ── Messages ──────────────────────────────────────────────────────

class Message(Base):
    """Message table for storing chat messages."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment="user, assistant")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True, comment="JSON format sources")
    intent: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    # Relationships
    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message(id={self.id!r}, conversation_id={self.conversation_id!r}, role={self.role!r})>"


class MessageFeedback(Base):
    """User feedback for an assistant message."""

    __tablename__ = "message_feedbacks"
    __table_args__ = (UniqueConstraint("user_id", "message_id", name="uq_message_feedback_user_message"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"), nullable=False, index=True)
    rating: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    reason: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<MessageFeedback(id={self.id!r}, message_id={self.message_id!r}, rating={self.rating!r})>"


# ── User Model Configs ────────────────────────────────────────────

class UserModelConfig(Base):
    """User model configuration table."""

    __tablename__ = "user_model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, comment="openai, deepseek, claude, gemini, qwen, ernie")
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(Text, nullable=False, comment="Encrypted API key")
    base_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    temperature: Mapped[float] = mapped_column(Float, default=0.7)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="model_configs")

    def __repr__(self) -> str:
        return f"<UserModelConfig(id={self.id!r}, user_id={self.user_id!r}, provider={self.provider!r})>"


class SupportTicket(Base):
    """Support ticket created when a conversation needs human follow-up."""

    __tablename__ = "support_tickets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conversation_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("conversations.id"), nullable=True, index=True
    )
    message_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("messages.id"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(32), default="general", nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="medium", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="open", nullable=False, index=True)
    summary: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    user_question: Mapped[str] = mapped_column(Text, nullable=False)
    ai_answer: Mapped[str] = mapped_column(Text, default="", nullable=False)
    public_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    debug_sources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, index=True
    )
    staff_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(
        "User", back_populates="tickets", foreign_keys=[user_id]
    )
    assignee: Mapped[Optional["User"]] = relationship(
        "User", back_populates="assigned_tickets", foreign_keys=[assigned_to]
    )

    def __repr__(self) -> str:
        return (
            f"<SupportTicket(id={self.id!r}, ticket_no={self.ticket_no!r}, "
            f"user_id={self.user_id!r}, status={self.status!r})>"
        )
