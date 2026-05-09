"""
Hybrid retriever: Dense (Milvus) + Sparse (BM25) → RRF fusion → BGE-Reranker.

This is the core retrieval pipeline of the RAG system. It combines:
1. Dense recall  — Milvus ANN search with BGE-M3 embeddings
2. Sparse recall — BM25 lexical matching via rank-bm25
3. RRF fusion   — Reciprocal Rank Fusion merges both result lists
4. Re-rank      — BGE-Reranker cross-encoder for final precision ordering
"""

from __future__ import annotations

import logging

import numpy as np

from config.settings import settings
from mysql_module.bm25_scorer import search as bm25_search
from rag_qa.embedder import encode_single
from rag_qa.milvus_store import search as dense_search, is_available as milvus_available
from rag_qa.reranker import rerank

logger = logging.getLogger(__name__)


def _rrf_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    k: int = 60,
    top_n: int = 20,
) -> list[dict]:
    """
    Reciprocal Rank Fusion.

    Each candidate gets score = sum( 1 / (k + rank_i) ) across result lists.

    Returns combined list sorted by RRF score descending.
    """
    scores: dict[str, dict] = {}  # keyed by passage text (dedup)

    for rank, item in enumerate(dense_results):
        key = item["text"]
        if key not in scores:
            scores[key] = {**item, "rrf_score": 0.0}
        scores[key]["rrf_score"] += 1.0 / (k + rank + 1)

    for rank, item in enumerate(sparse_results):
        key = item["text"]
        if key not in scores:
            scores[key] = {**item, "rrf_score": 0.0}
        scores[key]["rrf_score"] += 1.0 / (k + rank + 1)

    fused = sorted(scores.values(), key=lambda x: x["rrf_score"], reverse=True)
    return fused[:top_n]


def retrieve(
    query: str,
    dense_top_k: int | None = None,
    sparse_top_k: int | None = None,
    use_rerank: bool = True,
) -> list[dict]:
    """
    Run hybrid retrieval for a user query.

    Parameters
    ----------
    query : str
        The user question.
    dense_top_k : int, optional
        Top-K for Milvus ANN search.
    sparse_top_k : int, optional
        Top-K for BM25 search.
    use_rerank : bool
        Whether to apply BGE-Reranker after RRF fusion.

    Returns
    -------
    list[dict]
        Final ranked passages. Each dict has:
        {text, score, parent_id, parent_text, source, chunk_index}
    """
    dense_k = dense_top_k or settings.DENSE_TOP_K
    sparse_k = sparse_top_k or settings.SPARSE_TOP_K

    # ── 1. Dense retrieval ─────────────────────────────────────────
    dense_results: list[dict] = []
    if milvus_available():
        try:
            query_vec = encode_single(query)
            dense_results = dense_search(query_vec, top_k=dense_k)
        except Exception as e:
            logger.warning(f"Dense search failed (Milvus down?), falling back to BM25 only: {e}")
    else:
        logger.info("Milvus unavailable — skipping dense search")

    # ── 2. Sparse (BM25) retrieval ─────────────────────────────────
    sparse_results = bm25_search(query, top_k=sparse_k)

    # ── 3. Relevance check ────────────────────────────────────────
    best_dense = max((d["score"] for d in dense_results), default=0)
    best_sparse = max((d["score"] for d in sparse_results), default=0)
    has_sparse = len(sparse_results) > 0 and best_sparse > 0.1
    # Require: dense score > 0.55, OR BM25 has matches. This filters
    # weak vector-only matches in small knowledge bases.
    if best_dense < 0.55 and not has_sparse:
        logger.info(f"Relevance filtered: dense={best_dense:.3f}, sparse={best_sparse:.3f}")
        return []

    fused = _rrf_fusion(dense_results, sparse_results, k=settings.RRF_K)

    if not fused:
        logger.warning("No results after RRF fusion — returning empty")
        return []

    # ── 4. BGE-Reranker ────────────────────────────────────────────
    if use_rerank:
        try:
            passages = [item["text"] for item in fused]
            reranked = rerank(query, passages)

            # Map reranker output back to original items, deduplicate by parent
            final: list[dict] = []
            seen_pids: set[str] = set()
            for rr in reranked:
                original = fused[rr["index"]]
                pid = original.get("parent_id", "")
                if pid and pid in seen_pids:
                    continue
                if pid:
                    seen_pids.add(pid)
                final.append({
                    "text": original.get("parent_text", original["text"]),
                    "source": original.get("file_name", original.get("source", "")),
                    "score": round(rr["score"] * 100),
                    "parent_id": pid,
                    "chunk_index": original.get("chunk_index", -1),
                })
            return final
        except Exception as e:
            logger.warning(f"Reranker failed, using fused results: {e}")

    # ── Without reranker — deduplicate by parent, normalize 0~1 ────
    seen: set[str] = set()
    deduped: list[dict] = []
    for item in fused:
        pid = item.get("parent_id", "")
        if pid and pid in seen:
            continue
        if pid:
            seen.add(pid)
        deduped.append({
            "text": item.get("parent_text", item["text"]),
            "source": item.get("file_name", item.get("source", "")),
            "score": item.get("rrf_score", item.get("score", 0.0)),
            "parent_id": pid,
            "chunk_index": item.get("chunk_index", -1),
        })
    # Normalize to 0~1: top result = 1.0, rest proportional
    if deduped:
        max_score = max(d["score"] for d in deduped)
        if max_score > 0:
            for d in deduped:
                d["score"] = round(d["score"] / max_score, 4)
    return deduped
