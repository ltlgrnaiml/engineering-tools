"""Enhanced RAG - Multi-level context building for workflow generation.

Implements:
- Level 1: Query Enhancement (expand query with artifact-specific terms)
- Level 2: LLM Re-ranking (use LLM to score relevance)
- Level 3: Graph-Aware Retrieval (traverse document relationships)

Per user request: Levels 1+2 are default, with LLM re-ranking as UI toggle.
"""

import logging
from dataclasses import dataclass, field

from gateway.services.knowledge.database import get_connection
from gateway.services.knowledge.sanitizer import Sanitizer
from gateway.services.knowledge.search_service import SearchHit, SearchService

logger = logging.getLogger(__name__)


# =============================================================================
# Level 1: Query Enhancement
# =============================================================================

ARTIFACT_QUERY_EXPANSIONS = {
    "discussion": "requirements design options tradeoffs stakeholders considerations",
    "adr": "architecture decision alternatives consequences rationale patterns",
    "spec": "API endpoints data model schema requirements validation",
    "plan": "milestones tasks dependencies verification implementation timeline",
}

DOC_TYPE_KEYWORDS = {
    "adr": "ADR architecture decision record pattern",
    "spec": "SPEC specification requirement",
    "discussion": "DISC discussion design",
    "plan": "PLAN implementation milestone task",
    "session": "SESSION progress work",
}


def enhance_query(query: str, artifact_type: str | None = None) -> str:
    """Expand query with relevant terms for better retrieval.
    
    Args:
        query: Original user query.
        artifact_type: Type of artifact being generated (discussion, adr, spec, plan).
        
    Returns:
        Enhanced query with additional relevant terms.
    """
    parts = [query]

    # Add artifact-specific terms
    if artifact_type:
        expansion = ARTIFACT_QUERY_EXPANSIONS.get(artifact_type.lower(), "")
        if expansion:
            parts.append(expansion)

    # Add general project terms
    parts.append("engineering-tools platform workflow")

    return " ".join(parts)


# =============================================================================
# Level 2: LLM Re-ranking
# =============================================================================

@dataclass
class RankedResult:
    """Result with LLM-assigned relevance score."""
    hit: SearchHit
    relevance_score: float
    relevance_reason: str


def rerank_with_llm(
    query: str,
    candidates: list[SearchHit],
    top_k: int = 5,
) -> list[RankedResult]:
    """Use LLM to re-rank search results by relevance.
    
    Args:
        query: Original search query.
        candidates: List of search hits to re-rank.
        top_k: Number of top results to return.
        
    Returns:
        List of RankedResult with LLM-assigned scores.
    """
    if not candidates:
        return []

    try:
        from pydantic import BaseModel

        from gateway.services.llm_service import generate_structured, is_available

        if not is_available():
            logger.warning("LLM not available for re-ranking, using original order")
            return [
                RankedResult(hit=h, relevance_score=h.score, relevance_reason="Original score")
                for h in candidates[:top_k]
            ]

        # Build candidate list for LLM
        candidate_text = "\n".join([
            f"[{i}] {h.title}: {h.snippet[:200]}..."
            for i, h in enumerate(candidates)
        ])

        class ScoredDoc(BaseModel):
            index: int
            score: float  # 0-10
            reason: str

        class ReRankResponse(BaseModel):
            rankings: list[ScoredDoc]

        prompt = f"""Rate each document's relevance to this query: "{query}"

Documents:
{candidate_text}

For each document, provide:
- index: The document number [0-{len(candidates)-1}]
- score: Relevance score from 0 (irrelevant) to 10 (highly relevant)
- reason: Brief explanation of relevance

Return the top {top_k} most relevant documents."""

        response = generate_structured(
            prompt=prompt,
            schema=ReRankResponse,
            system_prompt="You are a document relevance scorer for a software development project.",
        )

        if response.success and response.data:
            rankings = response.data.get("rankings", [])
            # Sort by score descending
            rankings.sort(key=lambda x: x.get("score", 0), reverse=True)

            results = []
            for r in rankings[:top_k]:
                idx = r.get("index", 0)
                if 0 <= idx < len(candidates):
                    results.append(RankedResult(
                        hit=candidates[idx],
                        relevance_score=r.get("score", 0),
                        relevance_reason=r.get("reason", ""),
                    ))
            return results

    except Exception as e:
        logger.warning(f"LLM re-ranking failed: {e}, using original order")

    # Fallback to original order
    return [
        RankedResult(hit=h, relevance_score=h.score, relevance_reason="Original score")
        for h in candidates[:top_k]
    ]


