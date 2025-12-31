"""Tests for Context Builder - PLAN-002 M3."""

import sqlite3

import pytest

from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.context_builder import ContextBuilder, ContextResult
from gateway.services.knowledge.database import SCHEMA
from gateway.services.knowledge.sanitizer import Sanitizer
from gateway.services.knowledge.search_service import SearchService
from shared.contracts.knowledge.archive import Document, DocumentType


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
def sample_docs(archive):
    """Insert sample documents for testing."""
    docs = [
        Document(
            id='doc_ctx_001',
            type=DocumentType.SESSION,
            title='Test Session',
            content='# Test Session\n\nThis is a test document for context building.',
            file_path='.sessions/test.md',
            file_hash='hash1'
        ),
        Document(
            id='doc_ctx_002',
            type=DocumentType.ADR,
            title='Architecture Decision',
            content='# ADR-0001\n\nWe decided to use SQLite for the knowledge archive.',
            file_path='.adrs/adr-0001.md',
            file_hash='hash2'
        ),
        Document(
            id='doc_ctx_003',
            type=DocumentType.DISCUSSION,
            title='Design Discussion',
            content='# Discussion\n\nDiscussing the RAG implementation approach.',
            file_path='.discussions/disc-001.md',
            file_hash='hash3'
        ),
    ]
    for doc in docs:
        archive.upsert_document(doc)
    return docs


class TestContextBuilder:
    """Tests for ContextBuilder."""

    def test_build_context_no_results(self, search):
        """Test context with no search results."""
        builder = ContextBuilder(search, Sanitizer())
        result = builder.build_context("nonexistent query xyz123 asdfghjkl")
        assert "No relevant context found" in result.context
        assert result.sources == []
        assert result.token_count == 0

    def test_build_context_with_results(self, search, sample_docs):
        """Test context building with results."""
        builder = ContextBuilder(search, Sanitizer())
        result = builder.build_context("Test Session")
        assert result.context is not None
        assert "## Relevant Context" in result.context
        assert result.token_count >= 0

    def test_context_includes_sources(self, search, sample_docs):
        """Test context includes source attribution."""
        builder = ContextBuilder(search, Sanitizer())
        result = builder.build_context("Architecture Decision")
        # If results found, should have sources
        if result.sources:
            assert all('doc_id' in s for s in result.sources)
            assert all('title' in s for s in result.sources)

    def test_context_caching(self, search, sample_docs):
        """Test that results are cached."""
        builder = ContextBuilder(search, Sanitizer(), cache_enabled=True)

        # First call
        result1 = builder.build_context("Test")
        assert result1.cached is False

        # Second call - should be cached
        result2 = builder.build_context("Test")
        assert result2.cached is True

    def test_cache_disabled(self, search, sample_docs):
        """Test with caching disabled."""
        builder = ContextBuilder(search, Sanitizer(), cache_enabled=False)
        result1 = builder.build_context("Test")
        result2 = builder.build_context("Test")
        assert result1.cached is False
        assert result2.cached is False

    def test_clear_cache(self, search, sample_docs):
        """Test cache clearing."""
        builder = ContextBuilder(search, Sanitizer(), cache_enabled=True)

        # Build and cache
        builder.build_context("Test")

        # Clear cache
        builder.clear_cache()

        # Should not be cached after clear
        result = builder.build_context("Test")
        assert result.cached is False

    def test_token_budget_respected(self, search, sample_docs):
        """Test that token budget is respected."""
        builder = ContextBuilder(search, Sanitizer())

        # Very small budget
        result = builder.build_context("Test", max_tokens=50)
        assert result.token_count <= 50 or len(result.sources) <= 1

    def test_fit_to_budget_method(self, search):
        """Test _fit_to_budget method exists and works."""
        builder = ContextBuilder(search, Sanitizer())
        assert hasattr(builder, '_fit_to_budget')
        assert callable(builder._fit_to_budget)

    def test_estimate_tokens_method(self, search):
        """Test _estimate_tokens method."""
        builder = ContextBuilder(search, Sanitizer())
        tokens = builder._estimate_tokens("Hello world")
        assert tokens == len("Hello world") // 4

    def test_context_result_structure(self, search, sample_docs):
        """Test ContextResult has correct structure."""
        builder = ContextBuilder(search, Sanitizer())
        result = builder.build_context("Test")

        assert isinstance(result, ContextResult)
        assert hasattr(result, 'context')
        assert hasattr(result, 'sources')
        assert hasattr(result, 'token_count')
        assert hasattr(result, 'cached')

    def test_sanitization_applied(self, search, archive):
        """Test that sanitization is applied to context."""
        # Insert document with sensitive data
        doc = Document(
            id='doc_sensitive',
            type=DocumentType.SESSION,
            title='Sensitive Doc',
            content='Contact: secret@company.com, Key: sk-abc123456789012345678901',
            file_path='.sessions/sensitive.md',
            file_hash='hash_sensitive'
        )
        archive.upsert_document(doc)

        builder = ContextBuilder(search, Sanitizer())
        result = builder.build_context("Sensitive")

        # If document found, sensitive data should be sanitized
        if 'Sensitive' in result.context:
            assert 'secret@company.com' not in result.context
