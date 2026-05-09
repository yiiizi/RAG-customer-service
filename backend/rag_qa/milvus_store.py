"""
Milvus vector-database connection management and CRUD.

All connection attempts have a short timeout so the app never hangs
when Milvus is unavailable.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

import numpy as np
from pymilvus import (
    Collection,
    CollectionSchema,
    DataType,
    FieldSchema,
    MilvusClient,
    connections,
    utility,
)

from config.settings import settings

logger = logging.getLogger(__name__)

_client: Optional[MilvusClient] = None
_collection: Optional[Collection] = None
_available: Optional[bool] = None  # None=unchecked, True/False=result

_ID_MAX_LEN = 128
_TEXT_MAX_LEN = 8192
_NAME_MAX_LEN = 512


def _schema() -> CollectionSchema:
    fields = [
        FieldSchema("id", DataType.VARCHAR, is_primary=True, max_length=_ID_MAX_LEN),
        FieldSchema("text", DataType.VARCHAR, max_length=_TEXT_MAX_LEN),
        FieldSchema("embedding", DataType.FLOAT_VECTOR, dim=settings.MILVUS_DIM),
        FieldSchema("parent_id", DataType.VARCHAR, max_length=_ID_MAX_LEN),
        FieldSchema("parent_text", DataType.VARCHAR, max_length=_TEXT_MAX_LEN),
        FieldSchema("file_name", DataType.VARCHAR, max_length=_NAME_MAX_LEN),
        FieldSchema("file_type", DataType.VARCHAR, max_length=64),
        FieldSchema("chunk_index", DataType.INT64),
        FieldSchema("created_at", DataType.INT64),
    ]
    return CollectionSchema(fields, description="RAG knowledge base collection")


def is_available() -> bool:
    """Quick check — returns cached result. Use for health checks."""
    global _available
    if _available is not None:
        return _available
    try:
        _connect()
        _available = True
    except Exception:
        _available = False
    return _available


def _connect() -> MilvusClient:
    global _client, _available
    if _client is not None:
        return _client

    try:
        connections.connect(
            alias="default",
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT,
            db_name=settings.MILVUS_DB_NAME,
            timeout=3,
        )
        _client = MilvusClient(
            uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}",
            timeout=5,
        )
        _available = True
        logger.info(f"Connected to Milvus at {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        return _client
    except Exception as e:
        _available = False
        raise RuntimeError(f"Milvus unavailable: {e}") from e


def get_collection() -> Collection:
    global _collection
    if _collection is not None:
        return _collection

    client = _connect()

    if not utility.has_collection(settings.MILVUS_COLLECTION):
        client.create_collection(
            collection_name=settings.MILVUS_COLLECTION,
            schema=_schema(),
        )
        logger.info(f"Created Milvus collection: {settings.MILVUS_COLLECTION}")

    _collection = Collection(settings.MILVUS_COLLECTION)
    _ensure_index(_collection)
    _collection.load()
    return _collection


def _ensure_index(collection: Collection) -> None:
    if collection.has_index():
        return
    index_params = {
        "index_type": settings.MILVUS_INDEX_TYPE,
        "metric_type": settings.MILVUS_METRIC_TYPE,
        "params": {"nlist": settings.MILVUS_NLIST},
    }
    collection.create_index("embedding", index_params)
    logger.info(f"Created index: {settings.MILVUS_INDEX_TYPE} ({settings.MILVUS_METRIC_TYPE})")


def insert_chunks(chunks: list[dict]) -> list[str]:
    col = get_collection()
    now = int(time.time())
    data: list[list] = [[] for _ in range(9)]
    ids: list[str] = []
    for i, chunk in enumerate(chunks):
        ids.append(chunk.get("id", uuid.uuid4().hex))
        data[0].append(ids[-1])
        data[1].append(chunk["text"])
        emb = chunk["embedding"]
        data[2].append(emb.tolist() if isinstance(emb, np.ndarray) else emb)
        data[3].append(chunk.get("parent_id", ""))
        data[4].append(chunk.get("parent_text", ""))
        data[5].append(chunk.get("file_name", ""))
        data[6].append(chunk.get("file_type", ""))
        data[7].append(chunk.get("chunk_index", i))
        data[8].append(now)
    col.insert(data)
    col.flush()
    logger.info(f"Inserted {len(ids)} chunks into Milvus")
    return ids


def search(
    query_vector: np.ndarray,
    top_k: int | None = None,
    expr: str | None = None,
) -> list[dict]:
    col = get_collection()
    top_k = top_k or settings.DENSE_TOP_K
    search_params = {
        "metric_type": settings.MILVUS_METRIC_TYPE,
        "params": {"nprobe": 16},
    }
    vec_list = query_vector.tolist()
    # If shape is (1, D), unwrap one level. Milvus expects list[list[float]].
    if isinstance(vec_list, list) and len(vec_list) == 1 and isinstance(vec_list[0], list):
        vec_list = vec_list
    results = col.search(
        data=vec_list,
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        expr=expr,
        output_fields=[
            "id", "text", "parent_id", "parent_text",
            "file_name", "file_type", "chunk_index",
        ],
    )
    hits: list[dict] = []
    for hits_batch in results:
        for hit in hits_batch:
            hits.append({
                "id": hit.id,
                "text": hit.entity.get("text", ""),
                "parent_id": hit.entity.get("parent_id", ""),
                "parent_text": hit.entity.get("parent_text", ""),
                "file_name": hit.entity.get("file_name", ""),
                "file_type": hit.entity.get("file_type", ""),
                "chunk_index": hit.entity.get("chunk_index", -1),
                "score": float(hit.distance),
            })
    return hits


def delete_by_source(file_name: str) -> int:
    col = get_collection()
    expr = f'file_name == "{file_name}"'
    ids_to_delete = col.query(expr=expr, output_fields=["id"])
    if ids_to_delete:
        col.delete(f'file_name == "{file_name}"')
        col.flush()
        logger.info(f"Deleted {len(ids_to_delete)} chunks for file: {file_name}")
        return len(ids_to_delete)
    return 0


def collection_stats() -> dict:
    col = get_collection()
    return {
        "total_chunks": col.num_entities,
        "collection_name": settings.MILVUS_COLLECTION,
        "dimension": settings.MILVUS_DIM,
    }