# =============================================================================
# Level 3: Graph-Aware Retrieval
# =============================================================================

def expand_with_graph(
    doc_ids: list[str],
    conn=None,
    max_hops: int = 1,
) -> list[str]:
    """Expand document set by traversing relationships.
    
    Args:
        doc_ids: Initial set of document IDs.
        conn: Database connection (optional).
        max_hops: Maximum relationship hops to follow.
        
    Returns:
        Expanded list of document IDs including related documents.
    """
    if conn is None:
        conn = get_connection()

    expanded = set(doc_ids)
    frontier = set(doc_ids)

    for _ in range(max_hops):
        if not frontier:
            break

        # Find all documents referenced by or referencing frontier
        placeholders = ",".join("?" * len(frontier))
        rows = conn.execute(f"""
            SELECT DISTINCT target_id FROM relationships 
            WHERE source_id IN ({placeholders})
            UNION
            SELECT DISTINCT source_id FROM relationships
            WHERE target_id IN ({placeholders})
        """, list(frontier) + list(frontier)).fetchall()

        new_docs = {r[0] for r in rows} - expanded
        expanded.update(new_docs)
        frontier = new_docs

    return list(expanded)


def get_related_documents(
    doc_ids: list[str],
    conn=None,
) -> list[dict]:
    """Get full document info for related documents.
    
    Args:
        doc_ids: List of document IDs to retrieve.
        conn: Database connection (optional).
        
    Returns:
        List of document dicts with id, title, type, content snippet.
    """
    if not doc_ids or conn is None:
        conn = get_connection()

    placeholders = ",".join("?" * len(doc_ids))
    rows = conn.execute(f"""
        SELECT id, title, type, substr(content, 1, 500) as snippet
        FROM documents
        WHERE id IN ({placeholders}) AND archived_at IS NULL
    """, doc_ids).fetchall()

    return [
        {"id": r["id"], "title": r["title"], "type": r["type"], "snippet": r["snippet"]}
        for r in rows
    ]


# =============================================================================
# Enhanced RAG Context Builder
# =============================================================================

@dataclass
class EnhancedRAGConfig:
    """Configuration for enhanced RAG."""
    use_query_enhancement: bool = True  # Level 1
    use_llm_reranking: bool = True      # Level 2 (UI toggle)
    use_graph_expansion: bool = True    # Level 3
    max_candidates: int = 20            # Initial retrieval count
    top_k: int = 5                      # Final context count
    max_tokens: int = 3000              # Token budget for context
    graph_hops: int = 1                 # Relationship hops


@dataclass
class EnhancedRAGResult:
    """Result from enhanced RAG context building."""
    context: str
    sources: list[dict] = field(default_factory=list)
    query_used: str = ""
    reranked: bool = False
    graph_expanded: bool = False
    token_estimate: int = 0


