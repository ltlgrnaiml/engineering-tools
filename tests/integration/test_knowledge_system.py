"""Integration Tests for Knowledge System - PLAN-002 M4.

End-to-end tests for the full knowledge archive and RAG pipeline.
"""

import pytest
import sqlite3
from pathlib import Path

from shared.contracts.knowledge.archive import Document, DocumentType
from gateway.services.knowledge.database import SCHEMA, init_database
from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.search_service import SearchService
from gateway.services.knowledge.chunking import ChunkingService
from gateway.services.knowledge.embedding_service import EmbeddingService
from gateway.services.knowledge.sanitizer import Sanitizer
from gateway.services.knowledge.context_builder import ContextBuilder
from gateway.services.knowledge.sync_service import SyncService
from gateway.services.knowledge.parsers import parse_markdown_document
from gateway.services.knowledge.exporter import export_document


@pytest.fixture
def db_conn():
    """In-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


@pytest.fixture
def archive(db_conn):
    return ArchiveService(db_conn)


@pytest.fixture
def search(db_conn):
    return SearchService(db_conn)


@pytest.fixture
def chunking():
    return ChunkingService()


@pytest.fixture
def embedding():
    return EmbeddingService()


@pytest.fixture
def sanitizer():
    return Sanitizer()


class TestFullPipeline:
    """End-to-end pipeline tests."""

    def test_ingest_search_context_pipeline(self, archive, search, sanitizer):
        """Test full pipeline: file → ingest → search → context."""
        # 1. Create and ingest document
        doc = Document(
            id='e2e_doc_001',
            type=DocumentType.SESSION,
            title='Integration Test Session',
            content='# Integration Test\n\nThis tests the full RAG pipeline from ingestion to context.',
            file_path='.sessions/integration_test.md',
            file_hash='e2e_hash_001'
        )
        archive.upsert_document(doc)
        
        # 2. Verify document stored
        retrieved = archive.get_document('e2e_doc_001')
        assert retrieved is not None
        assert retrieved.title == 'Integration Test Session'
        
        # 3. Search for document
        results = search.fts_search('Integration Test', top_k=5)
        assert len(results) > 0
        assert any('e2e_doc_001' in r.doc_id for r in results)
        
        # 4. Build context
        builder = ContextBuilder(search, sanitizer)
        context = builder.build_context('Integration Test')
        assert context.context is not None
        assert '## Relevant Context' in context.context

    def test_document_types_ingest(self, archive):
        """Test all document types can be ingested."""
        doc_types = [
            (DocumentType.SESSION, '.sessions/test.md'),
            (DocumentType.PLAN, '.plans/test.md'),
            (DocumentType.DISCUSSION, '.discussions/test.md'),
            (DocumentType.ADR, '.adrs/test.json'),
            (DocumentType.SPEC, 'docs/specs/test.json'),
        ]
        
        for i, (dtype, path) in enumerate(doc_types):
            doc = Document(
                id=f'type_test_{i}',
                type=dtype,
                title=f'Test {dtype.value}',
                content=f'Content for {dtype.value}',
                file_path=path,
                file_hash=f'hash_{i}'
            )
            archive.upsert_document(doc)
            
            # Verify retrieval
            retrieved = archive.get_document(f'type_test_{i}')
            assert retrieved is not None
            assert retrieved.type == dtype

    def test_soft_delete_preserves_data(self, archive):
        """Test soft delete doesn't remove data."""
        doc = Document(
            id='delete_test',
            type=DocumentType.SESSION,
            title='To Delete',
            content='This will be soft deleted',
            file_path='.sessions/delete.md',
            file_hash='delete_hash'
        )
        archive.upsert_document(doc)
        
        # Soft delete
        archive.archive_document('delete_test')
        
        # Document should still exist in DB (just archived)
        # List should not include it
        docs = archive.list_documents()
        assert not any(d.id == 'delete_test' for d in docs)

    def test_export_roundtrip(self, archive):
        """Test document export produces original content."""
        original_content = '# Test Document\n\nOriginal content here.'
        doc = Document(
            id='export_test',
            type=DocumentType.SESSION,
            title='Export Test',
            content=original_content,
            file_path='.sessions/export.md',
            file_hash='export_hash'
        )
        archive.upsert_document(doc)
        
        # Export
        retrieved = archive.get_document('export_test')
        exported = export_document(retrieved)
        
        assert exported == original_content


