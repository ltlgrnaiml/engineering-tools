"""Document Parsers - SPEC-0043-AR02.

Parse markdown and JSON files into Document format.
"""

import hashlib
import json
import re
from pathlib import Path

from shared.contracts.knowledge.archive import Document, DocumentType


def _compute_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _extract_markdown_title(content: str, filepath: Path) -> str:
    """Extract title from markdown heading or filename."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return filepath.stem.replace('_', ' ').replace('-', ' ').title()


def _detect_document_type(filepath: Path) -> DocumentType:
    """Detect document type from path."""
    path_str = str(filepath).lower()
    if '.sessions/' in path_str or '.sessions\\' in path_str:
        return DocumentType.SESSION
    elif '.plans/' in path_str or '.plans\\' in path_str:
        return DocumentType.PLAN
    elif '.discussions/' in path_str or '.discussions\\' in path_str:
        return DocumentType.DISCUSSION
    elif '.adrs/' in path_str or '.adrs\\' in path_str:
        return DocumentType.ADR
    elif 'specs/' in path_str or 'specs\\' in path_str:
        return DocumentType.SPEC
    elif 'contracts/' in path_str or 'contracts\\' in path_str:
        return DocumentType.CONTRACT
    return DocumentType.SESSION  # Default


def parse_markdown_document(filepath: Path) -> Document:
    """Parse markdown file into Document."""
    content = filepath.read_text(encoding='utf-8')
    title = _extract_markdown_title(content, filepath)
    doc_type = _detect_document_type(filepath)
    doc_id = f"{doc_type.value}_{_compute_hash(str(filepath))}"

    return Document(
        id=doc_id,
        type=doc_type,
        title=title,
        content=content,
        file_path=str(filepath),
        file_hash=_compute_hash(content)
    )


def parse_json_document(filepath: Path) -> Document:
    """Parse JSON file into Document."""
    content = filepath.read_text(encoding='utf-8')
    data = json.loads(content)
    title = data.get('title', data.get('name', filepath.stem))
    doc_type = _detect_document_type(filepath)
    doc_id = f"{doc_type.value}_{_compute_hash(str(filepath))}"

    return Document(
        id=doc_id,
        type=doc_type,
        title=title,
        content=content,
        file_path=str(filepath),
        file_hash=_compute_hash(content)
    )


def parse_document(filepath: Path) -> Document:
    """Parse any supported document type."""
    if filepath.suffix == '.json':
        return parse_json_document(filepath)
    return parse_markdown_document(filepath)
