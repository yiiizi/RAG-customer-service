"""
内容过滤模块 — 敏感词过滤 + 合规检查。

功能：
1. 广告法违禁词检测（最、第一、国家级等）
2. 用户输入安全过滤（注入攻击防护）
3. 回答内容合规检查
"""

from __future__ import annotations

import re
import logging

logger = logging.getLogger(__name__)

# ── 广告法违禁词 ──────────────────────────────────────────────

AD_BANNED_WORDS = [
    "最", "最佳", "最好", "最优", "最大", "最小", "最高", "最低",
    "第一", "唯一", "首个", "首选", "顶级", "极致", "绝对",
    "国家级", "世界级", "全球领先", "行业领先", "遥遥领先",
    "100%", "纯天然", "零添加", "无副作用", "包治", "根治",
    "祖传秘方", "特供", "专供", "驰名商标",
]

# 编译正则（中文需要直接匹配，不用 \b）
_AD_PATTERNS = [re.compile(re.escape(w)) for w in AD_BANNED_WORDS]

# ── 注入攻击模式 ──────────────────────────────────────────────

_INJECTION_PATTERNS = [
    re.compile(r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous|above|prior)\s+(instructions?|prompts?)", re.IGNORECASE),
    re.compile(r"(?i)you\s+are\s+now\s+", re.IGNORECASE),
    re.compile(r"(?i)system\s*:\s*", re.IGNORECASE),
    re.compile(r"(?i)ignore\s+everything\s+above", re.IGNORECASE),
    re.compile(r"忽略(之前|上面|以上)(的)?(指令|提示|规则)"),
    re.compile(r"你现在是"),
    re.compile(r"忘记(你的|你)(身份|角色|设定)"),
]


def check_ad_compliance(text: str) -> list[str]:
    """
    检测广告法违禁词。

    Returns
    -------
    list[str]
        命中的违禁词列表，空列表表示合规。
    """
    found = []
    for word, pat in zip(AD_BANNED_WORDS, _AD_PATTERNS):
        if pat.search(text):
            found.append(word)
    return found


def check_injection(text: str) -> bool:
    """
    检测提示词注入攻击。

    Returns
    -------
    bool
        True 表示检测到注入风险。
    """
    for pat in _INJECTION_PATTERNS:
        if pat.search(text):
            logger.warning(f"Injection detected: {text[:80]}")
            return True
    return False


def sanitize_input(text: str) -> str:
    """
    清理用户输入，移除潜在危险内容。
    """
    # 移除零宽字符
    text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
    # 限制长度
    if len(text) > 4096:
        text = text[:4096]
    return text.strip()


def filter_response(text: str) -> str:
    """
    过滤 LLM 回答中的违禁词，用 * 替换。
    """
    for pat in _AD_PATTERNS:
        text = pat.sub("***", text)
    return text


def full_check(user_input: str) -> dict:
    """
    完整的内容安全检查。

    Returns
    -------
    dict with keys:
        - safe: bool, 是否安全
        - reason: str, 不安全的原因
        - cleaned: str, 清理后的文本
    """
    cleaned = sanitize_input(user_input)

    if not cleaned:
        return {"safe": False, "reason": "输入为空", "cleaned": ""}

    if check_injection(cleaned):
        return {"safe": False, "reason": "检测到异常输入，请重新提问", "cleaned": cleaned}

    return {"safe": True, "reason": "", "cleaned": cleaned}
