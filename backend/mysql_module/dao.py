"""
Async Data-Access Object (DAO) layer built on SQLAlchemy 2.0.

Provides typed CRUD helpers for faq_pairs, bm25_scores, and qa_logs.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Optional, Sequence

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from backend.config.settings import settings
from backend.mysql_module.models import Base, BM25Score, FAQPair, QALog

# ── Engine & session factory ────────────────────────────────────────
engine = create_async_engine(
    settings.mysql_url,
    pool_size=settings.MYSQL_POOL_SIZE,
    pool_recycle=settings.MYSQL_POOL_RECYCLE,
    echo=settings.DEBUG,
)

async_session = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    """Create all tables (idempotent). Call once on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Yield a new session. Use as a FastAPI dependency."""
    async with async_session() as session:
        yield session


# ── FAQ ────────────────────────────────────────────────────────────

async def faq_get_by_question(session: AsyncSession, question: str) -> Optional[FAQPair]:
    """Fuzzy-match lookup for a FAQ entry.

    Strategy (in order):
    1. Exact match (after normalizing punctuation)
    2. Substring containment (shorter string is substring of longer)
    3. Longest common substring >= 4 chars
    """
    import re

    def _normalize(text: str) -> str:
        """Remove punctuation and whitespace, keep only Chinese chars."""
        return ''.join(re.findall(r'[\u4e00-\u9fff]', text))

    def _longest_common_substr(a: str, b: str) -> int:
        """Length of longest common substring."""
        if not a or not b:
            return 0
        max_len = 0
        for i in range(len(a)):
            for j in range(len(b)):
                k = 0
                while i + k < len(a) and j + k < len(b) and a[i + k] == b[j + k]:
                    k += 1
                if k > max_len:
                    max_len = k
        return max_len

    q_norm = _normalize(question)
    if len(q_norm) < 2:
        return None

    stmt = select(FAQPair).options(selectinload(FAQPair.semantic_index))
    result = await session.execute(stmt)
    all_faqs = result.scalars().all()

    best_match = None
    best_score = 0

    for faq in all_faqs:
        ext = faq.semantic_index
        if ext and ext.status != "active":
            continue
        fq_norm = _normalize(faq.question)
        if not fq_norm:
            continue

        # Score 3: Exact match
        if q_norm == fq_norm:
            return faq

        # Score 2: Substring containment
        if q_norm in fq_norm or fq_norm in q_norm:
            score = 2
        else:
            # Score 1: Longest common substring
            lcs = _longest_common_substr(q_norm, fq_norm)
            score = 1 if lcs >= 4 else 0

        if score > best_score:
            best_score = score
            best_match = faq

    return best_match if best_score >= 1 else None


async def faq_search(
    session: AsyncSession,
    keyword: str = "",
    category: str = "",
    offset: int = 0,
    limit: int = 20,
) -> Sequence[FAQPair]:
    """Search FAQ entries by keyword (LIKE) and optional category filter."""
    stmt = select(FAQPair).options(selectinload(FAQPair.semantic_index))
    if keyword:
        stmt = stmt.where(FAQPair.question.contains(keyword))
    if category:
        stmt = stmt.where(FAQPair.category == category)
    stmt = stmt.order_by(FAQPair.frequency.desc()).offset(offset).limit(limit)
    result = await session.execute(stmt)
    return result.scalars().all()


async def faq_upsert(
    session: AsyncSession,
    question: str,
    answer: str,
    category: str = "general",
) -> FAQPair:
    """Insert a new FAQ pair or update answer if the question already exists."""
    existing = await faq_get_by_question(session, question)
    if existing:
        existing.answer = answer
        existing.category = category
        existing.updated_at = datetime.utcnow()
        session.add(existing)
        await session.flush()
        return existing

    faq = FAQPair(question=question, answer=answer, category=category)
    session.add(faq)
    await session.flush()
    return faq


async def faq_increment_frequency(session: AsyncSession, question: str) -> None:
    """Atomically increment the frequency counter for a FAQ entry."""
    stmt = (
        update(FAQPair)
        .where(FAQPair.question == question)
        .values(frequency=FAQPair.frequency + 1, updated_at=datetime.utcnow())
    )
    await session.execute(stmt)
    await session.flush()


async def faq_delete(session: AsyncSession, faq_id: str) -> bool:
    """Delete a FAQ entry by id. Returns True if a row was deleted."""
    stmt = delete(FAQPair).where(FAQPair.id == faq_id)
    result = await session.execute(stmt)
    await session.flush()
    return result.rowcount > 0


async def faq_get_hot(session: AsyncSession, top_n: int = 10) -> Sequence[FAQPair]:
    """Return the top-N FAQ entries ordered by frequency."""
    stmt = select(FAQPair).options(selectinload(FAQPair.semantic_index)).order_by(FAQPair.frequency.desc()).limit(top_n)
    result = await session.execute(stmt)
    return result.scalars().all()


async def faq_total_count(session: AsyncSession) -> int:
    stmt = select(func.count()).select_from(FAQPair)
    result = await session.execute(stmt)
    return result.scalar() or 0


# ── BM25 ───────────────────────────────────────────────────────────

def _query_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


async def bm25_get_cache(session: AsyncSession, query: str) -> Optional[BM25Score]:
    """Look up a recent BM25 result for the same query text."""
    stmt = (
        select(BM25Score)
        .where(BM25Score.query_text == query)
        .order_by(BM25Score.created_at.desc())
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def bm25_save(
    session: AsyncSession,
    query_text: str,
    doc_text: str,
    score: float,
    doc_source: str = "",
) -> BM25Score:
    """Persist a BM25 score record."""
    record = BM25Score(
        query_text=query_text,
        doc_text=doc_text,
        score=score,
        doc_source=doc_source,
    )
    session.add(record)
    await session.flush()
    return record


async def bm25_cleanup_old(session: AsyncSession, days: int = 30) -> int:
    """Remove BM25 records older than `days`. Returns deleted count."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = delete(BM25Score).where(BM25Score.created_at < cutoff)
    result = await session.execute(stmt)
    await session.flush()
    return result.rowcount


