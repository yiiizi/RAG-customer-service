from __future__ import annotations

import re
from datetime import datetime
from typing import Any

EXPLICIT_HANDOFF_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"转人工",
        r"转接人工",
        r"我要人工",
        r"帮我转人工",
        r"人工处理",
        r"客服介入",
        r"投诉",
    )
]

HIGH_RISK_RULES: list[tuple[str, str, str]] = [
    (r"退款|退钱|退款金额", "refund", "high"),
    (r"取消订单|取消这单", "cancel_order", "high"),
    (r"改地址|修改地址|更换地址", "address_change", "high"),
    (r"账号异常|账号安全|盗号|封号", "account_security", "high"),
]


def build_ticket_no(now: datetime | None = None) -> str:
    current = now or datetime.utcnow()
    return f"TK{current.strftime('%Y%m%d%H%M%S%f')[:-3]}"


def build_ticket_notice(ticket_no: str) -> str:
    return f"\n\n已为您创建工单：{ticket_no}。您可以在“工单”页面查看处理进度。"


def _clean_summary(query: str, max_len: int = 80) -> str:
    summary = " ".join(query.strip().split())
    if len(summary) > max_len:
        summary = summary[:max_len].rstrip() + "..."
    return summary or "客服工单"


def evaluate_handoff(query: str, intent: str | None = None, answer: str | None = None) -> dict[str, Any] | None:
    normalized = query.strip()
    for pattern in EXPLICIT_HANDOFF_PATTERNS:
        if pattern.search(normalized):
            return {
                "category": "manual_handoff",
                "priority": "medium",
                "reason": "user_requested",
                "summary": _clean_summary(query),
            }

    for pattern, category, priority in HIGH_RISK_RULES:
        if re.search(pattern, normalized, re.IGNORECASE):
            return {
                "category": category,
                "priority": priority,
                "reason": "high_risk",
                "summary": _clean_summary(query),
            }

    if intent == "error":
        return {
            "category": "system_error",
            "priority": "high",
            "reason": "system_error",
            "summary": _clean_summary(query),
        }

    if answer and "联系人工客服" in answer and re.search(r"退款|取消|改地址|投诉|账号", normalized):
        return {
            "category": "manual_handoff",
            "priority": "high",
            "reason": "assistant_suggested",
            "summary": _clean_summary(query),
        }

    return None
