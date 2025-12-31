"""Database Schema and Initialization - SPEC-0043-AR01.

Per ADR-0047: SQLite database at workspace/knowledge.db.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("workspace/knowledge.db")

SCHEMA = """
-- Documents table (SPEC-0043-AR01)
CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    file_path TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    archived_at TEXT DEFAULT NULL
);

-- Chunks table (SPEC-0043-CH01)
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    start_char INTEGER,
    end_char INTEGER,
    token_count INTEGER,
    UNIQUE(doc_id, chunk_index)
);

-- Embeddings table (SPEC-0043-EM01)
CREATE TABLE IF NOT EXISTS embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chunk_id INTEGER NOT NULL REFERENCES chunks(id) ON DELETE CASCADE,
    vector BLOB NOT NULL,
    model TEXT NOT NULL,
    dimensions INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Relationships table (SPEC-0043-SE04)
CREATE TABLE IF NOT EXISTS relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL REFERENCES documents(id),
    target_id TEXT NOT NULL REFERENCES documents(id),
    relationship_type TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(source_id, target_id, relationship_type)
);

-- LLM Calls table (SPEC-0043-AR05)
CREATE TABLE IF NOT EXISTS llm_calls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp TEXT DEFAULT (datetime('now')),
    model TEXT NOT NULL,
    prompt TEXT,
    response TEXT,
    tokens_in INTEGER DEFAULT 0,
    tokens_out INTEGER DEFAULT 0,
    cost REAL DEFAULT 0.0
);

-- FTS5 virtual table for full-text search (SPEC-0043-SE01)
CREATE VIRTUAL TABLE IF NOT EXISTS content_fts USING fts5(
    title, content, doc_id UNINDEXED, content='documents', content_rowid='rowid'
);

-- Triggers for FTS sync
CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
    INSERT INTO content_fts(rowid, title, content, doc_id) VALUES (new.rowid, new.title, new.content, new.id);
END;

CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
    INSERT INTO content_fts(content_fts, rowid, title, content, doc_id) VALUES ('delete', old.rowid, old.title, old.content, old.id);
END;

CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
    INSERT INTO content_fts(content_fts, rowid, title, content, doc_id) VALUES ('delete', old.rowid, old.title, old.content, old.id);
    INSERT INTO content_fts(rowid, title, content, doc_id) VALUES (new.rowid, new.title, new.content, new.id);
END;

-- Updated_at trigger
CREATE TRIGGER IF NOT EXISTS update_documents_timestamp AFTER UPDATE ON documents BEGIN
    UPDATE documents SET updated_at = datetime('now') WHERE id = new.id;
END;

-- Indexes
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type);
CREATE INDEX IF NOT EXISTS idx_documents_archived ON documents(archived_at);
CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id ON embeddings(chunk_id);
"""


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_database() -> sqlite3.Connection:
    """Initialize database with schema."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    return conn
