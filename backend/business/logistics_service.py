from __future__ import annotations

import copy
import re
from typing import Any

from backend.business.order_service import (
    extract_order_id,
    list_user_orders,
)
from backend.rag_qa.ecommerce_mock import MOCK_LOGISTICS

TRACKING_NO_RE = re.compile(r"\b([A-Z]{2}\d{8,16})\b", re.IGNORECASE)


def extract_tracking_no(query: str) -> str | None:
    match = TRACKING_NO_RE.search(query)
    return match.group(1).upper() if match else None


def _clone_user_logistics(user_id: int) -> dict[str, dict[str, Any]]:
    templates = list(MOCK_LOGISTICS.values())
    logistics: dict[str, dict[str, Any]] = {}
    shipped_orders = [order for order in list_user_orders(user_id) if order.get("logistics_no")]
    for idx, order in enumerate(shipped_orders):
        template = templates[idx % len(templates)]
        item = copy.deepcopy(template)
        logistics_no = str(order["logistics_no"])
        item["logistics_no"] = logistics_no
        item["order_id"] = order["order_id"]
        logistics[logistics_no] = item
    return logistics


def get_user_logistics_by_no(user_id: int, logistics_no: str) -> dict[str, Any] | None:
    return _clone_user_logistics(user_id).get(logistics_no.upper())


def get_user_logistics_by_order(user_id: int, order_id: str) -> dict[str, Any] | None:
    for item in _clone_user_logistics(user_id).values():
        if item.get("order_id") == order_id:
            return item
    return None


def format_logistics_detail(item: dict[str, Any]) -> str:
    lines = [
        f"订单号：{item.get('order_id', '-')}",
        f"运单号：{item['logistics_no']}",
        f"快递公司：{item['company']}",
        f"状态：{item['status']}",
    ]
    if item.get("eta"):
        lines.append(f"预计送达：{item['eta']}")
    lines.append("")
    lines.append("物流轨迹：")
    for track in item.get("tracks", []):
        lines.append(f"- [{track['time']}] {track['location']}：{track['detail']}")
    return "\n".join(lines)


def format_recent_logistics(user_id: int) -> str:
    lines = ["请提供订单号或物流单号，我可以继续帮您查询。", "", "您最近可查询的物流："]
    shipped_orders = [order for order in list_user_orders(user_id) if order.get("logistics_no")]
    if not shipped_orders:
        return "您当前没有可查询的物流订单。"
    for order in shipped_orders:
        lines.append(
            f"- 订单 {order['order_id']} | 运单 {order['logistics_no']} | {order['status']}"
        )
    return "\n".join(lines)


class LogisticsService:
    async def resolve(self, user_id: int | None, query: str) -> dict[str, Any]:
        if not user_id:
            return {
                "resolved": False,
                "needs_more_info": True,
                "text": "请先登录后再查询物流信息。",
            }

        tracking_no = extract_tracking_no(query)
        order_id = extract_order_id(query)

        item = None
        if tracking_no:
            item = get_user_logistics_by_no(user_id, tracking_no)
        elif order_id:
            item = get_user_logistics_by_order(user_id, order_id)
        else:
            return {
                "resolved": False,
                "needs_more_info": True,
                "text": format_recent_logistics(user_id),
            }

        if not item:
            return {
                "resolved": False,
                "needs_more_info": True,
                "text": "没有找到对应的物流信息。请确认订单号或物流单号是否正确。\n\n"
                + format_recent_logistics(user_id),
            }

        return {
            "resolved": True,
            "needs_more_info": False,
            "text": format_logistics_detail(item),
            "logistics_no": item["logistics_no"],
            "logistics": item,
        }


logistics_service = LogisticsService()
