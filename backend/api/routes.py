"""
FastAPI routes for the RAG system.

Endpoints
---------
- POST /api/chat              Q&A (non-streaming)
- WS   /ws/chat               Q&A (streaming via WebSocket)
- POST /api/kb/upload         Upload & index a file
- POST /api/kb/upload-dir     Index all files in a directory
- GET  /api/kb/list           List indexed documents
- GET  /api/kb/stats          Milvus collection stats
- DELETE /api/kb/{file_name}  Remove a file's chunks
- POST /api/kb/reindex        Re-index a file
- GET  /api/faq               List FAQ entries
- POST /api/faq               Create FAQ entry
- PUT  /api/faq/{faq_id}      Update FAQ entry
- DELETE /api/faq/{faq_id}    Delete FAQ entry
- POST /api/faq/batch-import  Bulk import FAQ
- GET  /api/dashboard         Dashboard analytics
- GET  /api/settings          Get current settings
- PUT  /api/settings          Update settings
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import (
    ChatRequest,
    ChatResponse,
    DashboardStats,
    FAQBatchImportRequest,
    FAQBatchImportResponse,
    FAQCreateRequest,
    FAQItem,
    FAQListResponse,
    FAQUpdateRequest,
    FeedbackRequest,
    FeedbackResponse,
    KBDeleteRequest,
    KBDeleteResponse,
    KBUploadResponse,
    SettingsResponse,
    SettingsUpdateRequest,
    UnresolvedQuestionListResponse,
    UnresolvedQuestionResponse,
    UnresolvedQuestionUpdateRequest,
    UnresolvedToFAQRequest,
)
from config.settings import settings
from middleware.auth import get_current_admin_user, get_current_staff_user, get_current_user
from business.ticket_service import build_ticket_no, build_ticket_notice, evaluate_handoff
from mysql_module.dao import (
    async_session,
    faq_delete,
    faq_get_hot,
    faq_search,
    faq_total_count,
    faq_upsert,
    get_session,
    qalog_stats,
)
from mysql_module import redis_cache
from mysql_module.conversations import (
    create_message,
    ensure_conversation,
    get_conversation_messages,
    maybe_set_initial_title,
)
from mysql_module.feedback import (
    feedback_counts_since,
    get_owned_assistant_message,
    get_previous_user_message,
    upsert_message_feedback,
)
from mysql_module.faq_semantic import extension_payload, upsert_faq_extension
from mysql_module.models import SupportTicket, UnresolvedQuestion
from mysql_module.tickets import create_ticket
from mysql_module.unresolved import (
    get_unresolved_question,
    list_unresolved_questions,
    record_unresolved_question,
    update_unresolved_status,
)
from offline_kb.indexer import delete_index, get_stats, index_directory, index_file, reindex_file
from rag_qa.pipeline import ask, ask_stream

router = APIRouter()

# ── Static file serving for uploads ─────────────────────────────────
KB_UPLOAD_DIR = settings.KB_UPLOAD_DIR
KB_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _faq_item_response(item) -> FAQItem:
    try:
        extra = extension_payload(item)
    except Exception:
        extra = {"status": "active", "priority": 0, "similar_questions": []}
    return FAQItem(
        id=item.id,
        question=item.question,
        answer=item.answer,
        frequency=item.frequency,
        category=item.category,
        status=extra["status"],
        priority=extra["priority"],
        similar_questions=extra["similar_questions"],
        created_at=item.created_at.isoformat() if item.created_at else None,
        updated_at=item.updated_at.isoformat() if item.updated_at else None,
    )


def _parse_source_list(raw: str | None) -> list[dict]:
    if not raw:
        return []
    try:
        value = json.loads(raw)
        if isinstance(value, dict):
            value = value.get("public_sources") or value.get("sources") or value.get("debug_sources") or []
        if not isinstance(value, list):
            return []
        return [
            {
                "text": str(item.get("text", "")),
                "source": str(item.get("source", "")),
                "score": float(item.get("score", 0.0) or 0.0),
                "chunk_index": int(item.get("chunk_index", -1) or -1),
            }
            for item in value
            if isinstance(item, dict)
        ]
    except Exception:
        return []


def _unresolved_item_response(item) -> UnresolvedQuestionResponse:
    return UnresolvedQuestionResponse(
        id=item.id,
        normalized_question=item.normalized_question,
        question=item.question,
        user_id=item.user_id,
        conversation_id=item.conversation_id,
        message_id=item.message_id,
        ai_answer=item.ai_answer,
        reason=item.reason,
        intent=item.intent,
        confidence=item.confidence,
        sources=_parse_source_list(item.sources),
        status=item.status,
        frequency=item.frequency,
        last_seen_at=item.last_seen_at.isoformat() if item.last_seen_at else "",
        created_at=item.created_at.isoformat() if item.created_at else "",
        updated_at=item.updated_at.isoformat() if item.updated_at else "",
    )


def _feedback_response(item) -> FeedbackResponse:
    return FeedbackResponse(
        id=item.id,
        message_id=item.message_id,
        rating=item.rating,
        reason=item.reason,
        comment=item.comment,
        created_at=item.created_at.isoformat() if item.created_at else None,
    )


def _sanitize_upload_name(file_name: str) -> str:
    """Return a safe flat file name for the upload directory."""
    name = Path(file_name).name.strip()
    name = re.sub(r"[\x00-\x1f<>:\"/\\|?*]", "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name:
        raise HTTPException(status_code=400, detail="文件名无效")
    return name


def _escape_milvus_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _is_staff_or_admin(user: dict) -> bool:
    return user.get("role") in {"staff", "admin"}


def _public_source_label(source: dict) -> str:
    src = str(source.get("source", "")).strip()
    if src.startswith(("http://", "https://")):
        return "来自联网搜索"
    return "来自知识库"


def _response_sources(sources: list[dict], user: dict) -> list[dict]:
    if _is_staff_or_admin(user):
        return [
            {"text": s["text"], "source": s.get("source", ""), "score": s.get("score", 0.0), "chunk_index": s.get("chunk_index", -1)}
            for s in sources
        ]
    labels: dict[str, dict] = {}
    for source in sources:
        label = _public_source_label(source)
        labels[label] = {"text": "", "source": label, "score": 0.0, "chunk_index": -1}
    return list(labels.values())


def _sources_payload(
    sources: list[dict],
    user: dict,
    status_value: str = "completed",
    extra: dict | None = None,
) -> str:
    public_sources = _response_sources(sources, {"role": "user"})
    debug_sources = _response_sources(sources, {"role": "admin"})
    payload = {
        "public_sources": public_sources,
        "debug_sources": debug_sources,
        "status": status_value,
    }
    if extra:
        payload.update(extra)
    return json.dumps(payload, ensure_ascii=False)


def _json_source_list(items: list[dict]) -> str:
    return json.dumps(items, ensure_ascii=False)


def _build_ticket_plan(query: str, intent: str | None = None, answer: str | None = None) -> dict | None:
    plan = evaluate_handoff(query=query, intent=intent, answer=answer)
    if not plan:
        return None
    return {"ticket_no": build_ticket_no(), **plan}


async def _create_support_ticket(
    user: dict,
    conversation_id: int,
    message_id: int,
    query: str,
    answer: str,
    sources: list[dict],
    ticket_plan: dict,
) -> dict | None:
    try:
        async with async_session() as session:
            ticket = await create_ticket(
                session,
                ticket_no=ticket_plan["ticket_no"],
                user_id=user["id"],
                conversation_id=conversation_id,
                message_id=message_id,
                category=ticket_plan["category"],
                priority=ticket_plan["priority"],
                summary=ticket_plan["summary"],
                user_question=query,
                ai_answer=answer,
                public_sources=_json_source_list(_response_sources(sources, {"role": "user"})),
                debug_sources=_json_source_list(_response_sources(sources, {"role": "admin"})),
            )
            await session.commit()
            return {"id": ticket.id, "ticket_no": ticket.ticket_no}
    except Exception:
        logger.exception("Failed to create support ticket")
        return None


def _is_low_confidence_result(result) -> bool:
    if result.intent in {"blocked", "chat", "faq", "order_query", "logistics_track"}:
        return False
    if result.metadata.get("kb_only") and not result.sources:
        return True
    if result.intent in {"knowledge_qa", "faq"} and not result.sources and not result.metadata.get("cache"):
        return True
    scores = [float(item.get("score") or 0) for item in result.sources or []]
    return bool(scores) and max(scores) < 0.35


def _low_confidence_answer() -> str:
    return "当前知识库中没有找到足够明确的信息。您可以补充商品型号、订单号或具体问题，我会继续帮您查询。"


async def _recent_low_confidence_count(conversation_id: int, user_id: int) -> int:
    async with async_session() as session:
        messages, _ = await get_conversation_messages(
            session,
            conversation_id=conversation_id,
            user_id=user_id,
            page=1,
            page_size=6,
        )
        count = 0
        for msg in reversed(messages):
            if msg.role != "assistant":
                continue
            try:
                payload = json.loads(msg.sources or "{}")
            except Exception:
                payload = {}
            if payload.get("low_confidence"):
                count += 1
            else:
                break
        return count


async def _record_unresolved(
    *,
    user: dict,
    conversation_id: int,
    message_id: int | None,
    query: str,
    answer: str,
    intent: str,
    sources: list[dict],
    reason: str = "low_confidence",
    confidence: float = 0.0,
) -> None:
    try:
        async with async_session() as session:
            await record_unresolved_question(
                session,
                question=query,
                user_id=user["id"],
                conversation_id=conversation_id,
                message_id=message_id,
                ai_answer=answer,
                reason=reason,
                intent=intent,
                confidence=confidence,
                sources=sources,
            )
            await session.commit()
    except Exception:
        logger.exception("Failed to record unresolved question")


async def _prepare_chat_conversation(
    user: dict,
    conversation_id: int | None,
    query: str,
) -> tuple[int, list[dict]]:
    """Verify/create conversation, persist user message, and return history."""
    async with async_session() as session:
        conversation = await ensure_conversation(
            session,
            user_id=user["id"],
            conversation_id=conversation_id,
            title="新对话",
        )
        await create_message(
            session,
            conversation_id=conversation.id,
            role="user",
            content=query,
            sources=json.dumps({"status": "completed"}, ensure_ascii=False),
        )
        await maybe_set_initial_title(session, conversation, query)
        messages, _total = await get_conversation_messages(
            session,
            conversation_id=conversation.id,
            user_id=user["id"],
            page=1,
            page_size=12,
        )
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages[:-1]
            if msg.content.strip()
        ][-10:]
        return conversation.id, history


async def _save_assistant_message(
    conversation_id: int,
    content: str,
    sources: list[dict],
    user: dict,
    intent: str | None = None,
    latency_ms: int | None = None,
    status_value: str = "completed",
    source_extra: dict | None = None,
) -> int:
    async with async_session() as session:
        message = await create_message(
            session,
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            sources=_sources_payload(sources, user, status_value=status_value, extra=source_extra),
            intent=intent,
            latency_ms=latency_ms,
        )
        return message.id


async def _get_ws_current_user(ws: WebSocket) -> dict | None:
    token = ws.query_params.get("token")
    if not token:
        return None
    try:
        from utils.security import decode_token
        from mysql_module.auth import get_user_by_id

        payload = decode_token(token)
        user_id = payload.get("sub") if payload else None
        if not user_id:
            return None
        async with async_session() as session:
            user = await get_user_by_id(session, int(user_id))
            if not user or not user.is_active:
                return None
            return {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "is_active": user.is_active,
            }
    except Exception:
        logger.exception("WebSocket authentication failed")
        return None


# ═════════════════════════════════════════════════════════════════════
#  CHAT
# ═════════════════════════════════════════════════════════════════════

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, current_user: dict = Depends(get_current_user)):
    """Non-streaming Q&A."""
    try:
        try:
            conversation_id, history = await _prepare_chat_conversation(current_user, req.conversation_id, req.query)
        except ValueError:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")
        result = await ask(
            req.query,
            kb_only=req.kb_only,
            web_search=req.web_search,
            history=history,
            model_config_id=None,
            user_id=current_user["id"],
        )
        low_confidence = _is_low_confidence_result(result)
        if low_confidence:
            result.answer = _low_confidence_answer()
            result.sources = []
            result.metadata["low_confidence"] = True
        ticket_plan = _build_ticket_plan(req.query, intent=result.intent, answer=result.answer)
        if low_confidence and await _recent_low_confidence_count(conversation_id, current_user["id"]) >= 1:
            ticket_plan = ticket_plan or {
                "ticket_no": build_ticket_no(),
                "category": "low_confidence",
                "priority": "medium",
                "reason": "repeated_low_confidence",
                "summary": req.query[:80],
            }
        final_answer = result.answer
        if ticket_plan:
            final_answer += build_ticket_notice(ticket_plan["ticket_no"])
        assistant_message_id = await _save_assistant_message(
            conversation_id=conversation_id,
            content=final_answer,
            sources=result.sources,
            user=current_user,
            intent=result.intent,
            latency_ms=result.latency_ms,
            source_extra={"low_confidence": low_confidence, "confidence": 0.0 if low_confidence else 1.0},
        )
        if low_confidence:
            await _record_unresolved(
                user=current_user,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                query=req.query,
                answer=final_answer,
                intent=result.intent,
                sources=result.sources,
                confidence=0.0,
            )
        created_ticket = None
        if ticket_plan:
            created_ticket = await _create_support_ticket(
                current_user,
                conversation_id=conversation_id,
                message_id=assistant_message_id,
                query=req.query,
                answer=final_answer,
                sources=result.sources,
                ticket_plan=ticket_plan,
            )
        return ChatResponse(
            answer=final_answer,
            intent=result.intent,
            sources=_response_sources(result.sources, current_user),
            latency_ms=result.latency_ms,
            conversation_id=conversation_id,
            message_id=assistant_message_id,
            need_handoff=bool(created_ticket),
            ticket_no=created_ticket["ticket_no"] if created_ticket else None,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    """Streaming Q&A via WebSocket (token-by-token typing effect)."""
    await ws.accept()
    current_user = await _get_ws_current_user(ws)
    if not current_user:
        await ws.send_json({"type": "error", "data": "未登录或登录已过期"})
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            query = data.get("query", "").strip()
            conversation_id = data.get("conversation_id", None)
            kb_only = data.get("kb_only", False)
            web_search = data.get("web_search", False)
            logger.info(f"WS: user={current_user['id']} query='{query}' conversation_id={conversation_id} kb_only={kb_only} web_search={web_search}")
            if not query:
                await ws.send_json({"type": "error", "data": "查询内容为空"})
                continue

            try:
                conversation_id, history = await _prepare_chat_conversation(
                    current_user,
                    int(conversation_id) if conversation_id else None,
                    query,
                )
            except ValueError:
                await ws.send_json({"type": "error", "data": "会话不存在或无权访问"})
                continue

            try:
                import time
                start = time.perf_counter()
                assistant_text = ""
                raw_sources: list[dict] = []
                done_payload: dict = {}
                async for chunk in ask_stream(
                    query,
                    kb_only=kb_only,
                    web_search=web_search,
                    history=history,
                    model_config_id=None,
                    user_id=current_user["id"],
                ):
                    if chunk.get("type") == "sources":
                        raw_sources = chunk.get("data") or []
                    if chunk.get("type") == "sources" and not _is_staff_or_admin(current_user):
                        chunk = {"type": "sources", "data": _response_sources(chunk.get("data") or [], current_user)}
                    elif chunk.get("type") == "token":
                        assistant_text += str(chunk.get("data") or "")
                    elif chunk.get("type") == "done":
                        done_payload = dict(chunk.get("data") or {})
                        done_payload["latency_ms"] = int((time.perf_counter() - start) * 1000)
                        continue
                    await ws.send_json(chunk)
                ticket_plan = _build_ticket_plan(
                    query,
                    intent=str(done_payload.get("intent") or ""),
                    answer=assistant_text,
                )
                stream_low_confidence = (
                    str(done_payload.get("intent") or "") in {"knowledge_qa", "faq"}
                    and not raw_sources
                    and not done_payload.get("cache")
                )
                if stream_low_confidence:
                    low_notice = "\n\n" + _low_confidence_answer()
                    assistant_text += low_notice
                    await ws.send_json({"type": "token", "data": low_notice})
                    done_payload["low_confidence"] = True
                    await _record_unresolved(
                        user=current_user,
                        conversation_id=conversation_id,
                        message_id=None,
                        query=query,
                        answer=assistant_text,
                        intent=str(done_payload.get("intent") or ""),
                        sources=raw_sources,
                        confidence=0.0,
                    )
                    if await _recent_low_confidence_count(conversation_id, current_user["id"]) >= 1:
                        ticket_plan = ticket_plan or {
                            "ticket_no": build_ticket_no(),
                            "category": "low_confidence",
                            "priority": "medium",
                            "reason": "repeated_low_confidence",
                            "summary": query[:80],
                        }
                created_ticket = None
                if ticket_plan:
                    notice = build_ticket_notice(ticket_plan["ticket_no"])
                    assistant_text += notice
                    await ws.send_json({"type": "token", "data": notice})
                    done_payload["ticket_no"] = ticket_plan["ticket_no"]
                    done_payload["need_handoff"] = True
                assistant_message_id = await _save_assistant_message(
                    conversation_id=conversation_id,
                    content=assistant_text,
                    sources=raw_sources,
                    user=current_user,
                    intent=str(done_payload.get("intent") or ""),
                    latency_ms=done_payload.get("latency_ms"),
                    status_value="completed",
                    source_extra={
                        "low_confidence": bool(done_payload.get("low_confidence")),
                        "confidence": 0.0 if done_payload.get("low_confidence") else 1.0,
                    },
                )
                if ticket_plan:
                    created_ticket = await _create_support_ticket(
                        current_user,
                        conversation_id=conversation_id,
                        message_id=assistant_message_id,
                        query=query,
                        answer=assistant_text,
                        sources=raw_sources,
                        ticket_plan=ticket_plan,
                    )
                    if created_ticket:
                        done_payload["ticket_no"] = created_ticket["ticket_no"]
                await ws.send_json({"type": "done", "data": done_payload})
                await ws.send_json({"type": "message_saved", "data": {"conversation_id": conversation_id, "message_id": assistant_message_id}})
                await ws.send_json({"type": "finish", "data": {}})
            except Exception as e:
                logger.exception("Stream error")
                if 'conversation_id' in locals():
                    await _save_assistant_message(
                        conversation_id=conversation_id,
                        content="抱歉，系统暂时出现问题，请稍后再试或联系人工客服。",
                        sources=[],
                        user=current_user,
                        intent="error",
                        latency_ms=None,
                        status_value="error",
                    )
                await ws.send_json({"type": "error", "data": str(e)})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")


# ═════════════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE
# ═════════════════════════════════════════════════════════════════════

@router.post("/kb/upload", response_model=KBUploadResponse)
async def kb_upload(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_admin_user),
):
    """Upload a single file and index it into the knowledge base."""
    # Fix encoding for Chinese filenames on Windows
    raw_name = file.filename or "unknown"
    try:
        safe_name = raw_name.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        safe_name = raw_name
    safe_name = _sanitize_upload_name(safe_name)
    ext = Path(safe_name).suffix.lower()
    if ext not in settings.KB_SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型：{ext}")

    # Save to upload dir
    file_path = KB_UPLOAD_DIR / safe_name
    try:
        content = await file.read()
        max_bytes = settings.KB_MAX_FILE_SIZE_MB * 1024 * 1024
        if len(content) > max_bytes:
            raise HTTPException(status_code=413, detail=f"文件大小不能超过 {settings.KB_MAX_FILE_SIZE_MB}MB")
        file_path.write_bytes(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存文件失败：{e}")

    try:
        result = await index_file(file_path)
        return KBUploadResponse(
            status=result.get("status", "ok"),
            file=safe_name,
            parent_chunks=result.get("parent_chunks", 0),
            child_chunks=result.get("child_chunks", 0),
            inserted=result.get("inserted", 0),
        )
    except Exception as e:
        logger.exception(f"Indexing failed for {safe_name}")
        return KBUploadResponse(status="error", file=safe_name, error=str(e))


@router.post("/kb/upload-dir")
async def kb_upload_dir(
    directory: str = Query(..., description="Directory path to index"),
    current_user: dict = Depends(get_current_admin_user),
):
    """Index all supported files from a directory."""
    try:
        result = await index_directory(directory)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/stats")
async def kb_stats(current_user: dict = Depends(get_current_admin_user)):
    """Get Milvus collection statistics."""
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/list")
async def kb_list(current_user: dict = Depends(get_current_admin_user)):
    """List all indexed documents with status."""
    try:
        from rag_qa.milvus_store import get_collection
        col = get_collection()
        # Query distinct files
        results = col.query(
            expr="id != \"\"",
            output_fields=["file_name", "file_type", "chunk_index", "created_at"],
            limit=16384,
        )
        # Aggregate by file_name
        files: dict[str, dict] = {}
        for r in results:
            name = r.get("file_name", "unknown")
            if name not in files:
                ts = r.get("created_at", None)
                created_str = None
                if ts:
                    from datetime import datetime, timezone, timedelta
                    beijing_tz = timezone(timedelta(hours=8))
                    created_str = datetime.fromtimestamp(int(ts), tz=beijing_tz).strftime('%Y-%m-%dT%H:%M:%S+08:00')
                files[name] = {
                    "file_name": name,
                    "file_type": r.get("file_type", ""),
                    "status": "indexed",
                    "chunk_count": 0,
                    "created_at": created_str,
                }
            files[name]["chunk_count"] += 1

        return {"items": list(files.values()), "total": len(files)}
    except Exception as e:
        logger.exception("KB list error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/chunks/{file_name}")
async def kb_chunks(file_name: str, current_user: dict = Depends(get_current_admin_user)):
    """Get all chunks for a specific file with parent-child relationships."""
    try:
        from rag_qa.milvus_store import get_collection
        col = get_collection()
        # Query all chunks for this file
        escaped_file_name = _escape_milvus_string(file_name)
        results = col.query(
            expr=f'file_name == "{escaped_file_name}"',
            output_fields=["id", "text", "parent_id", "parent_text", "chunk_index", "created_at"],
            limit=16384,
        )
        # Group by parent_id
        parents: dict[str, dict] = {}
        children: list[dict] = []
        for r in results:
            pid = r.get("parent_id", "")
            child_info = {
                "id": r.get("id", ""),
                "text": r.get("text", ""),
                "chunk_index": r.get("chunk_index", -1),
                "created_at": r.get("created_at", None),
            }
            if pid not in parents:
                parents[pid] = {
                    "parent_id": pid,
                    "parent_text": r.get("parent_text", ""),
                    "children": [],
                }
            parents[pid]["children"].append(child_info)
            children.append(child_info)
        parent_list = sorted(parents.values(), key=lambda p: p["children"][0]["chunk_index"] if p["children"] else 0)
        return {
            "file_name": file_name,
            "chunk_count": len(children),
            "parent_count": len(parent_list),
            "parents": parent_list,
        }
    except Exception as e:
        logger.exception("Chunk query error")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/kb/{file_name}", response_model=KBDeleteResponse)
async def kb_delete(file_name: str, current_user: dict = Depends(get_current_admin_user)):
    """Remove all chunks belonging to a file from the knowledge base."""
    try:
        result = await delete_index(file_name)
        return KBDeleteResponse(
            status="ok", file_name=file_name, chunks_removed=result.get("chunks_removed", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kb/reindex")
async def kb_reindex(
    file_name: str = Query(..., description="File name to re-index"),
    current_user: dict = Depends(get_current_admin_user),
):
    """Re-index a previously uploaded file."""
    safe_name = _sanitize_upload_name(file_name)
    file_path = KB_UPLOAD_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"文件未找到：{file_name}")
    try:
        result = await reindex_file(file_path)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═════════════════════════════════════════════════════════════════════
#  FAQ
# ═════════════════════════════════════════════════════════════════════

@router.get("/faq", response_model=FAQListResponse)
async def faq_list(
    keyword: str = Query(""),
    category: str = Query(""),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Search and list FAQ entries."""
    try:
        items = await faq_search(session, keyword=keyword, category=category, offset=offset, limit=limit)
        total = await faq_total_count(session)
        return FAQListResponse(items=[_faq_item_response(item) for item in items], total=total)
    except Exception as e:
        logger.exception("FAQ list error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faq", response_model=FAQItem)
