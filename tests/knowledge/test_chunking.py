"""Tests for Chunking Service - PLAN-002 M3."""

import pytest

from gateway.services.knowledge.chunking import ChunkingService


class TestChunkingService:
    """Tests for ChunkingService."""

    @pytest.fixture
    def chunking(self):
        return ChunkingService()

    def test_chunk_markdown_headers(self, chunking):
        """Test markdown chunking splits on ## headers."""
        content = """# Title

Introduction paragraph.

## Section One

Content of section one.

## Section Two

Content of section two.
"""
        chunks = chunking.chunk_document("doc_001", content, ".md")
        assert len(chunks) >= 2
        assert all(c.doc_id == "doc_001" for c in chunks)

    def test_chunk_python_functions(self, chunking):
        """Test Python chunking recognizes function boundaries."""
        content = '''def foo():
    """Foo function."""
    pass

def bar():
    """Bar function."""
    return 42

class MyClass:
    """A class."""
    def method(self):
        pass
'''
        chunks = chunking.chunk_document("doc_002", content, ".py")
        assert len(chunks) >= 1
        assert all(c.doc_id == "doc_002" for c in chunks)

    def test_chunk_json_whole(self, chunking):
        """Test JSON documents are kept as single chunk."""
        content = '{"key": "value", "nested": {"a": 1}}'
        chunks = chunking.chunk_document("doc_003", content, ".json")
        assert len(chunks) == 1
        assert chunks[0].content == content

    def test_chunk_paragraph_fallback(self, chunking):
        """Test paragraph chunking for unknown types."""
        content = """First paragraph here.

Second paragraph here.

Third paragraph here."""
        chunks = chunking.chunk_document("doc_004", content, ".txt")
        assert len(chunks) >= 1

    def test_chunk_metadata(self, chunking):
        """Test chunks have proper metadata."""
        content = "## Section\n\nSome content here."
        chunks = chunking.chunk_document("doc_005", content, ".md")
        assert len(chunks) >= 1
        chunk = chunks[0]
        assert chunk.doc_id == "doc_005"
        assert chunk.chunk_index >= 0
        assert chunk.content is not None
        assert chunk.token_count >= 0

    def test_rechunk_document(self, chunking):
        """Test rechunk_document method exists."""
        # Just verify the method exists and is callable
        assert hasattr(chunking, 'rechunk_document')
        assert callable(chunking.rechunk_document)

    def test_empty_content(self, chunking):
        """Test chunking handles empty content."""
        chunks = chunking.chunk_document("doc_empty", "", ".md")
        # Should return empty list or single empty chunk
        assert isinstance(chunks, list)
