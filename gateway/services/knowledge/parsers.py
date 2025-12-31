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


def _extract_artifact_id(filepath: Path, content: str, doc_type: DocumentType) -> str:
    """Extract canonical artifact ID from file.
    
    Per SPEC-0043-AR02: IDs should match artifact naming conventions
    (ADR-XXXX, SPEC-XXXX, DISC-XXX, PLAN-XXX, SESSION_XXX).
    
    Priority:
    1. JSON 'id' field (for ADR/SPEC)
    2. Filename pattern match (DISC-001, PLAN-001, etc.)
    3. Fallback to hashed ID
    """
    # Try JSON id field first
    if filepath.suffix == '.json':
        try:
            data = json.loads(content)
            if 'id' in data:
                return data['id']
        except json.JSONDecodeError:
            pass

    # Try filename pattern for known types
    filename = filepath.stem
    patterns = [
        r'^(ADR-\d{4})',      # ADR-0001
        r'^(SPEC-\d{4})',     # SPEC-0001
        r'^(DISC-\d{3})',     # DISC-001
        r'^(PLAN-\d{3})',     # PLAN-001
        r'^(SESSION[-_]\d{3})',  # SESSION_001 or SESSION-001
    ]

    for pattern in patterns:
        match = re.match(pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1).upper().replace('_', '-')

    # Fallback: use document type + hash (for sessions, contracts, etc.)
    return f"{doc_type.value}_{_compute_hash(str(filepath))}"


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
    doc_id = _extract_artifact_id(filepath, content, doc_type)

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
    doc_id = _extract_artifact_id(filepath, content, doc_type)

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
