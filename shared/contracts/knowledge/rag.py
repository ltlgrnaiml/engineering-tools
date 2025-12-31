"""Knowledge RAG Contracts.

Contracts for Retrieval-Augmented Generation context building.
Implements ADR-0047 RAG layer requirements.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


class ChunkingStrategy(str, Enum):
    """Chunking strategies for different content types."""

    MARKDOWN_HEADERS = "markdown_headers"  # Split on ## headers
    PYTHON_FUNCTIONS = "python_functions"  # Function/class boundaries
    JSON_WHOLE = "json_whole"  # Keep JSON documents whole
    PARAGRAPH = "paragraph"  # Split on paragraphs
    FIXED_SIZE = "fixed_size"  # Fixed token count


class Chunk(BaseModel):
    """A text chunk for embedding and retrieval.

    Attributes:
        id: Unique chunk identifier.
        doc_id: Parent document ID.
        chunk_index: Position within document.
        content: Chunk text content.
        start_char: Start character offset in source.
        end_char: End character offset in source.
        token_count: Estimated token count.
        strategy: Chunking strategy used.
    """

    id: int | None = None
    doc_id: str
    chunk_index: int
    content: str
    start_char: int = 0
    end_char: int = 0
    token_count: int = 0
    strategy: ChunkingStrategy = ChunkingStrategy.PARAGRAPH


class ContextRequest(BaseModel):
    """Request for RAG context generation.

    Attributes:
        prompt: User prompt to contextualize.
        max_tokens: Maximum tokens for context.
        top_k: Number of chunks to retrieve.
        doc_types: Filter by document types.
        sanitize: Whether to sanitize PII.
    """

    prompt: str
    max_tokens: int = 4000
    top_k: int = 10
    doc_types: list[str] | None = None
    sanitize: bool = True


class RAGContext(BaseModel):
    """Generated RAG context for LLM prompt.

    Attributes:
        context: Formatted context string.
        chunks_used: Number of chunks included.
        tokens_used: Estimated token count.
        sources: List of source document IDs.
        sanitized: Whether PII was sanitized.
    """

    context: str
    chunks_used: int = 0
    tokens_used: int = 0
    sources: list[str] = Field(default_factory=list)
    sanitized: bool = False

    def with_prompt(self, prompt: str) -> str:
        """Combine context with user prompt.

        Args:
            prompt: User's original prompt.

        Returns:
            Full prompt with context prepended.
        """
        if not self.context:
            return prompt
        return f"## Relevant Context\n\n{self.context}\n\n---\n\n## Your Task\n\n{prompt}"
