"""
Offline knowledge-base indexing pipeline.

Orchestrates: load → chunk → vectorize → store.

Also rebuilds the BM25 sparse corpus after insertion.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from config.settings import settings
from mysql_module.bm25_scorer import build_corpus
from offline_kb.chunker import chunk_documents
from offline_kb.loaders.document_loader import load_directory, load_file
from offline_kb.vectorizer import vectorize_and_store
from rag_qa.milvus_store import collection_stats, delete_by_source

logger = logging.getLogger(__name__)


async def index_file(file_path: str | Path) -> dict:
    """
    Index a single file: load → chunk → vectorize → store → rebuild BM25.

    Returns status dict with counts.
    """
    path = Path(file_path)
    doc = load_file(path)
    parents, children = chunk_documents([doc])

    if not children:
        return {"status": "no_content", "file": str(path), "chunks": 0}

    n = vectorize_and_store(children)

    # Rebuild BM25 corpus from Milvus (simplified: use current children)
    bm25_docs = [
        {"text": c["text"], "source": c["file_name"], "chunk_index": c["chunk_index"], "parent_id": c["parent_id"]}
        for c in children
    ]
    # Append to existing corpus (full rebuild is preferred for production)
    _rebuild_bm25_from_all()

    logger.info(f"Indexed {path.name}: {n} chunks")
    return {
        "status": "ok",
        "file": str(path),
        "parent_chunks": len(parents),
        "child_chunks": len(children),
        "inserted": n,
    }


async def index_directory(directory: str | Path) -> dict:
    """
    Index all supported files in a directory recursively.
    """
    docs = load_directory(directory)
    if not docs:
        return {"status": "no_files", "directory": str(directory), "chunks": 0}

    parents, children = chunk_documents(docs)
    if not children:
        return {"status": "no_content", "directory": str(directory), "chunks": 0}

    n = vectorize_and_store(children)
    _rebuild_bm25_from_all()

    return {
        "status": "ok",
        "directory": str(directory),
        "documents": len(docs),
        "parent_chunks": len(parents),
        "child_chunks": len(children),
        "inserted": n,
    }


async def reindex_file(file_path: str | Path) -> dict:
    """
    Delete existing chunks for a file, then re-index it.
    """
    path = Path(file_path)
    delete_by_source(path.name)
    return await index_file(path)


async def delete_index(file_name: str) -> dict:
    """Remove all chunks belonging to a file from Milvus."""
    count = delete_by_source(file_name)
    _rebuild_bm25_from_all()
    return {"status": "deleted", "file": file_name, "chunks_removed": count}


def get_stats() -> dict:
    """Return Milvus collection stats."""
    return collection_stats()


def _rebuild_bm25_from_all() -> None:
    """
    Rebuild the BM25 in-memory corpus from all chunks currently in Milvus.

    Note: For very large collections, use a paginated approach or maintain
    a separate corpus. This is a simplified single-shot refresh.
    """
    try:
        from rag_qa.milvus_store import get_collection
        col = get_collection()
        # Query all chunks (limit reasonable number for BM25 corpus)
        results = col.query(
            expr="id != \"\"",
            output_fields=["text", "file_name", "chunk_index", "parent_id"],
            limit=100_000,
        )
        bm25_docs = [
            {"text": r["text"], "source": r["file_name"], "chunk_index": r["chunk_index"], "parent_id": r["parent_id"]}
            for r in results
        ]
        build_corpus(bm25_docs)
        logger.info(f"BM25 corpus rebuilt with {len(bm25_docs)} chunks")
    except Exception:
        logger.exception("Failed to rebuild BM25 corpus")
