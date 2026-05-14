from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any


PRODUCT_ID_RE = re.compile(r"\b(P\d{4}|SKU\d{4}-\d{2}|SPU\d{4})\b", re.IGNORECASE)

PRODUCT_FOLLOWUP_WORDS = (
    "它", "这个", "这款", "该商品", "该产品", "多少钱", "价格", "库存", "有货", "现货",
    "参数", "规格", "配置", "颜色", "版本", "内存", "续航", "功率", "容量", "尺寸",
    "保修", "质保", "售后", "维修", "换新", "退货", "无理由", "能退", "发货", "配送",
    "优惠", "活动", "划算", "推荐", "适合", "区别", "对比",
)

PRODUCT_QUERY_WORDS = (
    "商品", "产品", "介绍", "了解", "咨询", "推荐", "价格", "库存", "参数", "规格",
    "保修", "售后", "退货", "发货", "配送", "多少钱", "有货", "能退", "适合",
)


def _catalog_path() -> Path:
    return Path(__file__).resolve().parents[2] / "datasets" / "product_import" / "product_import.json"


@lru_cache(maxsize=1)
def _load_products() -> list[dict[str, Any]]:
    path = _catalog_path()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        payload = json.load(f)
    items = payload.get("items", [])
    return [item for item in items if isinstance(item, dict)]


def _normalize(text: str | None) -> str:
    return (text or "").strip().lower()


def _tokens(text: str) -> list[str]:
    return [token.lower() for token in re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]+", text)]


def _product_text(product: dict[str, Any]) -> str:
    specs = product.get("specs") or {}
    spec_text = " ".join(f"{k} {v}" for k, v in specs.items())
    parts = [
        product.get("product_id"),
        product.get("spu_id"),
        product.get("sku_id"),
        product.get("name"),
        product.get("category"),
        product.get("brand"),
        product.get("model"),
        " ".join(product.get("tags") or []),
        " ".join(product.get("selling_points") or []),
        spec_text,
    ]
    return _normalize(" ".join(str(part) for part in parts if part))


def _format_specs(product: dict[str, Any]) -> str:
    specs = product.get("specs") or {}
    if not specs:
        return "暂无详细规格参数"
    return "；".join(f"{key}：{value}" for key, value in specs.items())


def _format_source(product: dict[str, Any]) -> dict[str, Any]:
    text = (
        f"{product.get('name')}（{product.get('model')}）\n"
        f"价格：¥{product.get('price')}，库存：{product.get('stock')}。\n"
        f"规格：{_format_specs(product)}\n"
        f"保修：{product.get('warranty')}\n"
        f"退换货：{product.get('return_policy')}\n"
        f"配送：{product.get('shipping_policy')}\n"
        f"售后：{product.get('after_sales')}"
    )
    return {
        "text": text,
        "source": f"商品数据/{product.get('sku_id')}",
        "score": 1.0,
        "parent_id": product.get("spu_id") or "",
        "chunk_index": 0,
    }


def _match_by_code(query: str) -> list[dict[str, Any]]:
    codes = {m.group(1).upper() for m in PRODUCT_ID_RE.finditer(query)}
    if not codes:
        return []
    matches = []
    for product in _load_products():
        if {
            str(product.get("product_id", "")).upper(),
            str(product.get("spu_id", "")).upper(),
            str(product.get("sku_id", "")).upper(),
        } & codes:
            matches.append(product)
    return matches


def _match_by_text(query: str) -> list[dict[str, Any]]:
    q = _normalize(query)
    products = _load_products()
    if not q or not products:
        return []

    exact_matches = []
    for product in products:
        name = _normalize(product.get("name"))
        model = _normalize(product.get("model"))
        if (name and name in q) or (model and model in q):
            exact_matches.append(product)
    if exact_matches:
        return exact_matches

    query_tokens = [t for t in _tokens(q) if len(t) >= 2]
    scored: list[tuple[int, dict[str, Any]]] = []
    for product in products:
        haystack = _product_text(product)
        score = sum(1 for token in query_tokens if token in haystack)
        if score > 0:
            scored.append((score, product))
    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored:
        return []
    best = scored[0][0]
    return [product for score, product in scored if score == best and score >= 1][:3]


def _recent_product_from_history(history: list[dict[str, Any]] | None) -> dict[str, Any] | None:
    if not history:
        return None
    text = "\n".join(str(item.get("content") or "") for item in history[-8:])
    matches = _match_by_code(text)
    if matches:
        return matches[-1]
    text_matches = _match_by_text(text)
    return text_matches[-1] if text_matches else None


def _is_product_query(query: str, matches: list[dict[str, Any]]) -> bool:
    if matches:
        return True
    return any(word in query for word in PRODUCT_QUERY_WORDS)


def _format_compare(products: list[dict[str, Any]]) -> str:
    rows = []
    for product in products[:3]:
        rows.append(
            f"- {product.get('name')}（{product.get('model')}，商品ID：{product.get('product_id')}）："
            f"¥{product.get('price')}，库存 {product.get('stock')}，规格：{_format_specs(product)}"
        )
    return "这几款商品的主要区别如下：\n" + "\n".join(rows) + "\n\n如果你更关注价格、配置、售后或使用场景，可以继续追问其中一款。"


