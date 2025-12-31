#!/usr/bin/env python
"""Sync knowledge database with project artifacts."""

from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.chunking import ChunkingService
from gateway.services.knowledge.database import init_database
from gateway.services.knowledge.sync_service import SyncService


def main():
    print("Initializing knowledge database...")
    conn = init_database()

    print("Creating services...")
    archive = ArchiveService(conn)
    sync = SyncService(archive)
    chunker = ChunkingService()

    print("Syncing documents from .adrs/, .discussions/, docs/specs/, etc...")
    count = sync.sync_all()
    print(f"Synced {count} documents")

    # Show what was synced
    cursor = conn.execute("SELECT type, COUNT(*) as cnt FROM documents GROUP BY type")
    print("\nDocuments by type:")
    for row in cursor:
        print(f"  - {row[0]}: {row[1]}")

    # Chunk all documents
    print("\nChunking documents...")
    docs = conn.execute("SELECT id, content, file_path FROM documents WHERE archived_at IS NULL").fetchall()
    total_chunks = 0
    for doc in docs:
        chunk_count = chunker.chunk_and_store(conn, doc['id'], doc['content'], doc['file_path'])
        total_chunks += chunk_count
    print(f"Created {total_chunks} chunks from {len(docs)} documents")

    conn.close()
    print("\nSync complete!")

if __name__ == "__main__":
    main()