class EnhancedRAGBuilder:
    """Enhanced RAG context builder with multiple retrieval strategies."""

    CHARS_PER_TOKEN = 4

    def __init__(self, config: EnhancedRAGConfig | None = None):
        self.config = config or EnhancedRAGConfig()
        self._conn = None
        self._search = None
        self._sanitizer = None

    def _get_services(self):
        """Lazy-load services."""
        if self._conn is None:
            self._conn = get_connection()
            self._search = SearchService(self._conn)
            self._sanitizer = Sanitizer()
        return self._conn, self._search, self._sanitizer

    def build_context(
        self,
        query: str,
        artifact_type: str | None = None,
        config_override: EnhancedRAGConfig | None = None,
    ) -> EnhancedRAGResult:
        """Build enhanced context using all enabled strategies.
        
        Args:
            query: User's query/prompt.
            artifact_type: Type of artifact being generated.
            config_override: Override default config for this call.
            
        Returns:
            EnhancedRAGResult with context and metadata.
        """
        config = config_override or self.config
        conn, search, sanitizer = self._get_services()

        # Level 1: Query Enhancement
        if config.use_query_enhancement:
            enhanced_query = enhance_query(query, artifact_type)
        else:
            enhanced_query = query

        # Initial retrieval (hybrid search)
        candidates = search.hybrid_search(
            enhanced_query,
            query_vector=None,  # TODO: Add vector search
            top_k=config.max_candidates,
        )

        if not candidates:
            return EnhancedRAGResult(
                context="No relevant context found in knowledge archive.",
                query_used=enhanced_query,
            )

        # Level 2: LLM Re-ranking
        reranked = False
        if config.use_llm_reranking:
            ranked = rerank_with_llm(query, candidates, top_k=config.top_k)
            if ranked:
                candidates = [r.hit for r in ranked]
                reranked = True
        else:
            candidates = candidates[:config.top_k]

        # Level 3: Graph Expansion
        graph_expanded = False
        doc_ids = [h.doc_id for h in candidates]
        if config.use_graph_expansion:
            expanded_ids = expand_with_graph(doc_ids, conn, config.graph_hops)
            if len(expanded_ids) > len(doc_ids):
                # Get additional documents
                new_ids = [d for d in expanded_ids if d not in doc_ids]
                related = get_related_documents(new_ids, conn)
                graph_expanded = True

        # Build final context
        context_parts = ["## PROJECT CONTEXT (from Knowledge Archive)\n"]
        sources = []
        total_chars = 0
        max_chars = config.max_tokens * self.CHARS_PER_TOKEN

        for hit in candidates:
            sanitized = sanitizer.sanitize_for_llm(hit.snippet)
            chunk = f"### {hit.title} [{hit.doc_type.upper()}]\n{sanitized}\n\n"

            if total_chars + len(chunk) > max_chars:
                break

            context_parts.append(chunk)
            sources.append({
                "doc_id": hit.doc_id,
                "title": hit.title,
                "type": hit.doc_type,
                "score": hit.score,
            })
            total_chars += len(chunk)

        # Add graph-expanded context if available
        if graph_expanded and related:
            context_parts.append("### Related Documents\n")
            for doc in related[:3]:  # Limit to 3 related
                if total_chars > max_chars:
                    break
                snippet = f"- **{doc['title']}** ({doc['type']}): {doc['snippet'][:150]}...\n"
                context_parts.append(snippet)
                total_chars += len(snippet)

        return EnhancedRAGResult(
            context="".join(context_parts),
            sources=sources,
            query_used=enhanced_query,
            reranked=reranked,
            graph_expanded=graph_expanded,
            token_estimate=total_chars // self.CHARS_PER_TOKEN,
        )


# =============================================================================
# Convenience Functions
# =============================================================================

_default_builder: EnhancedRAGBuilder | None = None


def get_enhanced_rag_builder() -> EnhancedRAGBuilder:
    """Get or create the default enhanced RAG builder."""
    global _default_builder
    if _default_builder is None:
        _default_builder = EnhancedRAGBuilder()
    return _default_builder


def get_enhanced_context(
    query: str,
    artifact_type: str | None = None,
    use_reranking: bool = True,
) -> str:
    """Convenience function to get enhanced RAG context.
    
    Args:
        query: User's query/prompt.
        artifact_type: Type of artifact being generated.
        use_reranking: Whether to use LLM re-ranking (UI toggle).
        
    Returns:
        Formatted context string.
    """
    builder = get_enhanced_rag_builder()
    config = EnhancedRAGConfig(
        use_query_enhancement=True,
        use_llm_reranking=use_reranking,
        use_graph_expansion=True,
    )
    result = builder.build_context(query, artifact_type, config)
    return result.context
