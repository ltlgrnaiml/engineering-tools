"""Search Service - SPEC-0043-SE01, SE02, SE03, SE04.

Full-text search, vector search, and hybrid search.
"""

import sqlite3
from dataclasses import dataclass

from gateway.services.knowledge.database import get_connection


@dataclass
class SearchHit:
    """Internal search result."""
    doc_id: str
    title: str
    snippet: str
    score: float
    doc_type: str


class SearchService:
    """Search service with FTS, vector, and hybrid modes."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        self.conn = conn or get_connection()

    def fts_search(self, query: str, top_k: int = 10) -> list[SearchHit]:
        """Full-text search using FTS5 (SPEC-0043-SE01)."""
        # Simple FTS search on documents table directly
        rows = self.conn.execute("""
            SELECT
                id as doc_id,
                title,
                substr(content, 1, 200) as snippet,
                type as doc_type
            FROM documents
            WHERE archived_at IS NULL
              AND (title LIKE ? OR content LIKE ?)
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', top_k)).fetchall()

        return [
            SearchHit(
                doc_id=r['doc_id'],
                title=r['title'],
                snippet=r['snippet'],
                score=1.0,  # Simple match score
                doc_type=r['doc_type']
            )
            for r in rows
        ]

    def _blob_to_vector(self, blob: bytes) -> list[float]:
        """Deserialize vector from BLOB."""
        import struct
        count = len(blob) // 4  # float32 = 4 bytes
        return list(struct.unpack(f'{count}f', blob))

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot / (norm1 * norm2)

    def vector_search(self, query_vector: list[float], top_k: int = 10) -> list[SearchHit]:
        """Vector similarity search (SPEC-0043-SE02)."""
        rows = self.conn.execute("""
            SELECT
                e.vector,
                c.doc_id,
                c.content as snippet,
                d.title,
                d.type as doc_type
            FROM embeddings e
            JOIN chunks c ON e.chunk_id = c.id
            JOIN documents d ON c.doc_id = d.id
            WHERE d.archived_at IS NULL
        """).fetchall()

        scored = []
        for r in rows:
            vec = self._blob_to_vector(r['vector'])
            sim = self._cosine_similarity(query_vector, vec)
            scored.append(SearchHit(
                doc_id=r['doc_id'],
                title=r['title'],
                snippet=r['snippet'][:200],
                score=sim,
                doc_type=r['doc_type']
            ))

        scored.sort(key=lambda x: x.score, reverse=True)
        return scored[:top_k]

    def hybrid_search(
        self,
        query: str,
        query_vector: list[float] | None = None,
        top_k: int = 10,
        fts_weight: float = 0.5,
        vec_weight: float = 0.5
    ) -> list[SearchHit]:
        """Hybrid search with Reciprocal Rank Fusion (SPEC-0043-SE03).

        RRF formula: score = sum(1 / (k + rank)) where k=60
        """
        k = 60  # RRF constant
        rrf_scores: dict[str, float] = {}
        doc_data: dict[str, SearchHit] = {}

        # FTS results
        fts_results = self.fts_search(query, top_k * 2)
        for rank, hit in enumerate(fts_results):
            rrf_scores[hit.doc_id] = rrf_scores.get(hit.doc_id, 0) + fts_weight / (k + rank + 1)
            doc_data[hit.doc_id] = hit

        # Vector results (if vector provided)
        if query_vector:
            vec_results = self.vector_search(query_vector, top_k * 2)
            for rank, hit in enumerate(vec_results):
                rrf_scores[hit.doc_id] = rrf_scores.get(hit.doc_id, 0) + vec_weight / (k + rank + 1)
                if hit.doc_id not in doc_data:
                    doc_data[hit.doc_id] = hit

        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

        return [
            SearchHit(
                doc_id=doc_data[doc_id].doc_id,
                title=doc_data[doc_id].title,
                snippet=doc_data[doc_id].snippet,
                score=rrf_scores[doc_id],
                doc_type=doc_data[doc_id].doc_type
            )
            for doc_id in sorted_ids[:top_k]
        ]
