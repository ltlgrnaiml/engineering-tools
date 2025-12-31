"""Embedding Service - SPEC-0043-EM01, EM02, EM03, EM04.

Generate embeddings with dual-mode and auto-fallback.
"""

import os
import struct
from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class EmbeddingResult:
    """Result of embedding operation."""
    vector: list[float]
    model: str
    dimensions: int


class EmbeddingService:
    """Embedding generation with fallback support."""

    PRIMARY_MODEL = 'all-mpnet-base-v2'  # 768 dims
    FALLBACK_MODEL = 'all-MiniLM-L6-v2'  # 384 dims

    def __init__(self, batch_size: int = 32):
        self.batch_size = batch_size
        self._model = None
        self._model_name: str | None = None
        self._mode = os.getenv('KNOWLEDGE_EMBEDDING_MODE', 'local')

    def _load_model(self, model_name: str):
        """Lazy load model with fallback on MemoryError."""
        if self._model_name == model_name:
            return

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name)
            self._model_name = model_name
        except MemoryError:
            if model_name == self.PRIMARY_MODEL:
                # Auto-fallback (SPEC-0043-EM02)
                self._load_model(self.FALLBACK_MODEL)
            else:
                raise
        except ImportError:
            raise ImportError("sentence-transformers required. Install with: pip install sentence-transformers")

    def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding for single text."""
        self._load_model(self.PRIMARY_MODEL)
        vec = self._model.encode(text, normalize_embeddings=True)
        return EmbeddingResult(
            vector=vec.tolist(),
            model=self._model_name,
            dimensions=len(vec)
        )

    def embed_batch(self, texts: list[str]) -> list[EmbeddingResult]:
        """Generate embeddings for multiple texts."""
        self._load_model(self.PRIMARY_MODEL)
        vectors = self._model.encode(texts, normalize_embeddings=True, batch_size=self.batch_size)
        return [
            EmbeddingResult(vector=v.tolist(), model=self._model_name, dimensions=len(v))
            for v in vectors
        ]

    @staticmethod
    def vector_to_blob(vector: list[float]) -> bytes:
        """Serialize vector to BLOB for SQLite storage."""
        return struct.pack(f'{len(vector)}f', *vector)

    @staticmethod
    def blob_to_vector(blob: bytes) -> list[float]:
        """Deserialize vector from BLOB."""
        count = len(blob) // 4
        return list(struct.unpack(f'{count}f', blob))

    def embed_all_chunks(
        self,
        conn,
        progress_callback: Callable[[int, int], None] | None = None
    ) -> int:
        """Embed all chunks without embeddings (resume-capable).

        SPEC-0043-EM04: Batch processing with progress callback.
        """
        # Find unembedded chunks
        rows = conn.execute("""
            SELECT c.id, c.content FROM chunks c
            LEFT JOIN embeddings e ON e.chunk_id = c.id
            WHERE e.chunk_id IS NULL
        """).fetchall()

        if not rows:
            return 0

        self._load_model(self.PRIMARY_MODEL)
        total = len(rows)
        embedded = 0

        for i in range(0, total, self.batch_size):
            batch = rows[i:i + self.batch_size]
            texts = [r['content'] for r in batch]
            vectors = self._model.encode(texts, normalize_embeddings=True)

            for row, vec in zip(batch, vectors):
                conn.execute(
                    "INSERT INTO embeddings (chunk_id, vector, model, dimensions) VALUES (?,?,?,?)",
                    (row['id'], self.vector_to_blob(vec.tolist()), self._model_name, len(vec))
                )
                embedded += 1

            conn.commit()  # Commit each batch for resume

            if progress_callback:
                progress_callback(embedded, total)

        return embedded