async def faq_create(
    req: FAQCreateRequest,
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Create a new FAQ entry."""
    faq = await faq_upsert(session, req.question, req.answer, req.category)
    requested_status = req.status
    if current_user.get("role") != "admin":
        requested_status = "draft"
    await upsert_faq_extension(
        session,
        faq,
        status=requested_status or "active",
        priority=req.priority,
        similar_questions=req.similar_questions,
    )
    await session.commit()
    await session.refresh(faq)
    return _faq_item_response(faq)


@router.put("/faq/{faq_id}", response_model=FAQItem)
async def faq_update(
    faq_id: str,
    req: FAQUpdateRequest,
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Update an existing FAQ entry."""
    from mysql_module.models import FAQPair
    from sqlalchemy import select

    stmt = select(FAQPair).where(FAQPair.id == faq_id)
    result = await session.execute(stmt)
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ 未找到")

    if req.question is not None:
        faq.question = req.question
    if req.answer is not None:
        faq.answer = req.answer
    if req.category is not None:
        faq.category = req.category

    session.add(faq)
    await session.flush()
    status_value = req.status
    if current_user.get("role") != "admin":
        status_value = None
    await upsert_faq_extension(
        session,
        faq,
        status=status_value,
        priority=req.priority,
        similar_questions=req.similar_questions,
        rebuild_embedding=bool(req.question is not None or req.similar_questions is not None),
    )
    await session.commit()
    await session.refresh(faq)

    return _faq_item_response(faq)


@router.delete("/faq/{faq_id}")
async def faq_delete_route(
    faq_id: str,
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Delete a FAQ entry."""
    deleted = await faq_delete(session, faq_id)
    await session.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="FAQ 未找到")
    return {"status": "deleted", "id": faq_id}


@router.post("/faq/batch-import", response_model=FAQBatchImportResponse)
async def faq_batch_import(
    req: FAQBatchImportRequest,
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Bulk import FAQ entries."""
    imported = 0
    skipped = 0
    errors: list[str] = []

    for item in req.items:
        try:
            faq = await faq_upsert(session, item.question, item.answer, item.category)
            status_value = item.status
            if current_user.get("role") != "admin":
                status_value = "draft"
            await upsert_faq_extension(
                session,
                faq,
                status=status_value or "active",
                priority=item.priority,
                similar_questions=item.similar_questions,
            )
            imported += 1
        except Exception as e:
            errors.append(f"{item.question[:30]}...: {e}")
            skipped += 1

    await session.commit()
    return FAQBatchImportResponse(imported=imported, skipped=skipped, errors=errors)


# ═════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═════════════════════════════════════════════════════════════════════

@router.get("/unresolved", response_model=UnresolvedQuestionListResponse)
async def unresolved_list(
    status_value: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """List unresolved questions for FAQ and knowledge-base improvement."""
    items, total = await list_unresolved_questions(
        session,
        status_value=status_value,
        page=page,
        page_size=page_size,
    )
    return UnresolvedQuestionListResponse(
        items=[_unresolved_item_response(item) for item in items],
        total=total,
    )


@router.put("/unresolved/{unresolved_id}", response_model=UnresolvedQuestionResponse)
async def unresolved_update(
    unresolved_id: int,
    req: UnresolvedQuestionUpdateRequest,
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Update unresolved question status."""
    try:
        item = await update_unresolved_status(session, unresolved_id, req.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid unresolved question status")
    if not item:
        raise HTTPException(status_code=404, detail="Unresolved question not found")
    await session.commit()
    await session.refresh(item)
    return _unresolved_item_response(item)


@router.post("/unresolved/{unresolved_id}/to-faq", response_model=FAQItem)
async def unresolved_to_faq(
    unresolved_id: int,
    req: UnresolvedToFAQRequest,
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Create an active FAQ from an unresolved question and warm Redis cache."""
    item = await get_unresolved_question(session, unresolved_id)
    if not item:
        raise HTTPException(status_code=404, detail="Unresolved question not found")

    question = (req.question or item.question).strip()
    answer = (req.answer or item.ai_answer or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="FAQ question cannot be empty")
    if not answer:
        answer = "请补充标准答案后再发布。"

    if not (req.answer or item.ai_answer or "").strip():
        answer = "该问题已收录，标准答案待运营人员补充完善。"

    try:
        faq = await faq_upsert(session, question, answer, req.category)
        await upsert_faq_extension(
            session,
            faq,
            status="active",
            priority=0,
            similar_questions=req.similar_questions,
        )
        item.status = "converted_to_faq"
        await session.commit()
        await session.refresh(faq)
        await redis_cache.faq_cache_set(question, answer, faq.frequency)
        for similar_question in req.similar_questions:
            similar_question = similar_question.strip()
            if similar_question:
                await redis_cache.faq_cache_set(similar_question, answer, faq.frequency)
        return _faq_item_response(faq)
    except Exception as e:
        await session.rollback()
        logger.exception("Failed to convert unresolved question to FAQ")
        raise HTTPException(status_code=500, detail=f"FAQ 生成失败：{e}")
        raise HTTPException(status_code=500, detail=f"FAQ 生成失败：{e}")


@router.post("/messages/{message_id}/feedback", response_model=FeedbackResponse)
async def message_feedback(
    message_id: int,
    req: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Create or update feedback for an owned assistant message."""
    rating = req.rating.strip().lower()
    if rating not in {"helpful", "unhelpful"}:
        raise HTTPException(status_code=400, detail="rating must be helpful or unhelpful")

    message = await get_owned_assistant_message(
        session,
        message_id=message_id,
        user_id=current_user["id"],
    )
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    item = await upsert_message_feedback(
        session,
        user_id=current_user["id"],
        conversation_id=message.conversation_id,
        message_id=message.id,
        rating=rating,
        reason=req.reason,
        comment=req.comment,
    )

    if rating == "unhelpful":
        previous_user_message = await get_previous_user_message(
            session,
            conversation_id=message.conversation_id,
            before_message_id=message.id,
        )
        question = previous_user_message.content if previous_user_message else req.comment or message.content[:200]
        await record_unresolved_question(
            session,
            question=question,
            user_id=current_user["id"],
            conversation_id=message.conversation_id,
            message_id=message.id,
            ai_answer=message.content,
            reason=req.reason or "negative_feedback",
            intent=message.intent,
            confidence=0.0,
            sources=_parse_source_list(message.sources),
        )

    await session.commit()
    await session.refresh(item)
    return _feedback_response(item)


def _dashboard_since(range_value: str) -> tuple[str, datetime]:
    now = datetime.utcnow()
    value = range_value if range_value in {"today", "7d", "30d"} else "7d"
    if value == "today":
        return value, now.replace(hour=0, minute=0, second=0, microsecond=0)
    if value == "30d":
        return value, now - timedelta(days=30)
    return value, now - timedelta(days=7)


def _safe_rate(part: int, total: int) -> float:
    return round(part / total, 3) if total else 0.0


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(
    range_value: str = Query("7d", alias="range"),
    current_user: dict = Depends(get_current_staff_user),
    session: AsyncSession = Depends(get_session),
):
    """Aggregated analytics for the dashboard page."""
    try:
        selected_range, since = _dashboard_since(range_value)
        stats = await qalog_stats(session, since=since)
        top_faqs = await faq_get_hot(session, top_n=10)
        feedback_counts = await feedback_counts_since(session, since)
        helpful_count = feedback_counts.get("helpful", 0)
        unhelpful_count = feedback_counts.get("unhelpful", 0)
        feedback_total = helpful_count + unhelpful_count

        unresolved_count = (
            await session.execute(
                select(func.count(UnresolvedQuestion.id)).where(UnresolvedQuestion.created_at >= since)
            )
        ).scalar() or 0
        faq_conversion_count = (
            await session.execute(
                select(func.count(UnresolvedQuestion.id)).where(
                    UnresolvedQuestion.status == "converted_to_faq",
                    UnresolvedQuestion.updated_at >= since,
                )
            )
        ).scalar() or 0
        ticket_total = (
            await session.execute(
                select(func.count(SupportTicket.id)).where(SupportTicket.created_at >= since)
            )
        ).scalar() or 0
        ticket_resolved = (
            await session.execute(
                select(func.count(SupportTicket.id)).where(
                    SupportTicket.created_at >= since,
                    SupportTicket.status.in_(["resolved", "closed"]),
                )
            )
        ).scalar() or 0
        top_unresolved_rows = (
            await session.execute(
                select(UnresolvedQuestion)
                .where(UnresolvedQuestion.created_at >= since)
                .order_by(UnresolvedQuestion.frequency.desc(), UnresolvedQuestion.last_seen_at.desc())
                .limit(5)
            )
        ).scalars().all()
        milvus_stats = {}
        try:
            milvus_stats = get_stats()
        except Exception:
            pass

        return DashboardStats(
            total_queries=stats["total_queries"],
            avg_latency_ms=stats["avg_latency_ms"],
            hit_rate=stats["hit_rate"],
            intent_distribution=stats["intent_distribution"],
            daily_trend=stats["daily_trend"],
            top_faqs=[_faq_item_response(f) for f in top_faqs],
            milvus_stats=milvus_stats,
            range=selected_range,
            helpful_rate=_safe_rate(helpful_count, feedback_total),
            unhelpful_rate=_safe_rate(unhelpful_count, feedback_total),
            unresolved_count=unresolved_count,
            handoff_rate=_safe_rate(ticket_total, stats["total_queries"]),
            ticket_resolution_rate=_safe_rate(ticket_resolved, ticket_total),
            faq_conversion_count=faq_conversion_count,
            top_unresolved=[
                {
                    "id": item.id,
                    "question": item.question,
                    "frequency": item.frequency,
                    "status": item.status,
                }
                for item in top_unresolved_rows
            ],
        )
    except Exception as e:
        logger.exception("Dashboard error")
        raise HTTPException(status_code=500, detail=str(e))


# ═════════════════════════════════════════════════════════════════════
#  SETTINGS
# ═════════════════════════════════════════════════════════════════════

@router.get("/settings", response_model=SettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_admin_user)):
    """Return current effective settings (non-sensitive)."""
    return SettingsResponse(
        llm={
            "api_base": "***",
            "model": settings.LLM_MODEL,
            "temperature": settings.LLM_TEMPERATURE,
            "max_tokens": settings.LLM_MAX_TOKENS,
        },
        retrieval={
            "dense_top_k": settings.DENSE_TOP_K,
            "sparse_top_k": settings.SPARSE_TOP_K,
            "reranker_top_n": settings.RERANKER_TOP_N,
            "bm25_threshold": settings.BM25_SCORE_THRESHOLD,
        },
        cache={
            "redis_faq_ttl_hours": settings.REDIS_FAQ_TTL // 3600,
            "redis_hot_threshold": settings.REDIS_FAQ_HOT_THRESHOLD,
            "redis_hot_ttl_days": settings.REDIS_FAQ_HOT_TTL // 86400,
        },
    )


@router.put("/settings")
async def update_settings(req: SettingsUpdateRequest, current_user: dict = Depends(get_current_admin_user)):
    """
    Update runtime settings.

    Note: these are in-memory only and reset on restart.
    For persistent changes, edit the .env file.
    """
    if req.llm_model is not None:
        settings.LLM_MODEL = req.llm_model
    if req.llm_temperature is not None:
        settings.LLM_TEMPERATURE = req.llm_temperature
    if req.llm_max_tokens is not None:
        settings.LLM_MAX_TOKENS = req.llm_max_tokens
    if req.dense_top_k is not None:
        settings.DENSE_TOP_K = req.dense_top_k
    if req.sparse_top_k is not None:
        settings.SPARSE_TOP_K = req.sparse_top_k
    if req.reranker_top_n is not None:
        settings.RERANKER_TOP_N = req.reranker_top_n
    if req.bm25_threshold is not None:
        settings.BM25_SCORE_THRESHOLD = req.bm25_threshold
    if req.redis_faq_ttl is not None:
        settings.REDIS_FAQ_TTL = req.redis_faq_ttl
    if req.redis_hot_threshold is not None:
        settings.REDIS_FAQ_HOT_THRESHOLD = req.redis_hot_threshold

    return {"status": "ok"}
