"""Chunking Service - SPEC-0043-CH01, CH02, CH03.

Content-aware text segmentation with metadata tracking.
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Chunk:
    """A chunk of document content."""
    doc_id: str
    chunk_index: int
    content: str
    start_char: int
    end_char: int
    token_count: int
    strategy: str


class ChunkingService:
    """Content-aware chunking service."""

    TARGET_TOKENS = 384  # Middle of 256-512 range
    CHARS_PER_TOKEN = 4  # Rough approximation
    MAX_CHUNK_CHARS = 2048  # ~512 tokens
    OVERLAP_CHARS = 200  # ~50 tokens overlap

    def chunk_document(self, doc_id: str, content: str, file_ext: str) -> list[Chunk]:
        """Chunk document based on file type."""
        if file_ext in ('.md', '.markdown'):
            return self._chunk_markdown(doc_id, content)
        elif file_ext == '.py':
            return self._chunk_python(doc_id, content)
        elif file_ext == '.json':
            return self._chunk_json(doc_id, content)
        return self._chunk_paragraphs(doc_id, content)

    def _chunk_markdown(self, doc_id: str, content: str) -> list[Chunk]:
        """Split markdown on ## headers (SPEC-0043-CH01)."""
        sections = re.split(r'\n(?=## )', content)
        chunks = []
        char_pos = 0

        for i, section in enumerate(sections):
            if not section.strip():
                char_pos += len(section)
                continue
            chunks.append(Chunk(
                doc_id=doc_id,
                chunk_index=i,
                content=section.strip(),
                start_char=char_pos,
                end_char=char_pos + len(section),
                token_count=len(section) // self.CHARS_PER_TOKEN,
                strategy='markdown_headers'
            ))
            char_pos += len(section)

        return chunks if chunks else [self._single_chunk(doc_id, content, 'markdown_whole')]

    def _chunk_python(self, doc_id: str, content: str) -> list[Chunk]:
        """Split Python on function/class boundaries."""
        pattern = r'\n(?=(?:def |class |async def ))'
        sections = re.split(pattern, content)
        chunks = []
        char_pos = 0

        for i, section in enumerate(sections):
            if not section.strip():
                char_pos += len(section)
                continue
            chunks.append(Chunk(
                doc_id=doc_id,
                chunk_index=i,
                content=section.strip(),
                start_char=char_pos,
                end_char=char_pos + len(section),
                token_count=len(section) // self.CHARS_PER_TOKEN,
                strategy='python_functions'
            ))
            char_pos += len(section)

        return chunks if chunks else [self._single_chunk(doc_id, content, 'python_whole')]

    def _chunk_json(self, doc_id: str, content: str) -> list[Chunk]:
        """JSON as single chunk (SPEC-0043-CH01)."""
        return [self._single_chunk(doc_id, content, 'json_whole')]

    def _chunk_paragraphs(self, doc_id: str, content: str) -> list[Chunk]:
        """Fallback: split on double newlines."""
        paragraphs = re.split(r'\n\n+', content)
        chunks = []
        char_pos = 0

        for i, para in enumerate(paragraphs):
            if not para.strip():
                char_pos += len(para) + 2
                continue
            chunks.append(Chunk(
                doc_id=doc_id,
                chunk_index=i,
                content=para.strip(),
                start_char=char_pos,
                end_char=char_pos + len(para),
                token_count=len(para) // self.CHARS_PER_TOKEN,
                strategy='paragraphs'
            ))
            char_pos += len(para) + 2

        return chunks if chunks else [self._single_chunk(doc_id, content, 'single')]

    def _single_chunk(self, doc_id: str, content: str, strategy: str) -> Chunk:
        """Create single chunk for entire content."""
        return Chunk(
            doc_id=doc_id,
            chunk_index=0,
            content=content,
            start_char=0,
            end_char=len(content),
            token_count=len(content) // self.CHARS_PER_TOKEN,
            strategy=strategy
        )

    def rechunk_document(self, conn, doc_id: str) -> int:
        """Re-chunk document after update (SPEC-0043-CH03).

        Deletes old chunks (embeddings CASCADE) and creates new ones.
        """
        # Delete old chunks (embeddings cascade delete via FK)
        conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))

        # Get document content
        row = conn.execute(
            "SELECT content, file_path FROM documents WHERE id = ?", (doc_id,)
        ).fetchone()

        if not row:
            return 0

        # Re-chunk based on file extension
        ext = Path(row['file_path']).suffix
        chunks = self.chunk_document(doc_id, row['content'], ext)

        # Store new chunks
        for chunk in chunks:
            conn.execute("""
                INSERT INTO chunks (doc_id, chunk_index, content, start_char, end_char, token_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chunk.doc_id, chunk.chunk_index, chunk.content,
                  chunk.start_char, chunk.end_char, chunk.token_count))

        conn.commit()
        return len(chunks)

    def chunk_and_store(self, conn, doc_id: str, content: str, file_path: str) -> int:
        """Chunk document and store in database."""
        ext = Path(file_path).suffix
        chunks = self.chunk_document(doc_id, content, ext)

        for chunk in chunks:
            conn.execute("""
                INSERT OR REPLACE INTO chunks
                (doc_id, chunk_index, content, start_char, end_char, token_count)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (chunk.doc_id, chunk.chunk_index, chunk.content,
                  chunk.start_char, chunk.end_char, chunk.token_count))

        conn.commit()
        return len(chunks)
