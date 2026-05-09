"""
BGE-Reranker using FlagEmbedding. Lazy-loads on first use.
"""

from __future__ import annotations

import logging
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)

_model: Optional[object] = None
_import_error: str | None = None


def get_model():
    global _model, _import_error
    if _model is not None:
        return _model
    if _import_error:
        raise ImportError(f"FlagEmbedding not available: {_import_error}")
    try:
        from FlagEmbedding import FlagReranker
    except ImportError as e:
        _import_error = str(e)
        raise ImportError("FlagEmbedding not installed. Run: pip install FlagEmbedding torch") from e

    logger.info(f"Loading BGE-Reranker: {settings.RERANKER_MODEL_NAME} on {settings.RERANKER_DEVICE}")
    _model = FlagReranker(
        settings.RERANKER_MODEL_NAME,
        use_fp16=settings.RERANKER_DEVICE == "cuda",
        device=settings.RERANKER_DEVICE,
    )
    return _model


def rerank(query: str, passages: list[str], top_n: int | None = None) -> list[dict]:
    model = get_model()
    top_n = top_n or settings.RERANKER_TOP_N

    pairs = [[query, passage] for passage in passages]
    scores = model.compute_score(pairs, normalize=True)

    if not isinstance(scores, list):
        scores = [scores]

    indexed = [
        {"text": passages[i], "score": float(scores[i]), "index": i}
        for i in range(len(passages))
    ]
    indexed.sort(key=lambda x: x["score"], reverse=True)
    return indexed[:top_n]
