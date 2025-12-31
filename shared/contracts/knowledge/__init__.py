"""Knowledge Archive contracts for document storage and RAG.

This module provides contracts for the Knowledge Archive & RAG system.
"""

__version__ = "2025.12.01"

from .archive import (
    Document,
    DocumentMetadata,
    DocumentType,
    SyncConfig,
    SyncMode,
    SyncStatus,
)
from .search import (
    HybridSearchConfig,
    Relationship,
    RelationshipType,
    SearchQuery,
    SearchResult,
)
from .rag import (
    Chunk,
    ChunkingStrategy,
    ContextRequest,
    RAGContext,
)

__all__ = [
    # Archive
    "Document",
    "DocumentMetadata",
    "DocumentType",
    "SyncConfig",
    "SyncMode",
    "SyncStatus",
    # Search
    "HybridSearchConfig",
    "Relationship",
    "RelationshipType",
    "SearchQuery",
    "SearchResult",
    # RAG
    "Chunk",
    "ChunkingStrategy",
    "ContextRequest",
    "RAGContext",
]
