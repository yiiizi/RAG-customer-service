"""
Conversation and message API routes.
"""

from __future__ import annotations

import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ConversationCreateRequest,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdateRequest,
    MessageListResponse,
    MessageResponse,
)
from config.settings import settings
from middleware.auth import get_current_user
from mysql_module.conversations import (
    create_conversation,
    delete_conversation as delete_conversation_record,
    get_conversation_messages,
    get_user_conversations,
    update_conversation_title,
)
from mysql_module.dao import async_session
from mysql_module.models import SupportTicket

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _is_staff_or_admin(user: dict) -> bool:
    return user.get("role") in {"staff", "admin"}


def _serialize_message_sources(raw: str | None, user: dict) -> tuple[str | None, str | None]:
    """Return a role-safe sources JSON string and extracted status."""
    if not raw:
        return None, None
    try:
        payload = json.loads(raw)
    except Exception:
        return raw, None
    status_value = payload.get("status")
    if not _is_staff_or_admin(user) and isinstance(payload, dict):
        payload = {
            "public_sources": payload.get("public_sources", []),
            "status": status_value,
        }
    return json.dumps(payload, ensure_ascii=False), status_value


async def _get_accessible_conversation(session: AsyncSession, conversation_id: int, current_user: dict):
    from mysql_module.conversations import get_conversation as get_conv

    conversation = await get_conv(
        session=session,
        conversation_id=conversation_id,
        user_id=current_user["id"],
    )
    if conversation:
        return conversation

    if _is_staff_or_admin(current_user):
        ticket_stmt = select(SupportTicket.id).where(SupportTicket.conversation_id == conversation_id).limit(1)
        ticket_id = (await session.execute(ticket_stmt)).scalar_one_or_none()
        if ticket_id is not None:
            return await get_conv(session=session, conversation_id=conversation_id, user_id=None)

    return None

@router.post("", response_model=ConversationResponse)
async def create_new_conversation(
    req: ConversationCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new conversation.
    """
    async with async_session() as session:
        conversation = await create_conversation(
            session=session,
            user_id=current_user["id"],
            title=req.title
        )
        
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else "",
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else "",
        }


@router.get("", response_model=ConversationListResponse)
async def get_conversations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated conversations for current user.
    """
    async with async_session() as session:
        conversations, total = await get_user_conversations(
            session=session,
            user_id=current_user["id"],
            page=page,
            page_size=page_size
        )
        
        items = [
            {
                "id": conv.id,
                "user_id": conv.user_id,
                "title": conv.title,
                "created_at": conv.created_at.isoformat() if conv.created_at else "",
                "updated_at": conv.updated_at.isoformat() if conv.updated_at else "",
            }
            for conv in conversations
        ]
        
        return {
            "items": items,
            "total": total
        }


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a single conversation by ID.
    """
    async with async_session() as session:
        conversation = await _get_accessible_conversation(session, conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else "",
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else "",
        }


@router.put("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: int,
    req: ConversationUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update conversation title.
    """
    async with async_session() as session:
        conversation = await update_conversation_title(
            session=session,
            conversation_id=conversation_id,
            user_id=current_user["id"],
            new_title=req.title
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {
            "id": conversation.id,
            "user_id": conversation.user_id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else "",
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else "",
        }


@router.delete("/{conversation_id}")
async def delete_conversation_route(
    conversation_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a conversation.
    """
    async with async_session() as session:
        success = await delete_conversation_record(
            session=session,
            conversation_id=conversation_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"status": "success", "message": "Conversation deleted"}


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(
    conversation_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Get paginated messages for a conversation.
    """
    async with async_session() as session:
        conversation = await _get_accessible_conversation(session, conversation_id, current_user)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        messages, total = await get_conversation_messages(
            session=session,
            conversation_id=conversation_id,
            user_id=None if _is_staff_or_admin(current_user) else current_user["id"],
            page=page,
            page_size=page_size
        )
        
        items = []
        for msg in messages:
            sources, status_value = _serialize_message_sources(msg.sources, current_user)
            items.append({
                "id": msg.id,
                "conversation_id": msg.conversation_id,
                "role": msg.role,
                "content": msg.content,
                "sources": sources,
                "intent": msg.intent,
                "latency_ms": msg.latency_ms,
                "status": status_value,
                "created_at": msg.created_at.isoformat() if msg.created_at else "",
            })
        
        return {
            "items": items,
            "total": total
        }


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def create_message(
    conversation_id: int,
    req: dict,  # Simple dict for now
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new message in a conversation.
    """
    async with async_session() as session:
        from mysql_module.conversations import create_message as create_msg, get_conversation as get_conv
        
        # Verify conversation belongs to user
        conversation = await get_conv(
            session=session,
            conversation_id=conversation_id,
            user_id=current_user["id"]
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Create message
        message = await create_msg(
            session=session,
            conversation_id=conversation_id,
            role=req.get("role", "user"),
            content=req.get("content", ""),
            sources=req.get("sources"),
            intent=req.get("intent"),
            latency_ms=req.get("latency_ms")
        )
        
        sources, status_value = _serialize_message_sources(message.sources, current_user)
        return {
            "id": message.id,
            "conversation_id": message.conversation_id,
            "role": message.role,
            "content": message.content,
            "sources": sources,
            "intent": message.intent,
            "latency_ms": message.latency_ms,
            "status": status_value,
            "created_at": message.created_at.isoformat() if message.created_at else "",
        }


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a message.
    """
    async with async_session() as session:
        from mysql_module.conversations import delete_message as delete_msg
        
        success = await delete_msg(
            session=session,
            message_id=message_id,
            user_id=current_user["id"]
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        return {"status": "success", "message": "Message deleted"}
