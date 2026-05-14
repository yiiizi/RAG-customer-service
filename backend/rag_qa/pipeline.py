"""
RAG 问答流水线 — 主编排器。

连接：意图识别 → 策略路由 → 检索 → 生成 → 日志记录。
支持电商意图：订单查询、物流追踪。
"""

from __future__ import annotations

import logging
from typing import Any

from backend.business.logistics_service import logistics_service
from backend.business.order_service import order_service, resolve_order_followup
from backend.business.product_service import product_service
from backend.mysql_module import redis_cache
from backend.rag_qa.generator import generate, generate_stream
from backend.rag_qa.intent_recognizer import recognize
from backend.rag_qa.retriever import retrieve
from backend.rag_qa.strategy_selector import StrategyResult, selector
from backend.rag_qa.web_search import web_search as do_web_search
from backend.rag_qa.content_filter import full_check

logger = logging.getLogger(__name__)


async def _lookup_faq(query: str) -> dict[str, Any] | None:
    cached = await redis_cache.faq_cache_get(query)
    if cached:
        return {
            "answer": cached["answer"],
            "metadata": {"intent": "faq", "cache": "redis", "frequency": cached.get("frequency", 0)},
        }

    from backend.mysql_module.dao import async_session, faq_increment_frequency
    from backend.mysql_module.faq_semantic import search_active_faq

    async with async_session() as session:
        match = await search_active_faq(session, query)
        if not match:
            return None
        faq = match.faq
        await redis_cache.faq_cache_set(faq.question, faq.answer, faq.frequency)
        if query != faq.question:
            await redis_cache.faq_cache_set(query, faq.answer, faq.frequency)
        await faq_increment_frequency(session, faq.question)
        await session.commit()
        return {
            "answer": faq.answer,
            "metadata": {
                "intent": "faq",
                "cache": "semantic",
                "id": faq.id,
                "faq_score": round(match.score, 4),
                "match_source": match.source,
            },
        }


# ── 策略实现 ──────────────────────────────────────────────────────

