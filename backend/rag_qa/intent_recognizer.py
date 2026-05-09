"""
Intent Recognizer: classify user query into e-commerce intents.

Intents
-------
- chat            Casual conversation → route directly to LLM
- faq             High-frequency Q&A  → check Redis/MySQL cache first
- knowledge_qa    Product/domain knowledge → full hybrid retrieval + generation
- order_query     Order status query → fetch order data + LLM
- logistics_track Logistics tracking → fetch logistics data + LLM

Strategy: lightweight keyword-rule matching first (fast, no model cost),
then fall back to LLM classification for ambiguous cases.
"""

from __future__ import annotations

import logging
import re
from typing import Literal

import httpx

from config.settings import settings

logger = logging.getLogger(__name__)

Intent = Literal["chat", "faq", "knowledge_qa", "order_query", "logistics_track"]

# ── Keyword-rule patterns ──────────────────────────────────────────

# Greetings / small talk → chat
_CHAT_PATTERNS: list[re.Pattern] = [
    re.compile(r"^(你好|您好|hi|hello|嗨|早上好|晚上好|下午好)[!！。.]*$"),
    re.compile(r"^(谢谢|感谢|多谢|thanks|thank you)[!！。.]*$"),
    re.compile(r"^(再见|拜拜|bye|goodbye|88)[!！。.]*$"),
    re.compile(r"^(你是谁|你是|你的名字|what are you|who are you)"),
    re.compile(r"^(天气|今天|昨天|明天).{0,10}$"),
    re.compile(r"^(讲个笑话|笑话|好玩|有趣)"),
]

# Order query patterns → order_query (must include order-related keywords)
_ORDER_PATTERNS: list[re.Pattern] = [
    re.compile(r"(我的|查|看看|查询).{0,5}(订单|单号|下单)"),
    re.compile(r"(订单|单号).{0,10}(状态|进度|情况|在哪|什么)"),
    re.compile(r"(买了|购买了|下单了).{0,10}(什么|哪些|东西)"),
    re.compile(r"(订单|单号).{0,5}(发货|没发|什么时候发|还没收到)"),
    re.compile(r"(付款|支付|退款|到账).{0,5}(状态|进度|到了吗|什么时候)"),
]

# Logistics tracking patterns → logistics_track (must include logistics keywords)
_LOGISTICS_PATTERNS: list[re.Pattern] = [
    re.compile(r"(物流|快递|运单|包裹|配送).{0,10}(到哪|在哪|进度|状态|轨迹)"),
    re.compile(r"(物流|快递|包裹).{0,5}(到哪了|到哪里了|什么时候到|多久到|预计.*到)"),
    re.compile(r"(签收|已签|本人签|代收)"),
    re.compile(r"(快递|物流).{0,5}(单号|查询|跟踪)"),
]

# FAQ-like short factual questions → faq
_FAQ_PATTERNS: list[re.Pattern] = [
    re.compile(r"(退换货|退货|换货|退款).{0,10}(政策|流程|条件|规则|怎么|如何)"),
    re.compile(r"(优惠|折扣|促销|活动|满减|券|红包)"),
    re.compile(r"(运费|邮费|包邮|配送费)"),
    re.compile(r"(发票|开票|电子发票)"),
    re.compile(r"(保修|售后|维修|质保)"),
    re.compile(r"(会员|积分|等级|VIP)"),
    re.compile(r"(支付|付款).{0,5}(方式|方法)"),
    re.compile(r"(营业时间|客服电话|联系方式|人工客服)"),
]


def _rule_match(text: str) -> tuple[Intent | None, float]:
    """Return (intent, confidence) from keyword rules, or (None, 0)."""
    text_stripped = text.strip().lower()

    for pat in _CHAT_PATTERNS:
        if pat.search(text_stripped):
            return "chat", 0.9

    for pat in _ORDER_PATTERNS:
        if pat.search(text_stripped):
            return "order_query", 0.85

    for pat in _LOGISTICS_PATTERNS:
        if pat.search(text_stripped):
            return "logistics_track", 0.85

    for pat in _FAQ_PATTERNS:
        if pat.search(text_stripped):
            return "faq", 0.8

    return None, 0.0


# ── LLM fallback prompt ────────────────────────────────────────────

_INTENT_PROMPT = """你是电商客服意图分类器。将用户问题分类为以下意图之一：

- **chat**: 闲聊、问候、与购物无关的话题
- **faq**: 高频标准问题（退换货政策、优惠活动、运费、发票、会员等）
- **knowledge_qa**: 商品详情、规格参数、使用说明等需要查询知识库的问题
- **order_query**: 查询订单状态、发货情况、支付状态
- **logistics_track**: 查询物流进度、快递到哪了、预计到达时间

只回复一个单词：chat, faq, knowledge_qa, order_query, logistics_track

用户问题: {query}
意图:"""


async def _llm_classify(query: str) -> Intent:
    """Use a lightweight LLM call to classify intent."""
    prompt = _INTENT_PROMPT.format(query=query)

    async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
        resp = await client.post(
            f"{settings.LLM_API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.INTENT_LLM_MODEL or settings.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "你是意图分类器，只回复一个单词。"},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.0,
                "max_tokens": 20,
            },
        )

    if resp.status_code != 200:
        logger.warning(f"LLM intent classify failed ({resp.status_code}), defaulting to knowledge_qa")
        return "knowledge_qa"

    text = resp.json()["choices"][0]["message"]["content"].strip().lower()
    for intent in ("order_query", "logistics_track", "knowledge_qa", "faq", "chat"):
        if intent in text:
            return intent  # type: ignore[return-value]

    return "knowledge_qa"


async def recognize(query: str) -> tuple[Intent, float]:
    """
    Classify the user query.

    Returns
    -------
    (intent, confidence) — confidence in [0, 1].
    """
    # 1. Rule-based fast path
    intent, conf = _rule_match(query)
    if intent and conf >= settings.INTENT_RULE_THRESHOLD:
        logger.info(f"Intent (rule): {intent} (conf={conf:.2f})")
        return intent, conf

    # 2. LLM fallback
    logger.info("Intent: rule match low confidence, falling back to LLM")
    intent = await _llm_classify(query)
    logger.info(f"Intent (LLM): {intent}")
    return intent, 0.7