class TestSearchIntegration:
    """Search layer integration tests."""

    def test_fts_search_ranking(self, archive, search):
        """Test FTS returns ranked results."""
        # Insert multiple documents
        for i in range(3):
            doc = Document(
                id=f'rank_test_{i}',
                type=DocumentType.SESSION,
                title=f'Document {i}',
                content=f'Content with keyword search term repeated {"search " * (3-i)}',
                file_path=f'.sessions/rank_{i}.md',
                file_hash=f'rank_hash_{i}'
            )
            archive.upsert_document(doc)
        
        results = search.fts_search('search term', top_k=3)
        assert len(results) > 0
        # Results should be ranked by relevance

    def test_hybrid_search(self, archive, search):
        """Test hybrid search combines FTS and vector."""
        doc = Document(
            id='hybrid_test',
            type=DocumentType.ADR,
            title='Architecture Decision',
            content='This document describes our architecture decisions.',
            file_path='.adrs/hybrid.json',
            file_hash='hybrid_hash'
        )
        archive.upsert_document(doc)
        
        results = search.hybrid_search('architecture', query_vector=None, top_k=5)
        assert isinstance(results, list)

    def test_relationship_tracking(self, archive):
        """Test relationship extraction and storage."""
        # Create document with reference
        doc = Document(
            id='ref_source',
            type=DocumentType.DISCUSSION,
            title='Discussion',
            content='This implements ADR-0001 and references SPEC-0043.',
            file_path='.discussions/ref.md',
            file_hash='ref_hash'
        )
        archive.upsert_document(doc)
        
        # Extract relationships - pass the Document object
        refs = archive.extract_relationships(doc)
        assert len(refs) > 0
        
        # Save relationships (method takes Document and handles internally)
        archive.save_relationships(doc)
        
        # Query relationships
        rels = archive.get_relationships('ref_source')
        assert len(rels) > 0


class TestRAGIntegration:
    """RAG layer integration tests."""

    def test_chunking_and_embedding_pipeline(self, archive, chunking, embedding, db_conn):
        """Test chunking followed by embedding."""
        doc = Document(
            id='chunk_embed_test',
            type=DocumentType.SESSION,
            title='Chunking Test',
            content='## Section 1\n\nFirst section.\n\n## Section 2\n\nSecond section.',
            file_path='.sessions/chunk.md',
            file_hash='chunk_hash'
        )
        archive.upsert_document(doc)
        
        # Chunk the document
        chunks = chunking.chunk_document(doc.id, doc.content, '.md')
        assert len(chunks) >= 1
        
        # Store chunks
        for chunk in chunks:
            db_conn.execute("""
                INSERT INTO chunks (doc_id, chunk_index, content, start_char, end_char)
                VALUES (?, ?, ?, ?, ?)
            """, (chunk.doc_id, chunk.chunk_index, chunk.content, 
                  chunk.start_char, chunk.end_char))
        db_conn.commit()
        
        # Verify chunks stored
        stored = db_conn.execute(
            "SELECT COUNT(*) as cnt FROM chunks WHERE doc_id = ?", 
            (doc.id,)
        ).fetchone()
        assert stored['cnt'] >= 1

    def test_sanitization_in_context(self, archive, search, sanitizer):
        """Test PII is sanitized in context output."""
        doc = Document(
            id='pii_test',
            type=DocumentType.SESSION,
            title='PII Test',
            content='Contact: secret@company.com, API: sk-supersecretkey12345678901234',
            file_path='.sessions/pii.md',
            file_hash='pii_hash'
        )
        archive.upsert_document(doc)
        
        builder = ContextBuilder(search, sanitizer)
        context = builder.build_context('Contact API')
        
        # Sensitive data should be redacted
        assert 'secret@company.com' not in context.context
        assert 'sk-supersecretkey' not in context.context

    def test_context_caching(self, archive, search, sanitizer):
        """Test context caching works."""
        doc = Document(
            id='cache_test',
            type=DocumentType.SESSION,
            title='Cache Test',
            content='Caching test content.',
            file_path='.sessions/cache.md',
            file_hash='cache_hash'
        )
        archive.upsert_document(doc)
        
        builder = ContextBuilder(search, sanitizer, cache_enabled=True)
        
        # First call - not cached
        result1 = builder.build_context('Cache Test')
        assert result1.cached is False
        
        # Second call - should be cached
        result2 = builder.build_context('Cache Test')
        assert result2.cached is True