def _format_answer(product: dict[str, Any], query: str, is_followup: bool = False) -> str:
    q = query.lower()
    name = product.get("name")
    model = product.get("model")
    product_id = product.get("product_id")

    if any(word in q for word in ("介绍", "了解", "咨询", "推荐")):
        selling_points = "、".join(product.get("selling_points") or [])
        tags = "、".join(product.get("tags") or [])
        prefix = "这款商品" if is_followup else f"{name}"
        return (
            f"{prefix}是 {product.get('brand')} 的 {product.get('category')} 商品，型号为 {model}，商品ID：{product_id}。\n"
            f"- 价格库存：当前售价 ¥{product.get('price')}，原价 ¥{product.get('original_price')}，库存 {product.get('stock')} 件。\n"
            f"- 核心卖点：{selling_points}。\n"
            f"- 规格参数：{_format_specs(product)}。\n"
            f"- 标签：{tags}。\n"
            f"- 配送：{product.get('shipping_policy')}。\n"
            f"- 退换货：{product.get('return_policy')}。\n"
            f"- 售后：{product.get('after_sales')}。\n"
            f"你可以继续问它的价格、库存、保修、退货、发货或具体参数。"
        )

    if any(word in q for word in ("价格", "多少钱", "优惠", "活动", "划算")):
        return (
            f"{name}（{model}，商品ID：{product_id}）当前售价 ¥{product.get('price')}，"
            f"原价 ¥{product.get('original_price')}，库存 {product.get('stock')} 件。"
        )
    if any(word in q for word in ("库存", "有货", "现货")):
        return f"{name}（商品ID：{product_id}）当前库存 {product.get('stock')} 件，状态为 {product.get('status')}。"
    if any(word in q for word in ("参数", "规格", "配置", "颜色", "版本", "内存", "续航", "功率", "容量", "尺寸")):
        return f"{name}（{model}，商品ID：{product_id}）的规格参数是：{_format_specs(product)}。"
    if any(word in q for word in ("保修", "质保", "维修")):
        return f"{name}（商品ID：{product_id}）的保修政策：{product.get('warranty')}。售后处理：{product.get('after_sales')}。"
    if any(word in q for word in ("退货", "无理由", "能退", "退款", "换货")):
        return f"{name}（商品ID：{product_id}）的退换货政策：{product.get('return_policy')}。"
    if any(word in q for word in ("发货", "配送", "物流", "多久到")):
        return f"{name}（商品ID：{product_id}）的配送说明：{product.get('shipping_policy')}。"
    if any(word in q for word in ("售后", "坏了", "质量问题", "换新")):
        return f"{name}（商品ID：{product_id}）的售后规则：{product.get('after_sales')}；保修政策：{product.get('warranty')}。"

    selling_points = "、".join(product.get("selling_points") or [])
    tags = "、".join(product.get("tags") or [])
    prefix = "这款商品" if is_followup else f"{name}"
    return (
        f"{prefix}是 {product.get('brand')} 的 {product.get('category')} 商品，型号为 {model}，商品ID：{product_id}。\n"
        f"- 价格库存：当前售价 ¥{product.get('price')}，原价 ¥{product.get('original_price')}，库存 {product.get('stock')} 件。\n"
        f"- 核心卖点：{selling_points}。\n"
        f"- 规格参数：{_format_specs(product)}。\n"
        f"- 标签：{tags}。\n"
        f"- 退换货：{product.get('return_policy')}。\n"
        f"- 售后：{product.get('after_sales')}。\n"
        f"你可以继续问它的价格、库存、保修、退货、发货或具体参数。"
    )


def resolve_product_question(query: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    direct_matches = _match_by_code(query) or _match_by_text(query)
    is_followup = False

    if not direct_matches and any(word in query for word in PRODUCT_FOLLOWUP_WORDS):
        recent = _recent_product_from_history(history)
        if recent:
            direct_matches = [recent]
            is_followup = True

    if not _is_product_query(query, direct_matches):
        return None
    if not direct_matches:
        return None

    if len(direct_matches) > 1 and any(word in query for word in ("区别", "对比", "哪个", "哪款")):
        sources = [_format_source(product) for product in direct_matches]
        return {
            "resolved": True,
            "answer": _format_compare(direct_matches),
            "sources": sources,
            "product_id": direct_matches[0].get("product_id"),
            "is_followup": is_followup,
        }

    product = direct_matches[0]
    return {
        "resolved": True,
        "answer": _format_answer(product, query, is_followup=is_followup),
        "sources": [_format_source(product)],
        "product_id": product.get("product_id"),
        "is_followup": is_followup,
    }


class ProductService:
    def list_recommended(self, limit: int = 5) -> list[dict[str, Any]]:
        products = sorted(
            _load_products(),
            key=lambda item: {"A": 0, "B": 1, "C": 2}.get(str(item.get("recommend_level")), 9),
        )
        return products[:limit]

    def resolve(self, query: str, history: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
        return resolve_product_question(query, history)


product_service = ProductService()
