"""Archive Service - SPEC-0043-AR03, AR06.

Document CRUD with soft delete semantics.
GUARDRAIL: No hard deletes - always use archived_at.
"""

import sqlite3

from gateway.services.knowledge.database import get_connection
from shared.contracts.knowledge.archive import Document, DocumentType


class ArchiveService:
    """Document archive with soft delete."""

    def __init__(self, conn: sqlite3.Connection | None = None):
        self.conn = conn or get_connection()

    def upsert_document(self, doc: Document) -> bool:
        """Insert or update document. Returns True if changed."""
        existing = self.conn.execute(
            "SELECT file_hash FROM documents WHERE id = ?", (doc.id,)
        ).fetchone()

        if existing and existing['file_hash'] == doc.file_hash:
            return False  # No change

        self.conn.execute("""
            INSERT INTO documents (id, type, title, content, file_path, file_hash)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title = excluded.title,
                content = excluded.content,
                file_hash = excluded.file_hash,
                archived_at = NULL
        """, (doc.id, doc.type.value, doc.title, doc.content, doc.file_path, doc.file_hash))
        self.conn.commit()
        return True

    def get_document(self, doc_id: str) -> Document | None:
        """Get document by ID."""
        row = self.conn.execute(
            "SELECT * FROM documents WHERE id = ? AND archived_at IS NULL", (doc_id,)
        ).fetchone()
        if not row:
            return None
        return Document(
            id=row['id'],
            type=DocumentType(row['type']),
            title=row['title'],
            content=row['content'],
            file_path=row['file_path'],
            file_hash=row['file_hash']
        )

    def list_documents(self, doc_type: DocumentType | None = None) -> list[Document]:
        """List all non-archived documents."""
        if doc_type:
            rows = self.conn.execute(
                "SELECT * FROM documents WHERE type = ? AND archived_at IS NULL",
                (doc_type.value,)
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM documents WHERE archived_at IS NULL"
            ).fetchall()
        return [
            Document(
                id=r['id'], type=DocumentType(r['type']), title=r['title'],
                content=r['content'], file_path=r['file_path'], file_hash=r['file_hash']
            )
            for r in rows
        ]

    def archive_document(self, doc_id: str) -> bool:
        """Soft delete document. GUARDRAIL: No hard deletes."""
        result = self.conn.execute(
            "UPDATE documents SET archived_at = datetime('now') WHERE id = ? AND archived_at IS NULL",
            (doc_id,)
        )
        self.conn.commit()
        return result.rowcount > 0

    def extract_relationships(self, doc: Document) -> list[tuple[str, str, str]]:
        """Extract document references from content.

        Returns list of (source_id, target_id, relationship_type).
        """
        import re
        relationships = []

        # Pattern for ADR, SPEC, DISC, PLAN references
        patterns = [
            (r'ADR-\d{4}', 'references'),
            (r'SPEC-\d{4}', 'references'),
            (r'DISC-\d{3}', 'references'),
            (r'PLAN-\d{3}', 'references'),
        ]

        for pattern, rel_type in patterns:
            matches = re.findall(pattern, doc.content)
            for match in matches:
                # Keep original ID format (e.g., ADR-0001, not adr_adr_0001)
                if match != doc.id:  # Don't self-reference
                    relationships.append((doc.id, match, rel_type))

        # Also check for explicit reference fields in JSON content
        try:
            import json
            data = json.loads(doc.content)

            # implements_adr (SPEC -> ADR)
            for adr_id in data.get('implements_adr', []):
                if adr_id != doc.id:
                    relationships.append((doc.id, adr_id, 'implements'))

            # resulting_specs (ADR -> SPEC)
            for spec in data.get('resulting_specs', []):
                spec_id = spec.get('id') if isinstance(spec, dict) else spec
                if spec_id and spec_id != doc.id:
                    relationships.append((doc.id, spec_id, 'creates'))

            # source_references (Plan -> ADR/SPEC)
            for ref in data.get('source_references', []):
                ref_id = ref.get('id') if isinstance(ref, dict) else ref
                if ref_id and ref_id != doc.id:
                    relationships.append((doc.id, ref_id, 'references'))

            # references array
            for ref in data.get('references', []):
                ref_id = ref.get('id') if isinstance(ref, dict) else ref
                if ref_id and ref_id != doc.id:
                    relationships.append((doc.id, ref_id, 'references'))

        except (json.JSONDecodeError, TypeError):
            pass  # Not JSON content, skip structured extraction

        # Deduplicate
        return list(set(relationships))

    def save_relationships(self, doc: Document):
        """Save extracted relationships to database.
        
        Skips relationships where target document doesn't exist in archive
        (FK constraint protection).
        """
        rels = self.extract_relationships(doc)
        for source, target, rel_type in rels:
            try:
                self.conn.execute("""
                    INSERT OR IGNORE INTO relationships (source_id, target_id, relationship_type)
                    VALUES (?, ?, ?)
                """, (source, target, rel_type))
            except Exception:
                # Skip if FK constraint fails (target doc not in archive)
                pass
        self.conn.commit()

    def get_relationships(self, doc_id: str) -> list[dict]:
        """Get all relationships for a document."""
        rows = self.conn.execute("""
            SELECT source_id, target_id, relationship_type
            FROM relationships
            WHERE source_id = ? OR target_id = ?
        """, (doc_id, doc_id)).fetchall()

        return [
            {'source': r['source_id'], 'target': r['target_id'], 'type': r['relationship_type']}
            for r in rows
        ]
