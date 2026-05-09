"""
Async Redis cache layer for FAQ pairs and BM25 results.

TTL strategy
------------
- Normal FAQ:  24 h  (config: REDIS_FAQ_TTL)
- Hot FAQ:      7 d  (config: REDIS_FAQ_HOT_TTL) — triggered when frequency > HOT_THRESHOLD
- BM25 cache:   1 h  (config: REDIS_BM25_TTL)

All writes are write-through: MySQL update → Redis set.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

import redis.asyncio as aioredis

from config.settings import settings

logger = logging.getLogger(__name__)

# ── Connection pool ─────────────────────────────────────────────────
_redis_available = True

try:
    pool = aioredis.ConnectionPool.from_url(
        settings.REDIS_URL,
        max_connections=settings.REDIS_POOL_SIZE,
    )
    redis_client = aioredis.Redis(connection_pool=pool)
except Exception as e:
    logger.warning(f"Redis connection pool creation failed: {e}")
    _redis_available = False
    redis_client = None


def _faq_key(question: str) -> str:
    digest = hashlib.md5(question.encode("utf-8")).hexdigest()
    return f"faq:{digest}"


def _bm25_key(query: str) -> str:
    digest = hashlib.md5(query.encode("utf-8")).hexdigest()
    return f"bm25:{digest}"


# ── FAQ Cache ───────────────────────────────────────────────────────

async def faq_cache_get(question: str) -> Optional[dict]:
    """Retrieve a cached FAQ pair. Returns decoded dict or None."""
    if not _redis_available or redis_client is None:
        return None
    try:
        raw = await redis_client.get(_faq_key(question))
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis FAQ get failed: {e}")
    return None


async def faq_cache_set(question: str, answer: str, frequency: int = 0) -> None:
    """Write FAQ pair to Redis with dynamic TTL."""
    if not _redis_available or redis_client is None:
        return
    try:
        key = _faq_key(question)
        payload = json.dumps({"question": question, "answer": answer, "frequency": frequency})
        ttl = (
            settings.REDIS_FAQ_HOT_TTL
            if frequency > settings.REDIS_FAQ_HOT_THRESHOLD
            else settings.REDIS_FAQ_TTL
        )
        await redis_client.setex(key, ttl, payload)
    except Exception as e:
        logger.warning(f"Redis FAQ set failed: {e}")


async def faq_cache_delete(question: str) -> None:
    if not _redis_available or redis_client is None:
        return
    try:
        await redis_client.delete(_faq_key(question))
    except Exception as e:
        logger.warning(f"Redis FAQ delete failed: {e}")


async def faq_cache_clear() -> None:
    """Flush all FAQ-prefixed keys. Use with caution."""
    if not _redis_available or redis_client is None:
        return
    try:
        keys = []
        async for key in redis_client.scan_iter(match="faq:*"):
            keys.append(key)
        if keys:
            await redis_client.delete(*keys)
    except Exception as e:
        logger.warning(f"Redis FAQ clear failed: {e}")


# ── BM25 Cache ──────────────────────────────────────────────────────

async def bm25_cache_get(query: str) -> Optional[list[dict]]:
    if not _redis_available or redis_client is None:
        return None
    try:
        raw = await redis_client.get(_bm25_key(query))
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(f"Redis BM25 get failed: {e}")
    return None


async def bm25_cache_set(query: str, results: list[dict]) -> None:
    if not _redis_available or redis_client is None:
        return
    try:
        key = _bm25_key(query)
        await redis_client.setex(key, settings.REDIS_BM25_TTL, json.dumps(results))
    except Exception as e:
        logger.warning(f"Redis BM25 set failed: {e}")