async def _strategy_chat(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """直接 LLM 对话 — 无检索。"""
    answer = await generate(query, contexts=None, intent="chat", history=extra.get("history"), model_cfg=extra.get("model_cfg"))
    return {"answer": answer, "sources": [], "metadata": {"intent": "chat"}}


async def _strategy_faq(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    faq_hit = await _lookup_faq(query)
    if faq_hit:
        logger.info("FAQ hit: %s", faq_hit["metadata"])
        return {"answer": faq_hit["answer"], "sources": [], "metadata": faq_hit["metadata"]}

    """优先缓存 FAQ：Redis → MySQL → 回退检索。"""
    cached = await redis_cache.faq_cache_get(query)
    if cached:
        logger.info("FAQ：Redis 命中")
        return {
            "answer": cached["answer"],
            "sources": [],
            "metadata": {"intent": "faq", "cache": "redis", "frequency": cached.get("frequency", 0)},
        }

    from backend.mysql_module.dao import faq_get_by_question, async_session
    async with async_session() as session:
        faq = await faq_get_by_question(session, query)
        if faq:
            logger.info("FAQ：MySQL 命中 (freq=%s)", faq.frequency)
            await redis_cache.faq_cache_set(faq.question, faq.answer, faq.frequency)
            return {
                "answer": faq.answer,
                "sources": [],
                "metadata": {"intent": "faq", "cache": "mysql", "frequency": faq.frequency, "id": faq.id},
            }

    logger.info("FAQ：缓存未命中 — 回退到完整检索")
    contexts = retrieve(query)
    answer = await generate(query, contexts=contexts, intent="knowledge_qa", history=extra.get("history"), model_cfg=extra.get("model_cfg"))
    return {"answer": answer, "sources": contexts, "metadata": {"intent": "faq", "fallback": True}}


async def _strategy_knowledge_qa(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    faq_hit = await _lookup_faq(query)
    if faq_hit:
        logger.info("knowledge_qa FAQ hit: %s", faq_hit["metadata"])
        return {"answer": faq_hit["answer"], "sources": [], "metadata": faq_hit["metadata"]}

    """完整混合检索 + 生成。检索前优先查 FAQ 缓存。"""
    cached = await redis_cache.faq_cache_get(query)
    if cached:
        logger.info("knowledge_qa：FAQ Redis 命中")
        return {"answer": cached["answer"], "sources": [], "metadata": {"intent": "faq", "cache": "redis"}}

    from backend.mysql_module.dao import faq_get_by_question, async_session
    async with async_session() as session:
        faq = await faq_get_by_question(session, query)
    if faq:
        logger.info("knowledge_qa：FAQ MySQL 命中")
        await redis_cache.faq_cache_set(faq.question, faq.answer, faq.frequency)
        return {"answer": faq.answer, "sources": [], "metadata": {"intent": "faq", "cache": "mysql"}}

    contexts = retrieve(query)
    if extra.get("kb_only") and not contexts:
        return {"answer": "知识库中未找到相关内容，请尝试换个问题或上传相关文档。", "sources": [], "metadata": {"intent": "knowledge_qa", "kb_only": True}}
    answer = await generate(query, contexts=contexts, intent="knowledge_qa", history=extra.get("history"), model_cfg=extra.get("model_cfg"))
    return {"answer": answer, "sources": contexts, "metadata": {"intent": "knowledge_qa"}}


async def _strategy_order_query(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """订单查询：获取订单数据 + LLM 生成。"""
    resolved = await order_service.resolve(extra.get("user_id"), query)
    if resolved.get("needs_more_info"):
        return {
            "answer": resolved["text"],
            "sources": [],
            "metadata": {"intent": "order_query", "needs_more_info": True},
        }
    answer = await generate(query, intent="order_query", extra_info=resolved["text"], history=extra.get("history"), model_cfg=extra.get("model_cfg"))
    return {"answer": answer, "sources": [], "metadata": {"intent": "order_query", "order_id": resolved.get("order_id")}}


async def _strategy_logistics_track(query: str, extra: dict[str, Any]) -> dict[str, Any]:
    """物流追踪：获取物流数据 + LLM 生成。"""
    resolved = await logistics_service.resolve(extra.get("user_id"), query)
    if resolved.get("needs_more_info"):
        return {
            "answer": resolved["text"],
            "sources": [],
            "metadata": {"intent": "logistics_track", "needs_more_info": True},
        }
    answer = await generate(query, intent="logistics_track", extra_info=resolved["text"], history=extra.get("history"), model_cfg=extra.get("model_cfg"))
    return {"answer": answer, "sources": [], "metadata": {"intent": "logistics_track", "logistics_no": resolved.get("logistics_no")}}


# 注册策略
selector.register("chat", _strategy_chat)  # type: ignore
selector.register("faq", _strategy_faq)  # type: ignore
selector.register("knowledge_qa", _strategy_knowledge_qa)  # type: ignore
selector.register("order_query", _strategy_order_query)  # type: ignore
selector.register("logistics_track", _strategy_logistics_track)  # type: ignore


# ── 公开 API ──────────────────────────────────────────────────────

async def _get_model_cfg(model_config_id: int | None) -> dict | None:
    """Fetch the admin-managed default model config.

    ``model_config_id`` is intentionally ignored for normal chat. Model
    selection is centrally managed by admins; if no default exists the
    generator falls back to settings from .env.
    """
    try:
        from backend.mysql_module.dao import async_session
        from backend.mysql_module.model_config import get_global_default_model_config
        from backend.utils.encryption import decrypt_api_key
        async with async_session() as session:
            cfg = await get_global_default_model_config(session)
            if not cfg:
                return None
            return {
                "model": cfg.model_name,
                "api_base": cfg.base_url or "https://api.openai.com/v1",
                "api_key": decrypt_api_key(cfg.api_key_encrypted),
                "temperature": cfg.temperature,
                "max_tokens": cfg.max_tokens,
            }
    except Exception:
        logger.exception("Failed to load default model config")
        return None


async def ask(
    query: str,
    kb_only: bool = False,
    web_search: bool = False,
    history: list[dict[str, Any]] | None = None,
    model_config_id: int | None = None,
    user_id: int | None = None,
) -> StrategyResult:
    """
    通过完整 RAG 流水线提问。
    """
    import time
    start = time.perf_counter()

    # Load model config once
    model_cfg = await _get_model_cfg(model_config_id)

    # 内容安全检查
    check = full_check(query)
    if not check["safe"]:
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="blocked", intent="blocked",
            answer=check["reason"], sources=[], latency_ms=elapsed,
            metadata={"blocked": True},
        )
    query = check["cleaned"]

    product_result = product_service.resolve(query, history)
    if product_result:
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="product_query",
            intent="knowledge_qa",
            answer=product_result["answer"],
            sources=product_result.get("sources", []),
            latency_ms=elapsed,
            metadata={
                "intent": "knowledge_qa",
                "product_id": product_result.get("product_id"),
                "product_query": True,
                "product_followup": bool(product_result.get("is_followup")),
            },
        )

    followup = resolve_order_followup(user_id, query, history)
    if followup:
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="order_followup",
            intent="order_query",
            answer=followup["text"],
            sources=[],
            latency_ms=elapsed,
            metadata={
                "intent": "order_query",
                "order_id": followup.get("order_id"),
                "item_followup": True,
                "needs_more_info": bool(followup.get("needs_more_info")),
            },
        )

    # 同时启用知识库 + 网络搜索
    if kb_only and web_search:
        kb_sources = retrieve(query)
        web_results = await do_web_search(query)
        web_sources = [{"text": wr["text"], "source": wr.get("source", "互联网"), "score": 0, "parent_id": "", "chunk_index": -1} for wr in web_results]
        combined = kb_sources + web_sources
        if combined:
            answer = await generate(query, contexts=combined, intent="knowledge_qa", history=history, model_cfg=model_cfg)
        else:
            answer = "知识库和网络搜索均未找到相关内容。"
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(strategy_name="kb_web", intent="联网搜索", answer=answer, sources=combined, latency_ms=elapsed, metadata={"kb_only": True, "web_search": True})

    if kb_only:
        sources = retrieve(query)
        if not sources:
            answer = "知识库中未找到相关内容，请尝试换个问题或上传相关文档。"
        else:
            answer = await generate(query, contexts=sources, intent="knowledge_qa", history=history, model_cfg=model_cfg)
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="knowledge_qa", intent="knowledge_qa",
            answer=answer, sources=sources, latency_ms=elapsed,
            metadata={"kb_only": True},
        )

    faq_hit = await _lookup_faq(query)
    if faq_hit:
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="faq",
            intent="faq",
            answer=faq_hit["answer"],
            sources=[],
            latency_ms=elapsed,
            metadata=faq_hit["metadata"],
        )

    intent, _confidence = await recognize(query)

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
            answer = await generate(query, contexts=web_sources, intent="knowledge_qa", history=history, model_cfg=model_cfg)
        else:
            answer = await generate(query, contexts=None, intent="chat", history=history, model_cfg=model_cfg)
        elapsed = int((time.perf_counter() - start) * 1000)
        return StrategyResult(
            strategy_name="web_search", intent="联网搜索",
            answer=answer, sources=web_sources, latency_ms=elapsed,
            metadata={"web_search": True},
        )

    # 订单/物流意图先查 FAQ
    if intent in ("order_query", "logistics_track"):
        cached = await redis_cache.faq_cache_get(query)
        if cached:
            elapsed = int((time.perf_counter() - start) * 1000)
            return StrategyResult(strategy_name="faq", intent="faq", answer=cached["answer"], sources=[], latency_ms=elapsed, metadata={"cache": "redis"})
        from backend.mysql_module.dao import faq_get_by_question as _fbq, async_session as _sess
        async with _sess() as _s:
            faq = await _fbq(_s, query)
        if faq:
            elapsed = int((time.perf_counter() - start) * 1000)
            return StrategyResult(strategy_name="faq", intent="faq", answer=faq.answer, sources=[], latency_ms=elapsed, metadata={"cache": "mysql"})

    result = await selector.route(
        intent,
        query,
        extra={"kb_only": False, "history": history, "model_cfg": model_cfg, "user_id": user_id},
    )

    try:
        from backend.mysql_module.dao import async_session, qalog_insert, faq_increment_frequency
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
        logger.exception("记录问答日志失败（非致命）")

    return result


