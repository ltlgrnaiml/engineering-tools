"""Knowledge API Routes - SPEC-0043-API.

REST endpoints for knowledge archive.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse

from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.database import init_database
from gateway.services.knowledge.sync_service import SyncService
from shared.contracts.knowledge.archive import Document, DocumentType, SyncMode, SyncStatus

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# Dependency injection
def get_archive() -> ArchiveService:
    conn = init_database()
    return ArchiveService(conn)


def get_sync(archive: ArchiveService = Depends(get_archive)) -> SyncService:
    return SyncService(archive)


@router.get("/docs/{doc_id}", response_model=Document)
async def get_document(doc_id: str, archive: ArchiveService = Depends(get_archive)) -> Document:
    """Get document by ID (SPEC-0043-API04)."""
    doc = archive.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.get("/docs", response_model=list[Document])
async def list_documents(
    doc_type: str | None = None,
    archive: ArchiveService = Depends(get_archive)
) -> list[Document]:
    """List all documents, optionally filtered by type."""
    dtype = DocumentType(doc_type) if doc_type else None
    return archive.list_documents(dtype)


@router.post("/sync", response_model=SyncStatus)
async def force_sync(sync: SyncService = Depends(get_sync)) -> SyncStatus:
    """Force sync all documents (SPEC-0043-API06)."""
    count = sync.sync_all()
    return SyncStatus(mode=SyncMode.MANUAL, is_running=False, documents_synced=count)


@router.get("/sync/status", response_model=SyncStatus)
async def get_sync_status(sync: SyncService = Depends(get_sync)) -> SyncStatus:
    """Get sync status (SPEC-0043-API08)."""
    return sync.get_status()


@router.post("/sync/{doc_type}", response_model=SyncStatus)
async def sync_by_type(doc_type: str, sync: SyncService = Depends(get_sync)) -> SyncStatus:
    """Sync specific document type (SPEC-0043-API07)."""
    valid_types = ['session', 'plan', 'discussion', 'adr', 'spec', 'contract']
    if doc_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid type. Valid: {valid_types}")
    # Map type to path
    type_paths = {
        'session': '.sessions', 'plan': '.plans', 'discussion': '.discussions',
        'adr': '.adrs', 'spec': 'docs/specs', 'contract': 'shared/contracts'
    }
    count = sync.sync_path(Path(type_paths[doc_type]))
    return SyncStatus(mode=SyncMode.MANUAL, is_running=False, documents_synced=count)


@router.get("/docs/{doc_id}/export")
async def export_document_endpoint(doc_id: str, archive: ArchiveService = Depends(get_archive)) -> PlainTextResponse:
    """Export document to original format (SPEC-0043-API05)."""
    doc = archive.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    content_type = "application/json" if doc.type.value in ['adr', 'spec', 'plan'] else "text/markdown"
    return PlainTextResponse(content=doc.content, media_type=content_type)


from gateway.services.knowledge.search_service import SearchService


def get_search(archive: ArchiveService = Depends(get_archive)) -> SearchService:
    return SearchService(archive.conn)


@router.get("/search")
async def fts_search(
    q: str,
    top_k: int = 10,
    search: SearchService = Depends(get_search)
) -> list[dict]:
    """Full-text search (SPEC-0043-API01)."""
    results = search.fts_search(q, top_k)
    return [{'doc_id': r.doc_id, 'title': r.title, 'snippet': r.snippet, 'score': r.score} for r in results]


@router.get("/search/semantic")
async def semantic_search(
    q: str,
    top_k: int = 10,
    search: SearchService = Depends(get_search)
) -> list[dict]:
    """Semantic/vector search (SPEC-0043-API02)."""
    results = search.vector_search(q, top_k=top_k)
    return [{'doc_id': r.doc_id, 'title': r.title, 'snippet': r.snippet, 'score': r.score} for r in results]


@router.get("/search/hybrid")
async def hybrid_search(
    q: str,
    top_k: int = 10,
    search: SearchService = Depends(get_search)
) -> list[dict]:
    """Hybrid search - FTS + vector with RRF (SPEC-0043-API03)."""
    results = search.hybrid_search(q, query_vector=None, top_k=top_k)
    return [{'doc_id': r.doc_id, 'title': r.title, 'snippet': r.snippet, 'score': r.score} for r in results]


@router.get("/docs/{doc_id}/relationships")
async def get_relationships(
    doc_id: str,
    archive: ArchiveService = Depends(get_archive)
) -> list[dict]:
    """Get document relationships (SPEC-0043-API11)."""
    return archive.get_relationships(doc_id)


from gateway.services.knowledge.context_builder import ContextBuilder
from gateway.services.knowledge.sanitizer import Sanitizer


@router.get("/rag/context")
async def get_rag_context(
    q: str,
    max_tokens: int = 4000,
    top_k: int = 10,
    search: SearchService = Depends(get_search)
) -> dict:
    """Get RAG context for query (SPEC-0043-API10)."""
    builder = ContextBuilder(search, Sanitizer())
    result = builder.build_context(q, max_tokens=max_tokens, top_k=top_k)
    return {
        'context': result.context,
        'sources': result.sources,
        'token_count': result.token_count,
        'cached': result.cached
    }


@router.get("/stats")
async def get_stats(archive: ArchiveService = Depends(get_archive)) -> dict:
    """Get knowledge archive statistics (SPEC-0043-API09)."""
    # Documents by type
    type_rows = archive.conn.execute("""
        SELECT type, COUNT(*) as count
        FROM documents WHERE archived_at IS NULL
        GROUP BY type
    """).fetchall()
    docs_by_type = {r['type']: r['count'] for r in type_rows}

    # Aggregate stats
    stats = archive.conn.execute("""
        SELECT
            (SELECT COUNT(*) FROM documents WHERE archived_at IS NULL) as total_docs,
            (SELECT COUNT(*) FROM chunks) as total_chunks,
            (SELECT COUNT(*) FROM embeddings) as total_embeddings,
            (SELECT COALESCE(SUM(cost), 0) FROM llm_calls) as total_cost,
            (SELECT COUNT(*) FROM llm_calls) as llm_calls_count
    """).fetchone()

    return {
        'total_documents': stats['total_docs'],
        'documents_by_type': docs_by_type,
        'total_chunks': stats['total_chunks'],
        'total_embeddings': stats['total_embeddings'],
        'total_llm_cost': stats['total_cost'],
        'llm_calls_count': stats['llm_calls_count']
    }
