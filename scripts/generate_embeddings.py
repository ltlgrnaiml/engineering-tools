#!/usr/bin/env python
"""Generate embeddings for all chunks in knowledge database."""

from gateway.services.knowledge.database import get_connection
from gateway.services.knowledge.embedding_service import EmbeddingService


def main():
    print("Connecting to knowledge database...")
    conn = get_connection()

    # Check current state
    chunks = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    embeddings = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    print(f"Current state: {chunks} chunks, {embeddings} embeddings")

    if embeddings >= chunks:
        print("All chunks already have embeddings!")
        return

    print("\nInitializing embedding service (downloading model if needed)...")
    embedder = EmbeddingService()

    def progress(done, total):
        pct = (done / total) * 100
        print(f"  Progress: {done}/{total} ({pct:.1f}%)")

    print("Generating embeddings...")
    count = embedder.embed_all_chunks(conn, progress_callback=progress)
    print(f"\nGenerated {count} embeddings")

    # Verify
    final = conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]
    print(f"Total embeddings in database: {final}")

    conn.close()
    print("\nEmbedding generation complete!")

if __name__ == "__main__":
    main()
