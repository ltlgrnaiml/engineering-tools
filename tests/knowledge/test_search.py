"""Tests for Search Service - PLAN-002 M2."""

import pytest
import sqlite3

from shared.contracts.knowledge.archive import Document, DocumentType
from gateway.services.knowledge.database import SCHEMA
from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.search_service import SearchService


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
    """Insert sample documents for search testing."""
    docs = [
        Document(
            id='doc_001',
            type=DocumentType.SESSION,
            title='Python Development Session',
            content='# Python Development\n\nWorking on Python code with FastAPI.',
            file_path='.sessions/python.md',
            file_hash='hash1'
        ),
        Document(
            id='doc_002',
            type=DocumentType.ADR,
            title='Architecture Decision: Database',
            content='# ADR-0001\n\nUsing SQLite for local storage. References ADR-0002.',
            file_path='.adrs/adr-0001.md',
            file_hash='hash2'
        ),
    ]
    for doc in docs:
        archive.upsert_document(doc)
    return docs


def test_fts_search(search, sample_docs):
    """Test FTS search returns relevant results."""
    results = search.fts_search('Python', top_k=5)
    assert len(results) >= 1
    assert any('Python' in r.title or 'Python' in r.snippet for r in results)


def test_fts_no_results(search, sample_docs):
    """Test FTS with no matching query."""
    results = search.fts_search('NonexistentTerm12345', top_k=5)
    assert len(results) == 0


def test_hybrid_search_fts_only(search, sample_docs):
    """Test hybrid search falls back to FTS when no vector."""
    results = search.hybrid_search('SQLite', query_vector=None, top_k=5)
    assert len(results) >= 1


def test_relationship_extraction(archive):
    """Test that ADR references are extracted."""
    doc = Document(
        id='test_rel',
        type=DocumentType.SESSION,
        title='Relationship Test',
        content='This references ADR-0001 and SPEC-0043.',
        file_path='.sessions/rel.md',
        file_hash='relhash'
    )
    rels = archive.extract_relationships(doc)
    assert len(rels) == 2
    assert any('adr' in r[1] for r in rels)
    assert any('spec' in r[1] for r in rels)


def test_search_service_import():
    """Test SearchService can be imported."""
    from gateway.services.knowledge.search_service import SearchService
    assert SearchService is not None
