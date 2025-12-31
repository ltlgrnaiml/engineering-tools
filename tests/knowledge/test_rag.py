"""Tests for RAG components - PLAN-002 M3b + M4."""

import sqlite3

import pytest

from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.context_builder import ContextBuilder
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
            id='doc_001',
            type=DocumentType.SESSION,
            title='Test Session',
            content='# Test Session\n\nContact: test@example.com for help.',
            file_path='.sessions/test.md',
            file_hash='hash1'
        ),
        Document(
            id='doc_002',
            type=DocumentType.ADR,
            title='Architecture Decision',
            content='# ADR-0001\n\nUsing sk-secret12345678901234567890 key.',
            file_path='.adrs/adr-0001.md',
            file_hash='hash2'
        ),
    ]
    for doc in docs:
        archive.upsert_document(doc)
    return docs


class TestSanitizer:
    """Tests for PII Sanitizer."""

    def test_sanitize_email(self):
        """Test email redaction."""
        sanitizer = Sanitizer()
        result = sanitizer.sanitize("Contact me at john@company.com please")
        assert '[EMAIL]' in result.content
        assert 'john@company.com' not in result.content
        assert result.redaction_count == 1

    def test_sanitize_api_key(self):
        """Test API key redaction."""
        sanitizer = Sanitizer()
        result = sanitizer.sanitize("Key: sk-abc123def456ghi789jkl012mno345")
        assert '[API_KEY]' in result.content
        assert 'sk-abc123' not in result.content

    def test_sanitize_multiple(self):
        """Test multiple redactions."""
        sanitizer = Sanitizer()
        text = "Email: user@corp.com, API: sk-test12345678901234567890"
        result = sanitizer.sanitize(text)
        assert '[EMAIL]' in result.content
        assert '[API_KEY]' in result.content
        assert result.redaction_count == 2

    def test_allowlist_preserved(self):
        """Test that allowlisted items are not redacted."""
        sanitizer = Sanitizer()
        result = sanitizer.sanitize("Contact test@test.com for testing")
        # test@test.com is in allowlist
        assert 'test@test.com' in result.content or result.redaction_count == 0

    def test_sanitize_for_llm(self):
        """Test convenience method."""
        sanitizer = Sanitizer()
        result = sanitizer.sanitize_for_llm("Email: user@corp.com")
        assert isinstance(result, str)
        assert '[EMAIL]' in result


class TestContextBuilder:
    """Tests for Context Builder."""

    def test_build_context_no_results(self, search):
        """Test context with no search results."""
        builder = ContextBuilder(search, Sanitizer())
        result = builder.build_context("nonexistent query xyz123")
        assert "No relevant context found" in result.context

    def test_build_context_with_results(self, search, sample_docs):
        """Test context building with results."""
        builder = ContextBuilder(search, Sanitizer())
        result = builder.build_context("Test Session")
        assert result.context is not None
        assert result.token_count >= 0

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


class TestLangchainAdapter:
    """Tests for Langchain Adapter."""

    def test_import(self):
        """Test that adapter can be imported."""
        from gateway.services.knowledge.langchain_adapter import KnowledgeRetriever
        assert KnowledgeRetriever is not None


class TestIntegration:
    """Integration tests."""

    def test_devtools_integration_import(self):
        """Test DevTools integration function exists."""
        from gateway.services.devtools_service import get_knowledge_context
        assert callable(get_knowledge_context)

    def test_routes_import(self):
        """Test routes can be imported."""
        from gateway.routes.knowledge import router
        routes = [r.path for r in router.routes]
        assert '/api/knowledge/rag/context' in routes
        assert '/api/knowledge/stats' in routes
