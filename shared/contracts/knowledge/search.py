"""Knowledge Search Contracts.

Contracts for full-text and semantic search in the Knowledge Archive.
Implements ADR-0047 search layer requirements.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


class RelationshipType(str, Enum):
    """Types of relationships between documents."""

    IMPLEMENTS = "implements"  # SPEC implements ADR
    REFERENCES = "references"  # Cross-reference
    SUPERSEDES = "supersedes"  # Newer replaces older
    CREATES = "creates"  # Discussion creates ADR


class Relationship(BaseModel):
    """A relationship between two documents.

    Attributes:
        source_id: Source document ID.
        target_id: Target document ID.
        type: Type of relationship.
    """

    source_id: str
    target_id: str
    type: RelationshipType


class SearchQuery(BaseModel):
    """Query parameters for search operations.

    Attributes:
        query: Search query string.
        doc_types: Filter by document types.
        limit: Maximum results to return.
        offset: Offset for pagination.
        include_archived: Include archived documents.
    """

    query: str
    doc_types: list[str] | None = None
    limit: int = 20
    offset: int = 0
    include_archived: bool = False


class SearchResult(BaseModel):
    """A single search result.

    Attributes:
        doc_id: Document ID.
        doc_type: Document type.
        title: Document title.
        snippet: Matching text snippet with highlights.
        score: Relevance score (higher = more relevant).
        source: Search source (fts, vector, hybrid).
    """

    doc_id: str
    doc_type: str
    title: str
    snippet: str
    score: float
    source: str = "hybrid"


class HybridSearchConfig(BaseModel):
    """Configuration for hybrid search.

    Attributes:
        fts_weight: Weight for FTS5 results in fusion.
        vector_weight: Weight for vector results in fusion.
        rrf_k: RRF constant (default: 60).
        top_k: Number of results from each source.
        similarity_threshold: Minimum similarity for vector results.
    """

    fts_weight: float = 1.0
    vector_weight: float = 1.0
    rrf_k: int = 60
    top_k: int = 20
    similarity_threshold: float = 0.5