async def ask_stream(
    query: str,
    kb_only: bool = False,
    web_search: bool = False,
    history: list[dict[str, Any]] | None = None,
    model_config_id: int | None = None,
    user_id: int | None = None,
):
    """
    流式版本 — 逐块返回。
    """
    # Load model config once
    model_cfg = await _get_model_cfg(model_config_id)

    # 内容安全检查
    check = full_check(query)
    if not check["safe"]:
        yield {"type": "sources", "data": []}
        yield {"type": "token", "data": check["reason"]}
        yield {"type": "done", "data": {"intent": "blocked"}}
        return
    query = check["cleaned"]

    product_result = product_service.resolve(query, history)
    if product_result:
        yield {"type": "sources", "data": product_result.get("sources", [])}
        yield {"type": "token", "data": product_result["answer"]}
        yield {
            "type": "done",
            "data": {
                "intent": "knowledge_qa",
                "product_id": product_result.get("product_id"),
                "product_query": True,
                "product_followup": bool(product_result.get("is_followup")),
            },
        }
        return

    followup = resolve_order_followup(user_id, query, history)
    if followup:
        yield {"type": "sources", "data": []}
        yield {"type": "token", "data": followup["text"]}
        yield {
            "type": "done",
            "data": {
                "intent": "order_query",
                "order_id": followup.get("order_id"),
                "item_followup": True,
                "needs_more_info": bool(followup.get("needs_more_info")),
            },
        }
        return

    logger.info("STREAM: query='%s' kb_only=%s web_search=%s", query, kb_only, web_search)

    # 同时启用知识库 + 网络搜索
    if kb_only and web_search:
        kb_sources = retrieve(query)
        web_results = await do_web_search(query)
        web_sources = [{"text": wr["text"], "source": wr.get("source", "互联网"), "score": 0, "parent_id": "", "chunk_index": -1} for wr in web_results]
        combined = kb_sources + web_sources
        yield {"type": "sources", "data": combined}
        if combined:
            stream = generate_stream(query, contexts=combined, intent="knowledge_qa", history=history, model_cfg=model_cfg)
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
            stream = generate_stream(query, contexts=sources, intent="knowledge_qa", history=history, model_cfg=model_cfg)
            async for token in stream:
                yield {"type": "token", "data": token}
        yield {"type": "done", "data": {"intent": "knowledge_qa", "kb_only": True}}
        return

    faq_hit = await _lookup_faq(query)
    if faq_hit:
        yield {"type": "sources", "data": []}
        yield {"type": "token", "data": faq_hit["answer"]}
        yield {"type": "done", "data": faq_hit["metadata"]}
        return

    intent, _confidence = await recognize(query)
    logger.info("STREAM: intent=%s conf=%s query='%s...'", intent, _confidence, query[:30])

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
            yield {"type": "sources", "data": web_sources}
            stream = generate_stream(query, contexts=web_sources, intent="knowledge_qa", history=history, model_cfg=model_cfg)
        else:
            yield {"type": "sources", "data": []}
            stream = generate_stream(query, contexts=None, intent="chat", history=history, model_cfg=model_cfg)
        async for token in stream:
            yield {"type": "token", "data": token}
        yield {"type": "done", "data": {"intent": "联网搜索", "web_search": True}}
        return

    if intent in {"faq", "knowledge_qa", "order_query", "logistics_track"}:
        faq_hit = await _lookup_faq(query)
        if faq_hit:
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": faq_hit["answer"]}
            yield {"type": "done", "data": faq_hit["metadata"]}
            return

    if intent == "chat":
        sources = []
        stream = generate_stream(query, contexts=None, intent="chat", history=history, model_cfg=model_cfg)
    elif intent in ("order_query", "logistics_track"):
        # 先查 FAQ 缓存再使用模拟数据
        cached = await redis_cache.faq_cache_get(query)
        if cached:
            logger.info("STREAM: order/logistics -> FAQ Redis 命中")
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": cached["answer"]}
            yield {"type": "done", "data": {"intent": "faq", "cache": "redis"}}
            return
        from backend.mysql_module.dao import faq_get_by_question, async_session as _sess
        async with _sess() as _session:
            faq = await faq_get_by_question(_session, query)
        if faq:
            logger.info("STREAM: order/logistics -> FAQ MySQL 命中: %s", faq.question[:30])
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": faq.answer}
            yield {"type": "done", "data": {"intent": "faq", "cache": "mysql"}}
            return
        logger.info("STREAM: order/logistics -> 无 FAQ 匹配，使用模拟数据")
        sources = []
        if intent == "order_query":
            resolved = await order_service.resolve(user_id, query)
            if resolved.get("needs_more_info"):
                yield {"type": "sources", "data": []}
                yield {"type": "token", "data": resolved["text"]}
                yield {"type": "done", "data": {"intent": "order_query", "needs_more_info": True}}
                return
            stream = generate_stream(query, intent="order_query", extra_info=resolved["text"], history=history, model_cfg=model_cfg)
        else:
            resolved = await logistics_service.resolve(user_id, query)
            if resolved.get("needs_more_info"):
                yield {"type": "sources", "data": []}
                yield {"type": "token", "data": resolved["text"]}
                yield {"type": "done", "data": {"intent": "logistics_track", "needs_more_info": True}}
                return
            stream = generate_stream(query, intent="logistics_track", extra_info=resolved["text"], history=history, model_cfg=model_cfg)
    elif intent == "faq":
        cached = await redis_cache.faq_cache_get(query)
        if cached:
            logger.info("STREAM: faq -> Redis 命中")
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": cached["answer"]}
            yield {"type": "done", "data": {"intent": "faq", "cache": "redis"}}
            return
        from backend.mysql_module.dao import faq_get_by_question, async_session
        async with async_session() as session:
            faq = await faq_get_by_question(session, query)
        if faq:
            logger.info("STREAM: faq -> MySQL 命中: %s", faq.question[:30])
            yield {"type": "sources", "data": []}
            yield {"type": "token", "data": faq.answer}
            yield {"type": "done", "data": {"intent": "faq", "cache": "mysql"}}
            return
        logger.info("STREAM: faq -> 未命中，回退到检索")
        sources = retrieve(query)
        stream = generate_stream(query, contexts=sources, intent="knowledge_qa", history=history, model_cfg=model_cfg)
    else:
        sources = retrieve(query)
        stream = generate_stream(query, contexts=sources, intent="knowledge_qa", history=history, model_cfg=model_cfg)

    yield {"type": "sources", "data": sources}

    async for token in stream:
        yield {"type": "token", "data": token}

    yield {"type": "done", "data": {"intent": intent}}
