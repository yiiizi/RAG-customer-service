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
from loguru import logger
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect, status
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
    KBDeleteRequest,
    KBDeleteResponse,
    KBUploadResponse,
    SettingsResponse,
    SettingsUpdateRequest,
)
from config.settings import settings
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
from offline_kb.indexer import delete_index, get_stats, index_directory, index_file, reindex_file
from rag_qa.pipeline import ask, ask_stream

router = APIRouter()

# ── Static file serving for uploads ─────────────────────────────────
KB_UPLOAD_DIR = settings.KB_UPLOAD_DIR
KB_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ═════════════════════════════════════════════════════════════════════
#  CHAT
# ═════════════════════════════════════════════════════════════════════

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Non-streaming Q&A."""
    try:
        result = await ask(req.query, kb_only=req.kb_only, web_search=req.web_search, history=req.history)
        return ChatResponse(
            answer=result.answer,
            intent=result.intent,
            sources=[
                {"text": s["text"], "source": s.get("source", ""), "score": s.get("score", 0.0), "chunk_index": s.get("chunk_index", -1)}
                for s in result.sources
            ],
            latency_ms=result.latency_ms,
        )
    except Exception as e:
        logger.exception("Chat error")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws/chat")
async def ws_chat(ws: WebSocket):
    """Streaming Q&A via WebSocket (token-by-token typing effect)."""
    await ws.accept()
    try:
        while True:
            raw = await ws.receive_text()
            data = json.loads(raw)
            query = data.get("query", "").strip()
            kb_only = data.get("kb_only", False)
            web_search = data.get("web_search", False)
            history = data.get("history", None)
            logger.info(f"WS: query='{query}' kb_only={kb_only} web_search={web_search} history_len={len(history) if history else 0}")
            if not query:
                await ws.send_json({"type": "error", "data": "Empty query"})
                continue

            try:
                async for chunk in ask_stream(query, kb_only=kb_only, web_search=web_search, history=history):
                    await ws.send_json(chunk)
                await ws.send_json({"type": "finish", "data": {}})
            except Exception as e:
                logger.exception("Stream error")
                await ws.send_json({"type": "error", "data": str(e)})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")


# ═════════════════════════════════════════════════════════════════════
#  KNOWLEDGE BASE
# ═════════════════════════════════════════════════════════════════════

@router.post("/kb/upload", response_model=KBUploadResponse)
async def kb_upload(file: UploadFile = File(...)):
    """Upload a single file and index it into the knowledge base."""
    # Fix encoding for Chinese filenames on Windows
    raw_name = file.filename or "unknown"
    try:
        safe_name = raw_name.encode("latin-1").decode("utf-8")
    except (UnicodeDecodeError, UnicodeEncodeError):
        safe_name = raw_name
    ext = Path(safe_name).suffix.lower()
    if ext not in settings.KB_SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

    # Save to upload dir
    file_path = KB_UPLOAD_DIR / safe_name
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

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
async def kb_upload_dir(directory: str = Query(..., description="Directory path to index")):
    """Index all supported files from a directory."""
    try:
        result = await index_directory(directory)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/stats")
async def kb_stats():
    """Get Milvus collection statistics."""
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kb/list")
async def kb_list():
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
async def kb_chunks(file_name: str):
    """Get all chunks for a specific file with parent-child relationships."""
    try:
        from rag_qa.milvus_store import get_collection
        col = get_collection()
        # Query all chunks for this file
        results = col.query(
            expr=f'file_name == "{file_name}"',
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
async def kb_delete(file_name: str):
    """Remove all chunks belonging to a file from the knowledge base."""
    try:
        result = await delete_index(file_name)
        return KBDeleteResponse(
            status="ok", file_name=file_name, chunks_removed=result.get("chunks_removed", 0)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/kb/reindex")
async def kb_reindex(file_name: str = Query(..., description="File name to re-index")):
    """Re-index a previously uploaded file."""
    file_path = KB_UPLOAD_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_name}")
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
    session: AsyncSession = Depends(get_session),
):
    """Search and list FAQ entries."""
    try:
        items = await faq_search(session, keyword=keyword, category=category, offset=offset, limit=limit)
        total = await faq_total_count(session)
        return FAQListResponse(
            items=[
                FAQItem(
                    id=item.id,
                    question=item.question,
                    answer=item.answer,
                    frequency=item.frequency,
                    category=item.category,
                    created_at=item.created_at.isoformat() if item.created_at else None,
                    updated_at=item.updated_at.isoformat() if item.updated_at else None,
                )
                for item in items
            ],
            total=total,
        )
    except Exception as e:
        logger.exception("FAQ list error")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/faq", response_model=FAQItem)
async def faq_create(
    req: FAQCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new FAQ entry."""
    faq = await faq_upsert(session, req.question, req.answer, req.category)
    await session.commit()
    return FAQItem(
        id=faq.id,
        question=faq.question,
        answer=faq.answer,
        frequency=faq.frequency,
        category=faq.category,
    )


@router.put("/faq/{faq_id}", response_model=FAQItem)
async def faq_update(
    faq_id: str,
    req: FAQUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update an existing FAQ entry."""
    from mysql_module.models import FAQPair
    from sqlalchemy import select

    stmt = select(FAQPair).where(FAQPair.id == faq_id)
    result = await session.execute(stmt)
    faq = result.scalar_one_or_none()
    if not faq:
        raise HTTPException(status_code=404, detail="FAQ not found")

    if req.question is not None:
        faq.question = req.question
    if req.answer is not None:
        faq.answer = req.answer
    if req.category is not None:
        faq.category = req.category

    session.add(faq)
    await session.commit()
    await session.refresh(faq)

    return FAQItem(
        id=faq.id,
        question=faq.question,
        answer=faq.answer,
        frequency=faq.frequency,
        category=faq.category,
    )


@router.delete("/faq/{faq_id}")
async def faq_delete_route(
    faq_id: str,
    session: AsyncSession = Depends(get_session),
):
    """Delete a FAQ entry."""
    deleted = await faq_delete(session, faq_id)
    await session.commit()
    if not deleted:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return {"status": "deleted", "id": faq_id}


@router.post("/faq/batch-import", response_model=FAQBatchImportResponse)
async def faq_batch_import(
    req: FAQBatchImportRequest,
    session: AsyncSession = Depends(get_session),
):
    """Bulk import FAQ entries."""
    imported = 0
    skipped = 0
    errors: list[str] = []

    for item in req.items:
        try:
            await faq_upsert(session, item.question, item.answer, item.category)
            imported += 1
        except Exception as e:
            errors.append(f"{item.question[:30]}...: {e}")
            skipped += 1

    await session.commit()
    return FAQBatchImportResponse(imported=imported, skipped=skipped, errors=errors)


# ═════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ═════════════════════════════════════════════════════════════════════

@router.get("/dashboard", response_model=DashboardStats)
async def dashboard(session: AsyncSession = Depends(get_session)):
    """Aggregated analytics for the dashboard page."""
    try:
        stats = await qalog_stats(session)
        top_faqs = await faq_get_hot(session, top_n=10)
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
        top_faqs=[
            FAQItem(
                id=f.id,
                question=f.question,
                answer=f.answer,
                frequency=f.frequency,
                category=f.category,
            )
            for f in top_faqs
        ],
        milvus_stats=milvus_stats,
    )
    except Exception as e:
        logger.exception("Dashboard error")
        raise HTTPException(status_code=500, detail=str(e))


# ═════════════════════════════════════════════════════════════════════
#  SETTINGS
# ═════════════════════════════════════════════════════════════════════

@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
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
async def update_settings(req: SettingsUpdateRequest):
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
