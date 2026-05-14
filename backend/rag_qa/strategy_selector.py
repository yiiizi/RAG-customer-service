"""
Strategy Selector: routes user query to the correct processing path based on intent.

Intent → Strategy mapping:
- chat           → direct_llm (no retrieval)
- faq            → cache_first (Redis → MySQL → fallback retrieval)
- knowledge_qa   → full_retrieval (Milvus + BM25 → RRF → Reranker → LLM)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

Strategy = Callable[[str, dict[str, Any]], Any]


@dataclass
class StrategyResult:
    strategy_name: str
    intent: str
    answer: str
    sources: list[dict]
    latency_ms: int
    metadata: dict


class StrategySelector:
    """Registry of intent → strategy callables."""

    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, intent: str, fn: Strategy) -> None:
        self._strategies[intent] = fn

    async def route(
        self,
        intent: str,
        query: str,
        extra: dict[str, Any] | None = None,
    ) -> StrategyResult:
        """Route query to the appropriate strategy."""
        fn = self._strategies.get(intent)
        if fn is None:
            # Fall back to knowledge_qa if no dedicated strategy
            fn = self._strategies.get("knowledge_qa")
            if fn is None:
                raise RuntimeError(f"No strategy registered for intent '{intent}' and no fallback")

        import time
        start = time.perf_counter()
        result = await fn(query, extra or {})
        elapsed = int((time.perf_counter() - start) * 1000)

        return StrategyResult(
            strategy_name=intent,
            intent=intent,
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            latency_ms=elapsed,
            metadata=result.get("metadata", {}),
        )


# Singleton
selector = StrategySelector()
