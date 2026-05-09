"""
RAG Q&A Pipeline — main orchestrator.

Wires together: intent → strategy routing → retrieval → generation → logging.
Supports e-commerce intents: order_query, logistics_track.
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from loguru import logger
from config.settings import settings
from mysql_module import redis_cache
from rag_qa.generator import generate, generate_stream
from rag_qa.intent_recognizer import recognize
from rag_qa.retriever import retrieve
from rag_qa.strategy_selector import StrategyResult, selector
from rag_qa.web_search import web_search as do_web_search
from rag_qa.ecommerce_mock import query_order, query_logistics
from rag_qa.content_filter import full_check, filter_response


# ── Strategy implementations ──────────────────────────────────────

async def _strategy_chat(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """Direct LLM chat — no retrieval."""
    answer = await generate(query, contexts=None, intent="chat", history=extra.get("history"))
    return {"answer": answer, "sources": [], "metadata": {"intent": "chat"}}


async def _strategy_faq(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """Cache-first FAQ path: Redis → MySQL → fallback retrieval."""
    cached = await redis_cache.faq_cache_get(query)
    if cached:
        logger.info("FAQ: Redis hit")
        return {
            "answer": cached["answer"],
            "sources": [],
            "metadata": {"intent": "faq", "cache": "redis", "frequency": cached.get("frequency", 0)},
        }

    from mysql_module.dao import faq_get_by_question, async_session
    async with async_session() as session:
        faq = await faq_get_by_question(session, query)
        if faq:
            logger.info(f"FAQ: MySQL hit (freq={faq.frequency})")
            await redis_cache.faq_cache_set(faq.question, faq.answer, faq.frequency)
            return {
                "answer": faq.answer,
                "sources": [],
                "metadata": {"intent": "faq", "cache": "mysql", "frequency": faq.frequency, "id": faq.id},
            }

    logger.info("FAQ: cache miss — falling back to full retrieval")
    contexts = retrieve(query)
    answer = await generate(query, contexts=contexts, intent="knowledge_qa", history=extra.get("history"))
    return {"answer": answer, "sources": contexts, "metadata": {"intent": "faq", "fallback": True}}


async def _strategy_knowledge_qa(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """Full hybrid retrieval + generation. Also checks FAQ cache first."""
    # Check FAQ cache before retrieval
    cached = await redis_cache.faq_cache_get(query)
    if cached:
        logger.info("knowledge_qa: FAQ Redis hit")
        return {"answer": cached["answer"], "sources": [], "metadata": {"intent": "faq", "cache": "redis"}}

    from mysql_module.dao import faq_get_by_question, async_session
    async with async_session() as session:
        faq = await faq_get_by_question(session, query)
    if faq:
        logger.info(f"knowledge_qa: FAQ MySQL hit")
        await redis_cache.faq_cache_set(faq.question, faq.answer, faq.frequency)
        return {"answer": faq.answer, "sources": [], "metadata": {"intent": "faq", "cache": "mysql"}}

    contexts = retrieve(query)
    if extra.get("kb_only") and not contexts:
        return {"answer": "知识库中未找到相关内容，请尝试换个问题或上传相关文档。", "sources": [], "metadata": {"intent": "knowledge_qa", "kb_only": True}}
    answer = await generate(query, contexts=contexts, intent="knowledge_qa", history=extra.get("history"))
    return {"answer": answer, "sources": contexts, "metadata": {"intent": "knowledge_qa"}}


async def _strategy_order_query(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """Order query: fetch order data + LLM generation."""
    order_info = query_order()
    answer = await generate(query, intent="order_query", extra_info=order_info, history=extra.get("history"))
    return {"answer": answer, "sources": [], "metadata": {"intent": "order_query"}}


async def _strategy_logistics_track(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """Logistics tracking: fetch logistics data + LLM generation."""
    logistics_info = query_logistics()
    answer = await generate(query, intent="logistics_track", extra_info=logistics_info, history=extra.get("history"))
    return {"answer": answer, "sources": [], "metadata": {"intent": "logistics_track"}}


# Register strategies
selector.register("chat", _strategy_chat)
selector.register("faq", _strategy_faq)
selector.register("knowledge_qa", _strategy_knowledge_qa)
selector.register("order_query", _strategy_order_query)
selector.register("logistics_track", _strategy_logistics_track)


# ── Public API ────────────────────────────────────────────────────

async def ask(
    query: str,
    kb_only: bool = False,
    web_search: bool = False,
    history: list[dict] | None = None,
) -> StrategyResult:
    """
    Ask a question through the full RAG pipeline.
    """
    import time
    start = time.perf_counter()

    # Content safety check
    check = full_check(query)
    if not check["safe"]:
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="blocked", intent="blocked",
            answer=check["reason"], sources=[], latency_ms=elapsed,
            metadata={"blocked": True},
        )
    query = check["cleaned"]

    # Handle KB + web search combinations
    if kb_only and web_search:
        # Both enabled: combine KB + web results
        import asyncio
        kb_sources = retrieve(query)
        web_results = await do_web_search(query)
        web_sources = [{"text": wr["text"], "source": wr.get("source", "互联网"), "score": 0, "parent_id": "", "chunk_index": -1} for wr in web_results]
        combined = kb_sources + web_sources
        if combined:
            answer = await generate(query, contexts=combined, intent="knowledge_qa", history=history)
        else:
            answer = "知识库和网络搜索均未找到相关内容。"
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(strategy_name="kb_web", intent="联网搜索", answer=answer, sources=combined, latency_ms=elapsed, metadata={"kb_only": True, "web_search": True})

    if kb_only:
        sources = retrieve(query)
        if not sources:
            answer = "知识库中未找到相关内容，请尝试换个问题或上传相关文档。"
        else:
            answer = await generate(query, contexts=sources, intent="knowledge_qa", history=history)
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="knowledge_qa", intent="knowledge_qa",
            answer=answer, sources=sources, latency_ms=elapsed,
            metadata={"kb_only": True},
        )

    intent, confidence = await recognize(query)

    if web_search:
        web_results = await do_web_search(query)
        web_sources = [{
            "text": wr["text"],
            "source": wr.get("source", "互联网"),
            "score": 0,
            "parent_id": "",
            "chunk_index": -1,
        } for wr in web_results]
        if web_sources:
            answer = await generate(query, contexts=web_sources, intent="knowledge_qa", history=history)
        else:
            answer = await generate(query, contexts=None, intent="chat", history=history)
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="web_search", intent="联网搜索",
            answer=answer, sources=web_sources, latency_ms=elapsed,
            metadata={"web_search": True},
        )

    # For order/logistics intents, check FAQ first
    if intent in ("order_query", "logistics_track"):
        cached = await redis_cache.faq_cache_get(query)
        if cached:
            elapsed = int((time.perf_counter() - start) * 1000)
            return StrategyResult(strategy_name="faq", intent="faq", answer=cached["answer"], sources=[], latency_ms=elapsed, metadata={"cache": "redis"})
        from mysql_module.dao import faq_get_by_question as _fbq, async_session as _sess
        async with _sess() as _s:
            faq = await _fbq(_s, query)
        if faq:
            elapsed = int((time.perf_counter() - start) * 1000)
            return StrategyResult(strategy_name="faq", intent="faq", answer=faq.answer, sources=[], latency_ms=elapsed, metadata={"cache": "mysql"})

    result = await selector.route(intent, query, extra={"kb_only": False, "history": history})

    try:
        from mysql_module.dao import async_session, qalog_insert, faq_increment_frequency
        async with async_session() as session:
            await qalog_insert(
                session,
                query=query,
                intent=intent,
                answer=result.answer,
                latency_ms=result.latency_ms,
                hit_faq=(result.metadata.get("cache") in ("redis", "mysql")),
            )
            if result.metadata.get("cache") == "mysql":
                await faq_increment_frequency(session, query)
            await session.commit()
    except Exception:
        logger.exception("Failed to log QA record (non-fatal)")

    return result


async def ask_stream(
    query: str,
    kb_only: bool = False,
    web_search: bool = False,
    history: list[dict] | None = None,
):
    """
    Streaming version — yields chunks.
    """
    # Content safety check
    check = full_check(query)
    if not check["safe"]:
        yield {"type": "sources", "data": []}
        yield {"type": "token", "data": check["reason"]}
        yield {"type": "done", "data": {"intent": "blocked"}}
        return
    query = check["cleaned"]

    logger.info(f"STREAM: query='{query}' kb_only={kb_only} web_search={web_search}")

    # Handle KB + web search combinations
    if kb_only and web_search:
        import asyncio
        kb_sources = retrieve(query)
        web_results = await do_web_search(query)
        web_sources = [{"text": wr["text"], "source": wr.get("source", "互联网"), "score": 0, "parent_id": "", "chunk_index": -1} for wr in web_results]
        combined = kb_sources + web_sources
        yield {"type": "sources", "data": combined}
        if combined:
            stream = generate_stream(query, contexts=combined, intent="knowledge_qa", history=history)
            async for token in stream:
                yield {"type": "token", "data": token}
        else:
            yield {"type": "token", "data": "知识库和网络搜索均未找到相关内容。"}
        yield {"type": "done", "data": {"intent": "联网搜索", "kb_only": True, "web_search": True}}
        return

    if kb_only:
        sources = retrieve(query)
        yield {"type": "sources", "data": sources}
        if not sources:
            yield {"type": "token", "data": "知识库中未找到相关内容，请尝试换个问题或上传相关文档。"}
        else:
            stream = generate_stream(query, contexts=sources, intent="knowledge_qa", history=history)
            async for token in stream:
                yield {"type": "token", "data": token}
        yield {"type": "done", "data": {"intent": "knowledge_qa", "kb_only": True}}
        return

    intent, confidence = await recognize(query)
    logger.info(f"STREAM: intent={intent} conf={confidence} query='{query[:30]}'")

    if web_search:
        import asyncio
        # Only fetch web results (don't mix with KB unless kb_only is also set)
        web_results = await do_web_search(query)
        web_sources = [{
            "text": wr["text"],
            "source": wr.get("source", "互联网"),
            "score": 0,
            "parent_id": "",
            "chunk_index": -1,
        } for wr in web_results]

        if web_sources:
            yield {"type": "sources", "data": web_sources}
            stream = generate_stream(query, contexts=web_sources, intent="knowledge_qa", history=history)
        else:
            yield {"type": "sources", "data": []}
            stream = generate_stream(query, contexts=None, intent="chat", history=history)
        async for token in stream:
            yield {"type": "token", "data": token}
        yield {"type": "done", "data": {"intent": "联网搜索", "web_search": True}}
        return

    if intent == "chat":
        sources = []
        stream = generate_stream(query, contexts=None, intent="chat", history=history)
    elif intent in ("order_query", "logistics_track"):
        # Check FAQ cache first before using mock data
        cached = await redis_cache.faq_cache_get(query)
        if cached:
            logger.info(f"STREAM: order/logistics -> FAQ Redis hit")
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": cached["answer"]}
            yield {"type": "done", "data": {"intent": "faq", "cache": "redis"}}
            return
        from mysql_module.dao import faq_get_by_question, async_session as _sess
        async with _sess() as _session:
            faq = await faq_get_by_question(_session, query)
        if faq:
            logger.info(f"STREAM: order/logistics -> FAQ MySQL hit: {faq.question[:30]}")
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": faq.answer}
            yield {"type": "done", "data": {"intent": "faq", "cache": "mysql"}}
            return
        logger.info(f"STREAM: order/logistics -> No FAQ match, using mock data")
        # No FAQ match — use mock data + LLM
        sources = []
        if intent == "order_query":
            order_info = query_order()
            stream = generate_stream(query, intent="order_query", extra_info=order_info, history=history)
        else:
            logistics_info = query_logistics()
            stream = generate_stream(query, intent="logistics_track", extra_info=logistics_info, history=history)
    elif intent == "faq":
        cached = await redis_cache.faq_cache_get(query)
        if cached:
            logger.info(f"STREAM: faq -> Redis hit")
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": cached["answer"]}
            yield {"type": "done", "data": {"intent": "faq", "cache": "redis"}}
            return
        from mysql_module.dao import faq_get_by_question, async_session
        async with async_session() as session:
            faq = await faq_get_by_question(session, query)
        if faq:
            logger.info(f"STREAM: faq -> MySQL hit: {faq.question[:30]}")
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": faq.answer}
            yield {"type": "done", "data": {"intent": "faq", "cache": "mysql"}}
            return
        logger.info(f"STREAM: faq -> MISS, falling back to retrieval")
        sources = retrieve(query)
        stream = generate_stream(query, contexts=sources, intent="knowledge_qa", history=history)
    else:
        sources = retrieve(query)
        stream = generate_stream(query, contexts=sources, intent="knowledge_qa", history=history)

    yield {"type": "sources", "data": sources}

    async for token in stream:
        yield {"type": "token", "data": token}

    yield {"type": "done", "data": {"intent": intent}}
