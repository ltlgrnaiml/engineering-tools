"""Analyze knowledge.db for ADR/SPEC relationship audit.

This script extracts all documents and relationships from the knowledge
database to support semantic evaluation of ADR↔SPEC connections.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("workspace/knowledge.db")


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get document counts by type
    cursor.execute("SELECT type, COUNT(*) as cnt FROM documents GROUP BY type")
    print("=" * 60)
    print("Documents by type:")
    print("=" * 60)
    for row in cursor.fetchall():
        print(f"  {row['type']}: {row['cnt']}")

    # Get total relationships
    cursor.execute(
        "SELECT relationship_type, COUNT(*) as cnt FROM relationships GROUP BY relationship_type"
    )
    print("\n" + "=" * 60)
    print("Relationships by type:")
    print("=" * 60)
    for row in cursor.fetchall():
        print(f"  {row['relationship_type']}: {row['cnt']}")

    # Get all ADR documents
    cursor.execute("SELECT id, title, file_path FROM documents WHERE type = 'adr'")
    adrs = cursor.fetchall()
    print(f"\n{'=' * 60}")
    print(f"ADRs in database: {len(adrs)}")
    print("=" * 60)
    for row in adrs:
        print(f"  {row['id']}: {row['title'][:50]}...")

    # Get all SPEC documents
    cursor.execute("SELECT id, title, file_path FROM documents WHERE type = 'spec'")
    specs = cursor.fetchall()
    print(f"\n{'=' * 60}")
    print(f"SPECs in database: {len(specs)}")
    print("=" * 60)
    for row in specs:
        print(f"  {row['id']}: {row['title'][:50]}...")

    # Get all relationships
    cursor.execute("""
        SELECT 
            r.source_id,
            r.target_id,
            r.relationship_type,
            s.type as source_type,
            t.type as target_type
        FROM relationships r
        LEFT JOIN documents s ON r.source_id = s.id
        LEFT JOIN documents t ON r.target_id = t.id
        ORDER BY r.relationship_type, r.source_id
    """)
    rels = cursor.fetchall()
    print(f"\n{'=' * 60}")
    print(f"All relationships: {len(rels)}")
    print("=" * 60)
    for row in rels:
        print(f"  [{row['relationship_type']}] {row['source_id']} -> {row['target_id']}")

    conn.close()


if __name__ == "__main__":
    main()