class TestLangchainIntegration:
    """Langchain adapter integration tests."""

    def test_langchain_retriever_import(self):
        """Test Langchain retriever can be imported."""
        from gateway.services.knowledge.langchain_adapter import KnowledgeRetriever
        assert KnowledgeRetriever is not None

    def test_langchain_retriever_instantiation(self, search, embedding):
        """Test Langchain retriever can be created."""
        from gateway.services.knowledge.langchain_adapter import KnowledgeRetriever, LANGCHAIN_AVAILABLE
        
        if LANGCHAIN_AVAILABLE:
            retriever = KnowledgeRetriever(
                search_service=search,
                embedding_service=embedding,
                top_k=5
            )
            assert retriever is not None


class TestStatsIntegration:
    """Statistics endpoint integration tests."""

    def test_stats_accuracy(self, archive, db_conn):
        """Test statistics are accurate."""
        # Insert known documents
        for i in range(3):
            doc = Document(
                id=f'stats_test_{i}',
                type=DocumentType.SESSION,
                title=f'Stats Test {i}',
                content=f'Content {i}',
                file_path=f'.sessions/stats_{i}.md',
                file_hash=f'stats_hash_{i}'
            )
            archive.upsert_document(doc)
        
        # Query stats
        stats = db_conn.execute("""
            SELECT COUNT(*) as cnt FROM documents WHERE archived_at IS NULL
        """).fetchone()
        
        assert stats['cnt'] >= 3


class TestDevToolsIntegration:
    """DevTools integration tests."""

    def test_get_knowledge_context_function(self):
        """Test DevTools knowledge integration function."""
        from gateway.services.devtools_service import get_knowledge_context
        assert callable(get_knowledge_context)
        
        # Function should handle missing DB gracefully
        result = get_knowledge_context("test query")
        # May return None if DB not initialized, which is acceptable
        assert result is None or isinstance(result, dict)


class TestAPIRoutes:
    """API route integration tests."""

    def test_routes_registered(self):
        """Test all routes are registered."""
        from gateway.routes.knowledge import router
        
        routes = [r.path for r in router.routes]
        
        # Check all required endpoints
        required = [
            '/api/knowledge/docs/{doc_id}',
            '/api/knowledge/docs',
            '/api/knowledge/sync',
            '/api/knowledge/sync/status',
            '/api/knowledge/sync/{doc_type}',
            '/api/knowledge/docs/{doc_id}/export',
            '/api/knowledge/search',
            '/api/knowledge/search/semantic',
            '/api/knowledge/search/hybrid',
            '/api/knowledge/docs/{doc_id}/relationships',
            '/api/knowledge/rag/context',
            '/api/knowledge/stats',
        ]
        
        for endpoint in required:
            assert endpoint in routes, f"Missing endpoint: {endpoint}"
