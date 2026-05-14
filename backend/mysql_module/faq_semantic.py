from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mysql_module.models import FAQPair, FAQSemanticIndex

VALID_FAQ_STATUSES = {"draft", "rejected", "active", "inactive"}


@dataclass
class FAQMatch:
    faq: FAQPair
    score: float
    source: str


def parse_similar_questions(raw: str | None) -> list[str]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
    except Exception:
        pass
    return [item.strip() for item in raw.splitlines() if item.strip()]


def dump_similar_questions(items: list[str] | None) -> str | None:
    cleaned = [item.strip() for item in (items or []) if item and item.strip()]
    return json.dumps(cleaned, ensure_ascii=False) if cleaned else None


def _normalize(text: str) -> str:
    return "".join(re.findall(r"[\w\u4e00-\u9fff]+", text.lower()))


def _text_similarity(a: str, b: str) -> float:
    a_norm = _normalize(a)
    b_norm = _normalize(b)
    if not a_norm or not b_norm:
        return 0.0
    if a_norm == b_norm:
        return 1.0
    if a_norm in b_norm or b_norm in a_norm:
        return 0.9
    a_chars = set(a_norm)
    b_chars = set(b_norm)
    overlap = len(a_chars & b_chars)
    union = len(a_chars | b_chars)
    return overlap / union if union else 0.0


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if not norm_a or not norm_b:
        return 0.0
    return dot / (norm_a * norm_b)


def _encode_text(text: str) -> list[float] | None:
    try:
        from rag_qa.embedder import encode_single

        vec = encode_single(text)
        return [float(x) for x in vec[0]]
    except Exception:
        return None


def build_embedding_text(question: str, similar_questions: list[str] | None = None) -> str:
    values = [question.strip()] + [item.strip() for item in (similar_questions or []) if item.strip()]
    return "\n".join(values)


async def get_faq_extension(session: AsyncSession, faq_id: str) -> FAQSemanticIndex | None:
    result = await session.execute(
        select(FAQSemanticIndex).where(FAQSemanticIndex.faq_id == faq_id)
    )
    return result.scalar_one_or_none()


async def upsert_faq_extension(
    session: AsyncSession,
    faq: FAQPair,
    *,
    status: str | None = None,
    priority: int | None = None,
    similar_questions: list[str] | None = None,
    rebuild_embedding: bool = True,
) -> FAQSemanticIndex:
    ext = await get_faq_extension(session, faq.id)
    if not ext:
        ext = FAQSemanticIndex(faq_id=faq.id)
        session.add(ext)
    ext.faq = faq

    if status is not None:
        ext.status = status if status in VALID_FAQ_STATUSES else "draft"
    if priority is not None:
        ext.priority = priority
    if similar_questions is not None:
        ext.similar_questions = dump_similar_questions(similar_questions)

    if rebuild_embedding:
        questions = parse_similar_questions(ext.similar_questions)
        vector = _encode_text(build_embedding_text(faq.question, questions))
        if vector:
            ext.embedding = json.dumps(vector)

    ext.updated_at = datetime.utcnow()
    await session.flush()
    return ext


async def search_active_faq(session: AsyncSession, query: str, threshold: float = 0.72) -> FAQMatch | None:
    result = await session.execute(
        select(FAQPair)
        .options(selectinload(FAQPair.semantic_index))
        .order_by(FAQPair.frequency.desc())
    )
    faqs = list(result.scalars().all())
    if not faqs:
        return None

    best: FAQMatch | None = None

    for faq in faqs:
        ext = faq.semantic_index
        status = ext.status if ext else "active"
        if status != "active":
            continue

        candidates = [faq.question] + parse_similar_questions(ext.similar_questions if ext else None)
        text_score = max((_text_similarity(query, candidate) for candidate in candidates), default=0.0)
        faq_threshold = ext.score_threshold if ext else threshold
        priority = ext.priority if ext else 0
        if text_score >= faq_threshold and (
            best is None
            or (text_score, priority, faq.frequency) > (
                best.score,
                best.faq.semantic_index.priority if best.faq.semantic_index else 0,
                best.faq.frequency,
            )
        ):
            best = FAQMatch(faq=faq, score=text_score, source="text")

    if best:
        return best

    query_vec = _encode_text(query)
    if not query_vec:
        return None

    for faq in faqs:
        ext = faq.semantic_index
        status = ext.status if ext else "active"
        if status != "active" or not ext or not ext.embedding:
            continue

        try:
            faq_vec = json.loads(ext.embedding)
            score = _cosine(query_vec, faq_vec)
        except Exception:
            continue

        faq_threshold = ext.score_threshold if ext else threshold
        if score >= faq_threshold and (
            best is None
            or (score, ext.priority, faq.frequency) > (
                best.score,
                best.faq.semantic_index.priority if best.faq.semantic_index else 0,
                best.faq.frequency,
            )
        ):
            best = FAQMatch(faq=faq, score=score, source="embedding")

    return best


def extension_payload(faq: FAQPair) -> dict[str, Any]:
    ext = faq.semantic_index
    return {
        "status": ext.status if ext else "active",
        "priority": ext.priority if ext else 0,
        "similar_questions": parse_similar_questions(ext.similar_questions if ext else None),
    }
