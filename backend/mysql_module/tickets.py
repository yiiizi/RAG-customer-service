from __future__ import annotations

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from mysql_module.models import SupportTicket


def _ticket_query():
    return select(SupportTicket).options(
        selectinload(SupportTicket.user),
        selectinload(SupportTicket.assignee),
    )


async def create_ticket(
    session: AsyncSession,
    *,
    ticket_no: str,
    user_id: int,
    conversation_id: int | None,
    message_id: int | None,
    category: str,
    priority: str,
    summary: str,
    user_question: str,
    ai_answer: str,
    public_sources: str | None = None,
    debug_sources: str | None = None,
) -> SupportTicket:
    ticket = SupportTicket(
        ticket_no=ticket_no,
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        category=category,
        priority=priority,
        status="open",
        summary=summary,
        user_question=user_question,
        ai_answer=ai_answer,
        public_sources=public_sources,
        debug_sources=debug_sources,
    )
    session.add(ticket)
    await session.flush()
    return ticket


async def get_ticket(session: AsyncSession, ticket_id: int) -> Optional[SupportTicket]:
    result = await session.execute(
        _ticket_query().where(SupportTicket.id == ticket_id)
    )
    return result.scalar_one_or_none()


async def list_user_tickets(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[SupportTicket], int]:
    count_stmt = select(func.count(SupportTicket.id)).where(SupportTicket.user_id == user_id)
    total = (await session.execute(count_stmt)).scalar_one()
    stmt = (
        _ticket_query()
        .where(SupportTicket.user_id == user_id)
        .order_by(SupportTicket.updated_at.desc(), SupportTicket.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()
    return list(items), total


async def list_staff_tickets(
    session: AsyncSession,
    status_value: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[SupportTicket], int]:
    count_stmt = select(func.count(SupportTicket.id))
    stmt = _ticket_query()
    if status_value:
        count_stmt = count_stmt.where(SupportTicket.status == status_value)
        stmt = stmt.where(SupportTicket.status == status_value)
    total = (await session.execute(count_stmt)).scalar_one()
    stmt = (
        stmt.order_by(SupportTicket.created_at.desc(), SupportTicket.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = (await session.execute(stmt)).scalars().all()
    return list(items), total
