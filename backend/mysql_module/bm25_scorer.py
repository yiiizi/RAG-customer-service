"""
BM25 sparse retrieval using rank-bm25.

Used as the *sparse* leg of hybrid retrieval. Works on a corpus of
document chunks (child chunks from the knowledge base).

The scorer can operate in two modes:
1. **In-memory** — fast but limited corpus size; rebuild corpus on index refresh.
2. **MySQL-backed** — results are cached in the bm25_scores table plus Redis.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from rank_bm25 import BM25Okapi

from config.settings import settings

logger = logging.getLogger(__name__)

# ── In-memory corpus (trade memory for speed) ──────────────────────
_corpus_texts: list[str] = []
_corpus_metas: list[dict] = []
_bm25: Optional[BM25Okapi] = None
_corpus_tokenized: list[list[str]] = []


def _tokenize(text: str) -> list[str]:
    """Simple whitespace tokenizer; replace with jieba for Chinese."""
    return text.lower().split()


def build_corpus(documents: list[dict]) -> None:
    """
    Rebuild the BM25 corpus from a list of document dicts.

    Each dict must have:
        - text: str    (chunk content)
        - source: str  (file path)
        - chunk_index: int
        - parent_id: str
    """
    global _corpus_texts, _corpus_metas, _bm25, _corpus_tokenized

    _corpus_texts = [doc["text"] for doc in documents]
    _corpus_metas = [doc for doc in documents]
    _corpus_tokenized = [_tokenize(t) for t in _corpus_texts]
    _bm25 = BM25Okapi(_corpus_tokenized)

    logger.info(f"BM25 corpus built with {len(_corpus_texts)} documents")


def search(query: str, top_k: int | None = None) -> list[dict]:
    """
    Run BM25 against the in-memory corpus.

    Returns
    -------
    list[dict]
        Each item: {text, source, chunk_index, parent_id, score}
    """
    if _bm25 is None or len(_corpus_texts) == 0:
        logger.warning("BM25 corpus is empty — returning no results")
        return []

    top_k = top_k or settings.SPARSE_TOP_K
    tokenized = _tokenize(query)
    scores = _bm25.get_scores(tokenized)

    # Normalise to [0, 1]
    smax = float(scores.max())
    if smax > 0:
        scores = scores / smax

    top_indices = np.argsort(scores)[::-1][:top_k]

    results: list[dict] = []
    for idx in top_indices:
        if scores[idx] < settings.BM25_SCORE_THRESHOLD:
            continue
        meta = _corpus_metas[idx]
        results.append({
            "text": meta["text"],
            "source": meta.get("source", ""),
            "chunk_index": meta.get("chunk_index", -1),
            "parent_id": meta.get("parent_id", ""),
            "score": float(scores[idx]),
        })

    return results


def is_high_confidence(query: str, threshold: float | None = None) -> bool:
    """Return True if the top BM25 score exceeds the threshold."""
    threshold = threshold or settings.BM25_SCORE_THRESHOLD
    results = search(query, top_k=1)
    if not results:
        return False
    return results[0]["score"] >= threshold


def corpus_size() -> int:
    return len(_corpus_texts)


def clear_corpus() -> None:
    global _corpus_texts, _corpus_metas, _bm25, _corpus_tokenized
    _corpus_texts = []
    _corpus_metas = []
    _bm25 = None
    _corpus_tokenized = []
