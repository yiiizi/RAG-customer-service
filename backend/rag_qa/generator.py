"""
LLM Generator: wraps OpenAI-compatible chat-completion API.

Supports:
- Non-streaming (standard)
- Streaming SSE (for WebSocket push)
- E-commerce customer service prompts
- Multi-turn conversation with history
"""

from __future__ import annotations

import json
import logging
from typing import AsyncIterator

import httpx

from config.settings import settings
from rag_qa.content_filter import filter_response

logger = logging.getLogger(__name__)

# ── E-commerce system prompts ─────────────────────────────────

_ECOMMERCE_BASE = (
    "你是一位专业、友善的电商智能客服助手。你的职责是帮助顾客解决购物相关问题。\n\n"
    "## 身份与语气\n"
    "- 称呼用户为「您」，语气亲切专业\n"
    "- 回答简洁明了，避免冗长\n"
    "- 遇到无法解决的问题，引导用户联系人工客服\n\n"
    "## 约束\n"
    "- 绝不编造商品信息、价格、库存、优惠活动\n"
    "- 绝不承诺未在资料中明确标注的服务\n"
    "- 不讨论与电商无关的话题，礼貌引导回购物问题\n"
    "- 涉及退款金额、订单修改等操作，建议用户联系人工客服确认\n"
)

_ECOMMERCE_KNOWLEDGE = (
    _ECOMMERCE_BASE +
    "\n## 回答规则\n"
    "- 严格基于以下参考资料回答，不要编造信息\n"
    "- 如果参考资料中没有相关内容，诚实告知并建议联系人工客服\n"
    "- 引用具体商品参数时，请准确列出\n"
    "- 涉及价格、库存以参考资料中的信息为准\n"
)

_ECOMMERCE_CHAT = (
    _ECOMMERCE_BASE +
    "\n## 范围\n"
    "- 可以回答简单的问候和寒暄\n"
    "- 可以介绍平台的基本功能（退换货政策、配送方式等）\n"
    "- 不回答与购物无关的问题，礼貌引导\n"
)

_ECOMMERCE_ORDER = (
    _ECOMMERCE_BASE +
    "\n## 订单查询\n"
    "- 根据以下订单信息回答用户问题\n"
    "- 清晰列出订单状态、商品、金额、时间等关键信息\n"
    "- 如果订单状态异常，给出建议操作\n"
)

_ECOMMERCE_LOGISTICS = (
    _ECOMMERCE_BASE +
    "\n## 物流查询\n"
    "- 根据以下物流信息回答用户问题\n"
    "- 清晰展示物流轨迹，最新状态放在最前面\n"
    "- 预计到达时间如有，需明确说明是预估\n"
)


def _build_knowledge_qa_prompt(query: str, context: str, history: list[dict] | None = None) -> list[dict]:
    """Build messages for the knowledge-QA path."""
    messages = [{"role": "system", "content": _ECOMMERCE_KNOWLEDGE + "\n\n## 参考资料\n" + context}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": query})
    return messages


def _build_chat_prompt(query: str, history: list[dict] | None = None) -> list[dict]:
    """Build messages for the chat (casual) path."""
    messages = [{"role": "system", "content": _ECOMMERCE_CHAT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": query})
    return messages


def _build_order_prompt(query: str, order_info: str, history: list[dict] | None = None) -> list[dict]:
    """Build messages for order query."""
    messages = [{"role": "system", "content": _ECOMMERCE_ORDER + "\n\n## 订单信息\n" + order_info}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": query})
    return messages


def _build_logistics_prompt(query: str, logistics_info: str, history: list[dict] | None = None) -> list[dict]:
    """Build messages for logistics query."""
    messages = [{"role": "system", "content": _ECOMMERCE_LOGISTICS + "\n\n## 物流信息\n" + logistics_info}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": query})
    return messages


async def generate(
    query: str,
    contexts: list[dict] | None = None,
    stream: bool = False,
    intent: str = "knowledge_qa",
    history: list[dict] | None = None,
    extra_info: str | None = None,
) -> str:
    """
    Generate an answer via LLM.

    Parameters
    ----------
    query : str
        The user question.
    contexts : list[dict] | None
        Retrieved knowledge passages.
    intent : str
        Used to select the prompt template.
    history : list[dict] | None
        Conversation history [{role, content}, ...].
    extra_info : str | None
        Extra context (order info, logistics info, etc.).

    Returns
    -------
    str
        The LLM reply text.
    """
    if intent == "order_query" and extra_info:
        messages = _build_order_prompt(query, extra_info, history)
    elif intent == "logistics_track" and extra_info:
        messages = _build_logistics_prompt(query, extra_info, history)
    elif contexts:
        joined = "\n\n---\n\n".join(ctx["text"] for ctx in contexts)
        messages = _build_knowledge_qa_prompt(query, joined, history)
    else:
        messages = _build_chat_prompt(query, history)

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            resp = await client.post(
                f"{settings.LLM_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "stream": False,
                },
            )

        if resp.status_code != 200:
            logger.error(f"LLM request failed ({resp.status_code}): {resp.text}")
            return "抱歉，系统暂时出现问题，请稍后再试或联系人工客服。"
    except Exception as e:
        logger.error(f"LLM request exception: {e}")
        return "抱歉，系统暂时出现问题，请稍后再试或联系人工客服。"

    return filter_response(resp.json()["choices"][0]["message"]["content"])


async def generate_stream(
    query: str,
    contexts: list[dict] | None = None,
    intent: str = "knowledge_qa",
    history: list[dict] | None = None,
    extra_info: str | None = None,
) -> AsyncIterator[str]:
    """
    Stream LLM tokens via SSE.
    """
    if intent == "order_query" and extra_info:
        messages = _build_order_prompt(query, extra_info, history)
    elif intent == "logistics_track" and extra_info:
        messages = _build_logistics_prompt(query, extra_info, history)
    elif contexts:
        joined = "\n\n---\n\n".join(ctx["text"] for ctx in contexts)
        messages = _build_knowledge_qa_prompt(query, joined, history)
    else:
        messages = _build_chat_prompt(query, history)

    try:
        async with httpx.AsyncClient(timeout=settings.LLM_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{settings.LLM_API_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL,
                    "messages": messages,
                    "temperature": settings.LLM_TEMPERATURE,
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "stream": True,
                },
            ) as resp:
                if resp.status_code != 200:
                    logger.error(f"LLM stream failed ({resp.status_code})")
                    yield "抱歉，系统暂时出现问题，请稍后再试。"
                    return

                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data)
                            delta = chunk["choices"][0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue
    except Exception as e:
        logger.error(f"LLM stream exception: {e}")
        yield "抱歉，系统暂时出现问题，请稍后再试或联系人工客服。"
