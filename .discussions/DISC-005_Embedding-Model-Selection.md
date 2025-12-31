# DISC-005: Embedding Model Selection

**Status**: resolved  
**Created**: 2025-12-30  
**Author**: AI-Assisted  
**Depends On**: DISC-002

---

## Summary

Select an embedding model for semantic search in the RAG system, balancing quality, speed, and resource usage.

---

## Context

Need embeddings for:

- ADRs, SPECs, DISCs (markdown/JSON)
- Python code and docstrings
- Contract schemas

Must run locally (no API calls per query) for speed and cost.

---

## Candidates

| Model | Dim | Size | Quality | Speed |
|-------|-----|------|---------|-------|
| all-MiniLM-L6-v2 | 384 | 80MB | Good | Fast |
| all-mpnet-base-v2 | 768 | 420MB | Better | Medium |
| bge-small-en-v1.5 | 384 | 130MB | Good | Fast |
| nomic-embed-text-v1.5 | 768 | 550MB | Best | Slow |
| CodeBERT | 768 | 500MB | Best (code) | Slow |

---

## Evaluation Criteria

1. **Retrieval Quality**: Relevant chunks ranked highly
2. **Code Understanding**: Semantic similarity for Python
3. **Latency**: <100ms per query
4. **Memory**: <1GB loaded
5. **Maintenance**: Active development, good docs

---

## Decision

**Primary Model: all-mpnet-base-v2**

| Setting | Value | Rationale |
|---------|-------|----------|
| Primary Model | **all-mpnet-base-v2** | Best quality/speed balance |
| Fallback Model | **all-MiniLM-L6-v2** | Resource-constrained environments |
| Dimensions | 768 (primary), 384 (fallback) | Industry standard |
| Search Strategy | **Hybrid (BM25 + Vectors)** | Best retrieval quality |

**Hybrid Search Rationale**:
- BM25 excels at exact keyword matches (function names, error codes)
- Vector search excels at semantic similarity (concepts, intent)
- Combined approach covers both use cases

**Implementation**:
```python
def hybrid_search(query: str, top_k: int = 10) -> list[Chunk]:
    # Keyword search
    bm25_results = fts_search(query, top_k=top_k * 2)
    
    # Semantic search
    vector_results = vector_search(embed(query), top_k=top_k * 2)
    
    # Reciprocal Rank Fusion
    return rrf_merge(bm25_results, vector_results, top_k=top_k)
```

---

## Deferred Decisions

| Decision | Reason | Revisit When |
|----------|--------|-------------|
| Separate code model | Optimize after MVP | If code retrieval <80% accuracy |
| Fine-tuning | Need usage data | After 1000+ queries logged |
| Quantization | Memory not yet an issue | If >2GB memory usage |

---

## Open Questions

1. ~~Separate model for code vs docs?~~ → **No (start simple, optimize later)**
2. ~~Fine-tune on project corpus?~~ → **Deferred**
3. ~~Hybrid search (embeddings + BM25)?~~ → **Yes (RRF merge)**
4. ~~Quantization for smaller footprint?~~ → **Deferred**

---

## Next Steps

- [x] Decision: all-mpnet-base-v2 as primary ✅
- [x] Decision: Hybrid search with RRF ✅
- [ ] Implement embedding service
- [ ] Implement hybrid search in knowledge.db
- [ ] Benchmark retrieval accuracy

