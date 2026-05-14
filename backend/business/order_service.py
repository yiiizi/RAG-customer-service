from __future__ import annotations

import copy
import re
from typing import Any

from backend.rag_qa.ecommerce_mock import MOCK_ORDERS

ORDER_ID_RE = re.compile(r"\b(\d{8,16})\b")

FOLLOWUP_WORDS = (
    "这个", "那个", "它", "商品", "产品", "单个", "其中", "第一", "第二", "第三",
    "手机", "手表", "耳机", "充电宝", "移动电源", "键盘", "保温杯", "什么时候到",
    "多久到", "发货", "到哪", "到哪里",
)


def extract_order_id(query: str) -> str | None:
    match = ORDER_ID_RE.search(query)
    return match.group(1) if match else None


def _clone_user_orders(user_id: int) -> dict[str, dict[str, Any]]:
    templates = list(MOCK_ORDERS.values())
    orders: dict[str, dict[str, Any]] = {}
    offset = user_id % len(templates) if templates else 0
    for idx, template in enumerate(templates):
        source = templates[(offset + idx) % len(templates)]
        order = copy.deepcopy(source)
        order_id = f"{user_id:04d}{idx + 1:04d}"
        order["order_id"] = order_id
        order["address"] = f"用户{user_id}专属收货地址 {idx + 1} 号"
        logistics_no = order.get("logistics_no")
        if logistics_no:
            prefix = "".join(ch for ch in str(logistics_no) if ch.isalpha()) or "MO"
            order["logistics_no"] = f"{prefix}{user_id:04d}{idx + 1:06d}"
        orders[order_id] = order
    return orders


def list_user_orders(user_id: int) -> list[dict[str, Any]]:
    return list(_clone_user_orders(user_id).values())


def get_user_order(user_id: int, order_id: str) -> dict[str, Any] | None:
    return _clone_user_orders(user_id).get(order_id)


def format_order_detail(order: dict[str, Any]) -> str:
    lines = [
        f"订单号：{order['order_id']}",
        f"状态：{order['status']}",
        f"下单时间：{order['created_at']}",
        f"支付方式：{order['payment']}",
        f"收货地址：{order['address']}",
        "商品明细：",
    ]
    for index, item in enumerate(order.get("items", []), start=1):
        lines.append(
            f"  {index}. {item['name']} | SKU：{item['sku']} | 数量：{item['qty']} | 单价：¥{item['price']:.2f}"
        )
    lines.append(f"合计：¥{order['total']:.2f}")
    if order.get("logistics_no"):
        lines.append(f"物流单号：{order['logistics_no']}")
    return "\n".join(lines)


def format_recent_orders(user_id: int) -> str:
    lines = ["请提供订单号，我可以继续帮你查询。", "", "你最近的订单："]
    for order in list_user_orders(user_id):
        first_item = (order.get("items") or [{}])[0]
        lines.append(
            f"- {order['order_id']} | {order['status']} | {first_item.get('name', '商品')} | ¥{order['total']:.2f}"
        )
    return "\n".join(lines)


def _history_text(history: list[dict[str, Any]] | None) -> str:
    if not history:
        return ""
    return "\n".join(str(item.get("content") or "") for item in history[-8:])


def extract_recent_order_id(history: list[dict[str, Any]] | None) -> str | None:
    text = _history_text(history)
    matches = ORDER_ID_RE.findall(text)
    return matches[-1] if matches else None


def is_order_followup(query: str, history: list[dict[str, Any]] | None) -> bool:
    if extract_order_id(query):
        return False
    if not extract_recent_order_id(history):
        return False
    return any(word in query for word in FOLLOWUP_WORDS)


def _index_from_query(query: str) -> int | None:
    mapping = {
        "第一": 0,
        "第1": 0,
        "第二": 1,
        "第2": 1,
        "第三": 2,
        "第3": 2,
    }
    for key, index in mapping.items():
        if key in query:
            return index
    return None


