from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mysql_module.models import Conversation, Message, MessageFeedback

VALID_FEEDBACK_RATINGS = {"helpful", "unhelpful"}


async def get_owned_assistant_message(
    session: AsyncSession,
    *,
    message_id: int,
    user_id: int,
) -> Message | None:
    result = await session.execute(
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Message.id == message_id,
            Message.role == "assistant",
            Conversation.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def get_previous_user_message(
    session: AsyncSession,
    *,
    conversation_id: int,
    before_message_id: int,
) -> Message | None:
    result = await session.execute(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.role == "user",
            Message.id < before_message_id,
        )
        .order_by(Message.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def upsert_message_feedback(
    session: AsyncSession,
    *,
    user_id: int,
    conversation_id: int,
    message_id: int,
    rating: str,
    reason: str | None = None,
    comment: str | None = None,
) -> MessageFeedback:
    if rating not in VALID_FEEDBACK_RATINGS:
        raise ValueError("Invalid feedback rating")

    result = await session.execute(
        select(MessageFeedback).where(
            MessageFeedback.user_id == user_id,
            MessageFeedback.message_id == message_id,
        )
    )
    item = result.scalar_one_or_none()
    now = datetime.utcnow()
    if item:
        item.rating = rating
        item.reason = reason
        item.comment = comment
        item.updated_at = now
    else:
        item = MessageFeedback(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            rating=rating,
            reason=reason,
            comment=comment,
        )
        session.add(item)
    await session.flush()
    return item


async def feedback_counts_since(session: AsyncSession, since: datetime) -> dict[str, int]:
    result = await session.execute(
        select(MessageFeedback.rating, func.count(MessageFeedback.id))
        .where(MessageFeedback.created_at >= since)
        .group_by(MessageFeedback.rating)
    )
    return {str(row[0]): int(row[1]) for row in result.all()}
