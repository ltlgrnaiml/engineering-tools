"""Document Exporter - SPEC-0043-AR04.

Export documents back to file format.
"""

from pathlib import Path
from shared.contracts.knowledge.archive import Document


def export_document(doc: Document) -> str:
    """Export document to original format string."""
    return doc.content


def export_to_file(doc: Document, output_path: Path | None = None) -> Path:
    """Write document to file."""
    target = output_path or Path(doc.file_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(export_document(doc), encoding='utf-8')
    return target