def _item_matches_query(item: dict[str, Any], query: str) -> bool:
    haystack = f"{item.get('name', '')} {item.get('sku', '')}".lower()
    query_lower = query.lower()
    if any(token and token in haystack for token in re.findall(r"[\w\u4e00-\u9fff]+", query_lower)):
        return True
    alias_groups = {
        "手机": ("手机", "phone", "pro", "max"),
        "手表": ("手表", "watch", "s3"),
        "耳机": ("耳机", "蓝牙"),
        "充电宝": ("充电宝", "移动电源", "mah"),
        "移动电源": ("充电宝", "移动电源", "mah"),
        "键盘": ("键盘", "k870"),
        "保温杯": ("保温杯", "500ml"),
    }
    for query_key, aliases in alias_groups.items():
        if query_key in query_lower and any(alias.lower() in haystack for alias in aliases):
            return True
    return False


def _format_single_item(order: dict[str, Any], item: dict[str, Any]) -> str:
    lines = [
        f"订单号：{order['order_id']}",
        f"商品：{item['name']}",
        f"SKU：{item['sku']}",
        f"数量：{item['qty']}",
        f"单价：¥{item['price']:.2f}",
        f"订单状态：{order['status']}",
    ]
    if order.get("logistics_no"):
        lines.append(f"物流单号：{order['logistics_no']}")
    if order.get("shipped_at"):
        lines.append(f"发货时间：{order['shipped_at']}")
    else:
        lines.append("当前还没有发货时间，建议关注订单状态或联系人工客服确认。")
    return "\n".join(lines)


def resolve_order_followup(user_id: int | None, query: str, history: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not user_id or not is_order_followup(query, history):
        return None

    order_id = extract_recent_order_id(history)
    if not order_id:
        return None

    order = get_user_order(user_id, order_id)
    if not order:
        return None

    items = order.get("items") or []
    if not items:
        return {
            "resolved": True,
            "text": f"订单 {order_id} 没有找到商品明细，请联系人工客服进一步核实。",
            "order_id": order_id,
        }

    index = _index_from_query(query)
    if index is not None and 0 <= index < len(items):
        return {
            "resolved": True,
            "text": _format_single_item(order, items[index]),
            "order_id": order_id,
            "item": items[index],
        }

    matches = [item for item in items if _item_matches_query(item, query)]
    if len(matches) == 1:
        return {
            "resolved": True,
            "text": _format_single_item(order, matches[0]),
            "order_id": order_id,
            "item": matches[0],
        }
    if len(items) == 1 and any(word in query for word in ("这个", "那个", "它", "商品", "产品")):
        return {
            "resolved": True,
            "text": _format_single_item(order, items[0]),
            "order_id": order_id,
            "item": items[0],
        }

    names = "、".join(item.get("name", "商品") for item in items)
    return {
        "resolved": False,
        "needs_more_info": True,
        "text": f"订单 {order_id} 里有多个商品：{names}。请告诉我你想查询哪一个商品，我再单独说明。",
        "order_id": order_id,
    }


class OrderService:
    async def resolve(self, user_id: int | None, query: str) -> dict[str, Any]:
        if not user_id:
            return {
                "resolved": False,
                "needs_more_info": True,
                "text": "请先登录后再查询订单信息。",
            }

        order_id = extract_order_id(query)
        if not order_id:
            return {
                "resolved": False,
                "needs_more_info": True,
                "text": format_recent_orders(user_id),
            }

        order = get_user_order(user_id, order_id)
        if not order:
            return {
                "resolved": False,
                "needs_more_info": True,
                "text": f"未找到订单号 {order_id}。请确认订单号是否正确，或从最近订单中选择一个继续查询。\n\n{format_recent_orders(user_id)}",
            }

        return {
            "resolved": True,
            "needs_more_info": False,
            "text": format_order_detail(order),
            "order_id": order_id,
            "order": order,
        }


order_service = OrderService()
