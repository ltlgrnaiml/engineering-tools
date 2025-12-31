"""Tests for Archive Service - PLAN-002 M1."""

import pytest
import sqlite3
from pathlib import Path

from shared.contracts.knowledge.archive import Document, DocumentType
from gateway.services.knowledge.database import SCHEMA
from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.parsers import parse_markdown_document
from gateway.services.knowledge.exporter import export_document


@pytest.fixture
def db_conn():
    """In-memory database for testing."""
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    # Apply schema
    conn.executescript(SCHEMA)
    return conn


@pytest.fixture
def archive(db_conn):
    return ArchiveService(db_conn)


def test_upsert_document(archive):
    """Test document insert and update."""
    doc = Document(
        id='test_001',
        type=DocumentType.SESSION,
        title='Test Document',
        content='# Test\n\nContent here.',
        file_path='.sessions/test.md',
        file_hash='abc123'
    )

    # First insert
    assert archive.upsert_document(doc) is True

    # Same hash - no change
    assert archive.upsert_document(doc) is False

    # Updated content
    doc.file_hash = 'def456'
    assert archive.upsert_document(doc) is True


def test_soft_delete(archive):
    """Test that archive_document uses soft delete, not hard delete."""
    doc = Document(
        id='test_soft',
        type=DocumentType.SESSION,
        title='Soft Delete Test',
        content='Content',
        file_path='.sessions/soft.md',
        file_hash='soft123'
    )
    archive.upsert_document(doc)

    # Archive (soft delete)
    assert archive.archive_document('test_soft') is True

    # Should not appear in list
    docs = archive.list_documents()
    assert not any(d.id == 'test_soft' for d in docs)

    # But still exists in database (soft deleted)
    row = archive.conn.execute(
        "SELECT * FROM documents WHERE id = ?", ('test_soft',)
    ).fetchone()
    assert row is not None
    assert row['archived_at'] is not None


def test_export_roundtrip():
    """Test that export produces identical content."""
    original_content = '# Test\n\nThis is test content.'
    doc = Document(
        id='roundtrip',
        type=DocumentType.SESSION,
        title='Roundtrip Test',
        content=original_content,
        file_path='.sessions/roundtrip.md',
        file_hash='rt123'
    )

    exported = export_document(doc)
    assert exported == original_content


def test_list_documents_by_type(archive):
    """Test filtering documents by type."""
    docs = [
        Document(id='session1', type=DocumentType.SESSION, title='S1',
                 content='c', file_path='.sessions/s1.md', file_hash='h1'),
        Document(id='adr1', type=DocumentType.ADR, title='A1',
                 content='c', file_path='.adrs/a1.json', file_hash='h2'),
    ]
    for d in docs:
        archive.upsert_document(d)

    # Filter by session
    sessions = archive.list_documents(DocumentType.SESSION)
    assert len(sessions) == 1
    assert sessions[0].id == 'session1'

    # Filter by ADR
    adrs = archive.list_documents(DocumentType.ADR)
    assert len(adrs) == 1
    assert adrs[0].id == 'adr1'


def test_get_document(archive):
    """Test getting a single document."""
    doc = Document(
        id='get_test',
        type=DocumentType.PLAN,
        title='Get Test',
        content='Content',
        file_path='.plans/test.md',
        file_hash='get123'
    )
    archive.upsert_document(doc)

    # Get existing
    result = archive.get_document('get_test')
    assert result is not None
    assert result.title == 'Get Test'

    # Get non-existing
    result = archive.get_document('nonexistent')
    assert result is None
