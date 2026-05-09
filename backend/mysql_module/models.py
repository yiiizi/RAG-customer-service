"""
SQLAlchemy 2.0 async ORM models for the MySQL module.

Tables
------
- faq_pairs      High-frequency Q&A pairs
- bm25_scores    BM25 scoring records for sparse retrieval reference
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.mysql import VARCHAR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


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

    def __repr__(self) -> str:
        return f"<FAQPairs(id={self.id!r}, question={self.question[:40]!r}, freq={self.frequency})>"


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
