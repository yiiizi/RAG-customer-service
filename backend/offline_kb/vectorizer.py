"""
Batch vectorizer: BGE-M3 embedding for child chunks, then write to Milvus.
"""

from __future__ import annotations

import logging

import numpy as np

from config.settings import settings
from rag_qa.embedder import encode_documents
from rag_qa.milvus_store import insert_chunks

logger = logging.getLogger(__name__)


def vectorize_and_store(children: list[dict]) -> int:
    """
    Encode all child chunks with BGE-M3 and insert into Milvus.

    Parameters
    ----------
    children : list[dict]
        Child chunks from the chunker. Each must have: id, text, parent_id,
        parent_text, file_name, file_type, chunk_index.

    Returns
    -------
    int
        Number of chunks inserted.
    """
    if not children:
        logger.warning("No child chunks to vectorize")
        return 0

    texts = [c["text"] for c in children]
    total = len(texts)
    batch_size = settings.EMBED_BATCH_SIZE

    all_embeddings: list[np.ndarray] = []

    for start in range(0, total, batch_size):
        batch = texts[start : start + batch_size]
        embs = encode_documents(batch)
        all_embeddings.append(embs)
        logger.info(f"Vectorized {min(start + batch_size, total)}/{total} chunks")

    embeddings = np.concatenate(all_embeddings, axis=0)

    # Attach embeddings to children
    for i, child in enumerate(children):
        child["embedding"] = embeddings[i]

    # Write to Milvus
    ids = insert_chunks(children)
    logger.info(f"Inserted {len(ids)} chunks into Milvus")
    return len(ids)
