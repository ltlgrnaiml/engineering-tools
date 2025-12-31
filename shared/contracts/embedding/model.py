"""Embedding Model Contracts.

Stub implementation for DISC-005 (Embedding Model Selection).
Provides interfaces for text-to-vector embedding generation.

Decision: all-mpnet-base-v2 (768 dims) primary, all-MiniLM-L6-v2 (384 dims) fallback.
Search Strategy: Hybrid (BM25 + Vectors) with Reciprocal Rank Fusion.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


class EmbeddingMode(str, Enum):
    """Embedding generation mode."""

    LOCAL = "local"
    API = "api"


class EmbeddingModel(str, Enum):
    """Available embedding models."""

    # Local models (sentence-transformers)
    MPNET_BASE = "all-mpnet-base-v2"  # Primary: 768 dims
    MINILM_L6 = "all-MiniLM-L6-v2"  # Fallback: 384 dims

    # API models
    OPENAI_ADA = "text-embedding-ada-002"
    XAI_EMBED = "xai-embed-v1"


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation.

    Attributes:
        mode: Local or API embedding mode.
        model: Model to use for embeddings.
        dimensions: Expected embedding dimensions.
        batch_size: Number of texts to embed in parallel.
        normalize: Whether to L2-normalize vectors.
    """

    mode: EmbeddingMode = EmbeddingMode.LOCAL
    model: EmbeddingModel = EmbeddingModel.MPNET_BASE
    dimensions: int = 768
    batch_size: int = 32
    normalize: bool = True


class EmbeddingResult(BaseModel):
    """Result of an embedding operation.

    Attributes:
        vector: The embedding vector as list of floats.
        model: Model used for generation.
        dimensions: Dimensions of the vector.
        tokens_used: Number of tokens processed.
        error: Error message if embedding failed.
    """

    vector: list[float]
    model: EmbeddingModel
    dimensions: int
    tokens_used: int = 0
    error: str | None = None


class BatchEmbeddingResult(BaseModel):
    """Result of a batch embedding operation.

    Attributes:
        vectors: List of embedding vectors.
        model: Model used for generation.
        total_tokens: Total tokens processed.
        errors: List of errors (index, message).
    """

    vectors: list[list[float]]
    model: EmbeddingModel
    total_tokens: int = 0
    errors: list[tuple[int, str]] = Field(default_factory=list)


# === STUB IMPLEMENTATION ===
# Replace with full implementation when Phase 3 is executed


def embed(text: str, config: EmbeddingConfig | None = None) -> EmbeddingResult:
    """Generate embedding vector for text.

    STUB: Returns zero vector until implementation.

    Args:
        text: Text to embed.
        config: Embedding configuration.

    Returns:
        EmbeddingResult with vector.
    """
    cfg = config or EmbeddingConfig()
    # STUB: Return zero vector
    return EmbeddingResult(
        vector=[0.0] * cfg.dimensions,
        model=cfg.model,
        dimensions=cfg.dimensions,
        tokens_used=len(text.split()),
    )


def embed_batch(
    texts: list[str], config: EmbeddingConfig | None = None
) -> BatchEmbeddingResult:
    """Generate embedding vectors for multiple texts.

    STUB: Returns zero vectors until implementation.

    Args:
        texts: List of texts to embed.
        config: Embedding configuration.

    Returns:
        BatchEmbeddingResult with vectors.
    """
    cfg = config or EmbeddingConfig()
    # STUB: Return zero vectors
    return BatchEmbeddingResult(
        vectors=[[0.0] * cfg.dimensions for _ in texts],
        model=cfg.model,
        total_tokens=sum(len(t.split()) for t in texts),
    )
