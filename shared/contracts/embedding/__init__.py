"""Embedding contracts for vector generation.

This module provides stub contracts for the embedding service.
Replace with full implementation when DISC-005 is implemented.
"""

__version__ = "2025.12.01"

from .model import (
    EmbeddingConfig,
    EmbeddingMode,
    EmbeddingModel,
    EmbeddingResult,
)

__all__ = [
    "EmbeddingConfig",
    "EmbeddingMode",
    "EmbeddingModel",
    "EmbeddingResult",
]
