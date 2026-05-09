"""
Parent-Child chunking engine.

Strategy
--------
1. Split document into *parent chunks* (larger, e.g. 1024 tokens) that
   provide sufficient context for the LLM to generate good answers.
2. Further split each parent into *child chunks* (smaller, e.g. 256 tokens)
   for fine-grained vector similarity search.
3. Link children → parent via parent_id, so that when a child is retrieved
   we can return the full parent text to the LLM.
"""

from __future__ import annotations

import logging
import uuid
from typing import Optional

from config.settings import settings

logger = logging.getLogger(__name__)

_enc = None


def _get_enc():
    global _enc
    if _enc is not None:
        return _enc
    try:
        import tiktoken
    except ImportError:
        raise ImportError("tiktoken not installed. Run: pip install tiktoken")
    try:
        _enc = tiktoken.get_encoding("cl100k_base")
    except Exception:
        _enc = tiktoken.get_encoding("o200k_base")
    return _enc


def _count_tokens(text: str) -> int:
    return len(_get_enc().encode(text))


def chunk_documents(documents) -> tuple[list[dict], list[dict]]:
    """
    Produce parent and child chunks from a list of LlamaIndex Documents.
    """
    try:
        from llama_index.core import Document
        from llama_index.core.node_parser import SentenceSplitter
    except ImportError:
        raise ImportError("llama-index not installed. Run: pip install llama-index")

    parent_splitter = SentenceSplitter(
        chunk_size=settings.PARENT_CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )
    child_splitter = SentenceSplitter(
        chunk_size=settings.CHILD_CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
    )

    parents: list[dict] = []
    children: list[dict] = []

    for doc in documents:
        file_name = doc.metadata.get("file_name", "unknown")
        file_type = doc.metadata.get("file_type", "")

        # Step 1: Split into parent chunks
        parent_nodes = parent_splitter.get_nodes_from_documents([doc])

        for pi, pnode in enumerate(parent_nodes):
            parent_id = uuid.uuid4().hex
            parent_text = pnode.get_content()

            parent_entry = {
                "id": parent_id,
                "text": parent_text,
                "file_name": file_name,
                "file_type": file_type,
                "chunk_index": pi,
                "child_ids": [],
            }

            # Step 2: Split parent into child chunks
            child_doc = Document(text=parent_text)
            child_nodes = child_splitter.get_nodes_from_documents([child_doc])

            for ci, cnode in enumerate(child_nodes):
                child_text = cnode.get_content()
                if not child_text.strip():
                    continue

                child_id = uuid.uuid4().hex
                parent_entry["child_ids"].append(child_id)

                children.append({
                    "id": child_id,
                    "text": child_text,
                    "parent_id": parent_id,
                    "parent_text": parent_text,
                    "file_name": file_name,
                    "file_type": file_type,
                    "chunk_index": len(children),
                })

            if parent_entry["child_ids"]:
                parents.append(parent_entry)

    logger.info(
        f"Chunking complete: {len(documents)} docs → "
        f"{len(parents)} parents, {len(children)} children"
    )
    return parents, children
