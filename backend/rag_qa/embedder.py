"""
BGE-M3 embedding wrapper using FlagEmbedding (BAAI official library).
Lazy-loads the model on first use — server starts without torch installed.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

from config.settings import settings

logger = logging.getLogger(__name__)

_model: Optional[object] = None
_import_error: str | None = None


def _get_model_class():
    global _import_error
    if _import_error:
        raise ImportError(f"FlagEmbedding not available: {_import_error}")
    import os
    os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")
    try:
        from FlagEmbedding import BGEM3FlagModel
        return BGEM3FlagModel
    except ImportError as e:
        _import_error = str(e)
        logger.exception(f"FlagEmbedding import failed: {e}")
        raise ImportError(
            f"FlagEmbedding not available: {e}"
        ) from e
    except OSError as e:
        _import_error = str(e)
        logger.exception(f"FlagEmbedding OSError (DLL issue): {e}")
        raise ImportError(
            f"FlagEmbedding not available (DLL): {e}"
        ) from e
    except Exception as e:
        _import_error = f"{type(e).__name__}: {e}"
        logger.exception(f"FlagEmbedding unexpected error: {e}")
        raise ImportError(
            f"FlagEmbedding not available ({type(e).__name__}): {e}"
        ) from e


def get_model():
    global _model
    if _model is None:
        import os
        # Force offline mode — use cached model files only (use os.environ dict directly)
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ.pop("HF_ENDPOINT", None)
        os.environ.pop("HF_TOKEN", None)
        logger.info(f"HF_HUB_OFFLINE={os.environ.get('HF_HUB_OFFLINE')}, "
                    f"TRANSFORMERS_OFFLINE={os.environ.get('TRANSFORMERS_OFFLINE')}")
        BGEM3FlagModel = _get_model_class()
        logger.info(f"Loading BGE-M3: {settings.EMBED_MODEL_NAME} on {settings.EMBED_DEVICE}")
        _model = BGEM3FlagModel(
            settings.EMBED_MODEL_NAME,
            use_fp16=settings.EMBED_DEVICE == "cuda",
            device=settings.EMBED_DEVICE,
        )
    return _model


def encode_queries(queries: list[str]) -> np.ndarray:
    model = get_model()
    output = model.encode(
        queries,
        batch_size=settings.EMBED_BATCH_SIZE,
        max_length=settings.EMBED_MAX_LENGTH,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )
    return np.array(output["dense_vecs"], dtype=np.float32)


def encode_documents(documents: list[str]) -> np.ndarray:
    model = get_model()
    output = model.encode(
        documents,
        batch_size=settings.EMBED_BATCH_SIZE,
        max_length=settings.EMBED_MAX_LENGTH,
        return_dense=True,
        return_sparse=False,
        return_colbert_vecs=False,
    )
    return np.array(output["dense_vecs"], dtype=np.float32)


def encode_single(text: str) -> np.ndarray:
    return encode_queries([text])
