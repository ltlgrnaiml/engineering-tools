"""Context Builder - SPEC-0043-RA01, RA02, RA03, RA04.

Build RAG context from search results with token budget management.
"""

import time
from dataclasses import dataclass, field

from gateway.services.knowledge.sanitizer import Sanitizer
from gateway.services.knowledge.search_service import SearchHit, SearchService


@dataclass
class ContextResult:
    """Result of context building."""
    context: str
    sources: list[dict] = field(default_factory=list)
    token_count: int = 0
    cached: bool = False


class ContextBuilder:
    """Build sanitized RAG context from search results."""

    CHARS_PER_TOKEN = 4  # Rough approximation
    DEFAULT_MAX_TOKENS = 4000
    CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(
        self,
        search: SearchService,
        sanitizer: Sanitizer | None = None,
        cache_enabled: bool = True
    ):
        self.search = search
        self.sanitizer = sanitizer or Sanitizer()
        self.cache_enabled = cache_enabled
        self._cache: dict[str, tuple[ContextResult, float]] = {}

    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count from text length."""
        return len(text) // self.CHARS_PER_TOKEN

    def _fit_to_budget(
        self,
        results: list[SearchHit],
        max_tokens: int
    ) -> list[SearchHit]:
        """Keep chunks until budget exhausted (SPEC-0043-RA03).

        Chunks are already sorted by relevance score.
        """
        total = 0
        selected = []
        for hit in results:
            tokens = self._estimate_tokens(hit.snippet)
            if total + tokens > max_tokens:
                break
            selected.append(hit)
            total += tokens
        return selected

    def _get_cached(self, cache_key: str) -> ContextResult | None:
        """Get cached result if valid."""
        if not self.cache_enabled:
            return None
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.CACHE_TTL_SECONDS:
                result.cached = True
                return result
            del self._cache[cache_key]
        return None

    def _set_cached(self, cache_key: str, result: ContextResult):
        """Cache a result."""
        if self.cache_enabled:
            self._cache[cache_key] = (result, time.time())

    def build_context(
        self,
        query: str,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        top_k: int = 10
    ) -> ContextResult:
        """Build sanitized context for RAG (SPEC-0043-RA01).

        1. Search for relevant documents
        2. Sanitize content (GUARDRAIL)
        3. Build context within token budget
        4. Return with source attribution
        """
        # Check cache
        cache_key = f"{query}:{max_tokens}:{top_k}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # Search for relevant content
        results = self.search.hybrid_search(query, query_vector=None, top_k=top_k)

        if not results:
            return ContextResult(
                context="No relevant context found.",
                sources=[],
                token_count=0
            )

        # Build context within budget
        context_parts = []
        sources = []
        total_tokens = 0
        header_tokens = self._estimate_tokens("## Relevant Context\n\n")
        total_tokens += header_tokens

        for hit in results:
            # Sanitize content (GUARDRAIL: ALL content sanitized before LLM)
            sanitized = self.sanitizer.sanitize_for_llm(hit.snippet)

            # Format chunk with source
            chunk = f"### {hit.title}\n{sanitized}\n\n"
            chunk_tokens = self._estimate_tokens(chunk)

            if total_tokens + chunk_tokens > max_tokens:
                break

            context_parts.append(chunk)
            sources.append({
                'doc_id': hit.doc_id,
                'title': hit.title,
                'score': hit.score
            })
            total_tokens += chunk_tokens

        context = "## Relevant Context\n\n" + "".join(context_parts)

        result = ContextResult(
            context=context,
            sources=sources,
            token_count=total_tokens,
            cached=False
        )

        self._set_cached(cache_key, result)
        return result

    def clear_cache(self):
        """Clear the context cache."""
        self._cache.clear()
