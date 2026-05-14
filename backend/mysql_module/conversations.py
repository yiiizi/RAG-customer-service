"""
Conversation and message related database operations.
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from mysql_module.models import Conversation, Message


async def create_conversation(
    session: AsyncSession,
    user_id: int,
    title: str = "New Conversation"
) -> Conversation:
    """Create a new conversation."""
    conversation = Conversation(
        user_id=user_id,
        title=title
    )
    
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    
    return conversation


async def get_conversation(
    session: AsyncSession,
    conversation_id: int,
    user_id: Optional[int] = None
) -> Optional[Conversation]:
    """Get a conversation by ID, optionally filtered by user_id."""
    query = select(Conversation).where(Conversation.id == conversation_id)
    
    if user_id is not None:
        query = query.where(Conversation.user_id == user_id)
    
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def get_user_conversations(
    session: AsyncSession,
    user_id: int,
    page: int = 1,
    page_size: int = 20
) -> tuple[List[Conversation], int]:
    """Get paginated conversations for a user."""
    # Get total count
    count_query = select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
    total = await session.execute(count_query)
    total = total.scalar_one()
    
    # Get paginated conversations
    offset = (page - 1) * page_size
    query = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    
    result = await session.execute(query)
    conversations = result.scalars().all()
    
    return conversations, total


async def update_conversation_title(
    session: AsyncSession,
    conversation_id: int,
    user_id: int,
    new_title: str
) -> Optional[Conversation]:
    """Update conversation title."""
    conversation = await get_conversation(session, conversation_id, user_id)
    
    if not conversation:
        return None
    
    conversation.title = new_title
    await session.commit()
    await session.refresh(conversation)
    
    return conversation


async def delete_conversation(
    session: AsyncSession,
    conversation_id: int,
    user_id: int
) -> bool:
    """Delete a conversation."""
    conversation = await get_conversation(session, conversation_id, user_id)
    
    if not conversation:
        return False
    
    await session.delete(conversation)
    await session.commit()
    
    return True


async def create_message(
    session: AsyncSession,
    conversation_id: int,
    role: str,
    content: str,
    sources: Optional[str] = None,
    intent: Optional[str] = None,
    latency_ms: Optional[int] = None
) -> Message:
    """Create a new message."""
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        sources=sources,
        intent=intent,
        latency_ms=latency_ms
    )
    
    session.add(message)
    
    # Update conversation's updated_at
    conversation = await get_conversation(session, conversation_id)
    if conversation:
        from datetime import datetime
        conversation.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(message)
    
    return message


async def ensure_conversation(
    session: AsyncSession,
    user_id: int,
    conversation_id: Optional[int] = None,
    title: str = "New Conversation",
) -> Conversation:
    """Return an owned conversation or create one if no ID is provided."""
    if conversation_id is not None:
        conversation = await get_conversation(session, conversation_id, user_id)
        if not conversation:
            raise ValueError("Conversation not found")
        return conversation
    return await create_conversation(session, user_id=user_id, title=title)


async def maybe_set_initial_title(
    session: AsyncSession,
    conversation: Conversation,
    first_message: str,
    max_len: int = 30,
) -> Conversation:
    """Set a conversation title from the first user message when still default."""
    if conversation.title not in {"New Conversation", "新对话"}:
        return conversation
    title = first_message.strip().replace("\n", " ")
    if len(title) > max_len:
        title = title[:max_len].rstrip() + "..."
    if not title:
        return conversation
    conversation.title = title
    await session.commit()
    await session.refresh(conversation)
    return conversation


async def get_conversation_messages(
    session: AsyncSession,
    conversation_id: int,
    user_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 50
) -> tuple[List[Message], int]:
    """Get paginated messages for a conversation."""
    # Verify conversation belongs to user (if user_id provided)
    if user_id is not None:
        conversation = await get_conversation(session, conversation_id, user_id)
        if not conversation:
            return [], 0
    
    # Get total count
    count_query = select(func.count(Message.id)).where(Message.conversation_id == conversation_id)
    total = await session.execute(count_query)
    total = total.scalar_one()
    
    # Get paginated messages
    offset = (page - 1) * page_size
    query = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .offset(offset)
        .limit(page_size)
    )
    
    result = await session.execute(query)
    messages = result.scalars().all()
    
    return messages, total


async def delete_message(
    session: AsyncSession,
    message_id: int,
    user_id: int
) -> bool:
    """Delete a message."""
    # Get message and verify it belongs to user's conversation
    query = (
        select(Message)
        .join(Conversation)
        .where(Message.id == message_id)
        .where(Conversation.user_id == user_id)
    )
    
    result = await session.execute(query)
    message = result.scalar_one_or_none()
    
    if not message:
        return False
    
    await session.delete(message)
    await session.commit()
    
    return True
