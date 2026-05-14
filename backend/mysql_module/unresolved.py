from __future__ import annotations

import json
import re
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mysql_module.models import UnresolvedQuestion

VALID_UNRESOLVED_STATUSES = {"pending", "converted_to_faq", "ignored", "resolved"}


def normalize_question(text: str) -> str:
    value = text.strip().lower()
    value = re.sub(r"[\s\.,!?;:，。！？；：、\"'`~@#$%^&*()\[\]{}<>/\\|+=_-]+", "", value)
    return value[:191] or "empty"


async def record_unresolved_question(
    session: AsyncSession,
    *,
    question: str,
    user_id: int | None = None,
    conversation_id: int | None = None,
    message_id: int | None = None,
    ai_answer: str = "",
    reason: str = "low_confidence",
    intent: str | None = None,
    confidence: float = 0.0,
    sources: list[dict] | None = None,
) -> UnresolvedQuestion:
    normalized = normalize_question(question)
    result = await session.execute(
        select(UnresolvedQuestion).where(UnresolvedQuestion.normalized_question == normalized)
    )
    item = result.scalar_one_or_none()
    now = datetime.utcnow()
    if item:
        item.frequency += 1
        item.question = question
        item.user_id = user_id
        item.conversation_id = conversation_id
        item.message_id = message_id
        item.ai_answer = ai_answer
        item.reason = reason
        item.intent = intent
        item.confidence = confidence
        item.sources = json.dumps(sources or [], ensure_ascii=False)
        item.last_seen_at = now
        item.updated_at = now
    else:
        item = UnresolvedQuestion(
            normalized_question=normalized,
            question=question,
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            ai_answer=ai_answer,
            reason=reason,
            intent=intent,
            confidence=confidence,
            sources=json.dumps(sources or [], ensure_ascii=False),
            last_seen_at=now,
        )
        session.add(item)
    await session.flush()
    return item


async def get_unresolved_question(
    session: AsyncSession,
    unresolved_id: int,
) -> UnresolvedQuestion | None:
    result = await session.execute(
        select(UnresolvedQuestion).where(UnresolvedQuestion.id == unresolved_id)
    )
    return result.scalar_one_or_none()


async def list_unresolved_questions(
    session: AsyncSession,
    *,
    status_value: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[UnresolvedQuestion], int]:
    from sqlalchemy import func

    count_stmt = select(func.count(UnresolvedQuestion.id))
    stmt = select(UnresolvedQuestion)
    if status_value:
        count_stmt = count_stmt.where(UnresolvedQuestion.status == status_value)
        stmt = stmt.where(UnresolvedQuestion.status == status_value)
    total = (await session.execute(count_stmt)).scalar_one()
    items = (
        await session.execute(
            stmt.order_by(UnresolvedQuestion.frequency.desc(), UnresolvedQuestion.last_seen_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    ).scalars().all()
    return list(items), total


async def update_unresolved_status(
    session: AsyncSession,
    unresolved_id: int,
    status_value: str,
) -> UnresolvedQuestion | None:
    if status_value not in VALID_UNRESOLVED_STATUSES:
        raise ValueError("Invalid unresolved question status")
    item = await get_unresolved_question(session, unresolved_id)
    if not item:
        return None
    item.status = status_value
    item.updated_at = datetime.utcnow()
    await session.flush()
    return item