# ── Q&A Logs (dashboard) ───────────────────────────────────────────

async def qalog_insert(
    session: AsyncSession,
    query: str,
    intent: str,
    answer: str = "",
    latency_ms: int = 0,
    hit_faq: bool = False,
) -> QALog:
    log = QALog(
        query_text=query,
        intent=intent,
        answer_text=answer,
        latency_ms=latency_ms,
        hit_faq=1 if hit_faq else 0,
    )
    session.add(log)
    await session.flush()
    return log


async def qalog_stats(session: AsyncSession, days: int = 30, since: datetime | None = None) -> dict:
    """Aggregate dashboard stats for the last N days."""
    if since is None:
        since = datetime.utcnow() - timedelta(days=days)

    # total
    total_stmt = select(func.count()).select_from(QALog).where(QALog.created_at >= since)
    total = (await session.execute(total_stmt)).scalar() or 0

    # avg latency
    lat_stmt = select(func.avg(QALog.latency_ms)).where(QALog.created_at >= since)
    avg_lat = (await session.execute(lat_stmt)).scalar() or 0

    # intent distribution
    intent_stmt = (
        select(QALog.intent, func.count())
        .where(QALog.created_at >= since)
        .group_by(QALog.intent)
    )
    intents = {row[0]: row[1] for row in (await session.execute(intent_stmt)).all()}

    # FAQ hit rate
    faq_hits_stmt = (
        select(func.count())
        .select_from(QALog)
        .where(QALog.created_at >= since, QALog.hit_faq == 1)
    )
    faq_hits = (await session.execute(faq_hits_stmt)).scalar() or 0

    # daily trend
    daily_stmt = (
        select(func.date(QALog.created_at), func.count())
        .where(QALog.created_at >= since)
        .group_by(func.date(QALog.created_at))
        .order_by(func.date(QALog.created_at))
    )
    daily = [{"date": str(row[0]), "count": row[1]} for row in (await session.execute(daily_stmt)).all()]

    return {
        "total_queries": total,
        "avg_latency_ms": round(float(avg_lat), 1),
        "hit_rate": round(faq_hits / total, 3) if total else 0,
        "intent_distribution": intents,
        "daily_trend": daily,
    }
