"""
电商模拟数据 — 订单、物流、商品。
用于演示订单查询和物流追踪功能，生产环境替换为真实 API 调用。
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

# ── 模拟订单数据 ──────────────────────────────────────────────

MOCK_ORDERS = {
    "20240001": {
        "order_id": "20240001",
        "status": "已发货",
        "created_at": "2024-12-01 14:30:00",
        "paid_at": "2024-12-01 14:31:00",
        "shipped_at": "2024-12-02 09:00:00",
        "items": [
            {"name": "无线蓝牙耳机 Pro Max", "sku": "黑色/标准版", "qty": 1, "price": 299.00},
        ],
        "total": 299.00,
        "payment": "微信支付",
        "address": "北京市朝阳区xxx小区",
        "logistics_no": "SF1234567890",
    },
    "20240002": {
        "order_id": "20240002",
        "status": "待发货",
        "created_at": "2024-12-03 10:15:00",
        "paid_at": "2024-12-03 10:16:00",
        "shipped_at": None,
        "items": [
            {"name": "智能手表 S3", "sku": "银色/42mm", "qty": 1, "price": 899.00},
            {"name": "表带（硅胶）", "sku": "蓝色", "qty": 2, "price": 39.00},
        ],
        "total": 977.00,
        "payment": "支付宝",
        "address": "上海市浦东新区xxx路",
        "logistics_no": None,
    },
    "20240003": {
        "order_id": "20240003",
        "status": "已完成",
        "created_at": "2024-11-25 16:45:00",
        "paid_at": "2024-11-25 16:46:00",
        "shipped_at": "2024-11-26 08:30:00",
        "items": [
            {"name": "便携充电宝 20000mAh", "sku": "白色", "qty": 1, "price": 129.00},
        ],
        "total": 129.00,
        "payment": "银行卡",
        "address": "广州市天河区xxx大厦",
        "logistics_no": "ZT9876543210",
    },
}

# ── 模拟物流数据 ──────────────────────────────────────────────

MOCK_LOGISTICS = {
    "SF1234567890": {
        "logistics_no": "SF1234567890",
        "company": "顺丰速运",
        "status": "运输中",
        "tracks": [
            {"time": "2024-12-03 18:30:00", "location": "北京转运中心", "detail": "快件已到达北京转运中心"},
            {"time": "2024-12-03 06:00:00", "location": "上海转运中心", "detail": "快件已从上海转运中心发出"},
            {"time": "2024-12-02 20:00:00", "location": "上海分拣中心", "detail": "快件已到达上海分拣中心"},
            {"time": "2024-12-02 14:00:00", "location": "上海xxx营业点", "detail": "快递员已揽收"},
            {"time": "2024-12-02 09:00:00", "location": "系统", "detail": "商家已发货"},
        ],
        "eta": "2024-12-05",
    },
    "ZT9876543210": {
        "logistics_no": "ZT9876543210",
        "company": "中通快递",
        "status": "已签收",
        "tracks": [
            {"time": "2024-11-28 10:30:00", "location": "广州xxx小区", "detail": "快件已签收，签收人：本人"},
            {"time": "2024-11-28 08:00:00", "location": "广州xxx营业点", "detail": "快递员正在派送"},
            {"time": "2024-11-27 22:00:00", "location": "广州转运中心", "detail": "快件已到达广州转运中心"},
            {"time": "2024-11-26 14:00:00", "location": "上海转运中心", "detail": "快件已从上海转运中心发出"},
            {"time": "2024-11-26 08:30:00", "location": "系统", "detail": "商家已发货"},
        ],
        "eta": None,
    },
}

# ── 模拟商品数据 ──────────────────────────────────────────────

MOCK_PRODUCTS = [
    {"id": 1, "name": "无线蓝牙耳机 Pro Max", "category": "数码配件", "price": 299.00, "stock": 500,
     "desc": "主动降噪，蓝牙5.3，续航40小时，IPX5防水", "specs": "颜色: 黑/白/蓝 | 版本: 标准版/降噪版"},
    {"id": 2, "name": "智能手表 S3", "category": "智能穿戴", "price": 899.00, "stock": 200,
     "desc": "1.43寸AMOLED屏，血氧监测，GPS定位，NFC支付", "specs": "颜色: 银/黑 | 尺寸: 42mm/46mm"},
    {"id": 3, "name": "便携充电宝 20000mAh", "category": "数码配件", "price": 129.00, "stock": 1000,
     "desc": "20000mAh大容量，22.5W快充，可充手机4-5次", "specs": "颜色: 白/黑 | 容量: 10000mAh/20000mAh"},
    {"id": 4, "name": "机械键盘 K870T", "category": "电脑外设", "price": 399.00, "stock": 300,
     "desc": "87键布局，热插拔轴体，RGB背光，蓝牙+有线双模", "specs": "轴体: 红轴/青轴/茶轴 | 颜色: 黑/白"},
    {"id": 5, "name": "运动水杯 500ml", "category": "生活用品", "price": 49.00, "stock": 2000,
     "desc": "316不锈钢内胆，保温12小时，一键开盖", "specs": "颜色: 黑/白/粉/蓝 | 容量: 350ml/500ml"},
]


def query_order(order_id: str | None = None) -> str:
    """查询订单信息，返回格式化文本。"""
    if order_id and order_id in MOCK_ORDERS:
        o = MOCK_ORDERS[order_id]
        lines = [
            f"订单号：{o['order_id']}",
            f"状态：{o['status']}",
            f"下单时间：{o['created_at']}",
            f"支付方式：{o['payment']}",
            f"收货地址：{o['address']}",
            "商品明细：",
        ]
        for item in o["items"]:
            lines.append(f"  - {item['name']}（{item['sku']}）x{item['qty']}  ¥{item['price']:.2f}")
        lines.append(f"合计：¥{o['total']:.2f}")
        if o["logistics_no"]:
            lines.append(f"物流单号：{o['logistics_no']}")
        return "\n".join(lines)

    # 没有指定订单号或未找到，返回最近订单
    lines = ["您最近的订单：\n"]
    for o in MOCK_ORDERS.values():
        lines.append(f"订单 {o['order_id']}：{o['status']}，{o['items'][0]['name']}，¥{o['total']:.2f}")
    return "\n".join(lines)


def query_logistics(logistics_no: str | None = None) -> str:
    """查询物流信息，返回格式化文本。"""
    if logistics_no and logistics_no in MOCK_LOGISTICS:
        lg = MOCK_LOGISTICS[logistics_no]
        lines = [
            f"运单号：{lg['logistics_no']}",
            f"快递公司：{lg['company']}",
            f"状态：{lg['status']}",
        ]
        if lg["eta"]:
            lines.append(f"预计送达：{lg['eta']}")
        lines.append("\n物流轨迹：")
        for t in lg["tracks"]:
            lines.append(f"  [{t['time']}] {t['location']} — {t['detail']}")
        return "\n".join(lines)

    # 没有指定单号，返回所有在途物流
    lines = ["您的物流信息：\n"]
    for lg in MOCK_LOGISTICS.values():
        latest = lg["tracks"][0]
        lines.append(f"运单 {lg['logistics_no']}（{lg['company']}）：{lg['status']}，{latest['detail']}")
    return "\n".join(lines)


def search_products(keyword: str) -> list[dict]:
    """搜索商品。"""
    keyword = keyword.lower()
    return [p for p in MOCK_PRODUCTS if keyword in p["name"].lower() or keyword in p["category"].lower()]
