"""Knowledge Archive Contracts.

Contracts for document storage and synchronization in the Knowledge Archive.
Implements ADR-0047 archive layer requirements.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "2025.12.01"


class DocumentType(str, Enum):
    """Types of documents stored in the archive."""

    SESSION = "session"
    PLAN = "plan"
    DISCUSSION = "discussion"
    ADR = "adr"
    SPEC = "spec"
    CONTRACT = "contract"


class SyncMode(str, Enum):
    """File synchronization mode."""

    WATCHDOG = "watchdog"  # Real-time via file watcher
    MANUAL = "manual"  # On-demand via API


class DocumentMetadata(BaseModel):
    """Metadata extracted from document content.

    Attributes:
        status: Document status (draft, active, etc.).
        author: Document author.
        tags: Associated tags.
        references: Referenced document IDs.
        custom: Type-specific metadata.
    """

    status: str | None = None
    author: str | None = None
    tags: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    custom: dict[str, Any] = Field(default_factory=dict)


class Document(BaseModel):
    """A document in the Knowledge Archive.

    Attributes:
        id: Unique document identifier (e.g., ADR-0047, DISC-006).
        type: Type of document.
        title: Document title.
        file_path: Path to source file (relative to workspace).
        file_hash: SHA-256 hash of content for change detection.
        content: Full document content.
        metadata: Extracted metadata.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        archived_at: Soft-delete timestamp (null if active).
    """

    id: str
    type: DocumentType
    title: str
    file_path: str
    file_hash: str = ""
    content: str
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    archived_at: datetime | None = None

    @property
    def is_archived(self) -> bool:
        """Check if document is archived (soft-deleted)."""
        return self.archived_at is not None


class SyncConfig(BaseModel):
    """Configuration for file synchronization.

    Attributes:
        mode: Sync mode (watchdog or manual).
        watched_paths: Directories to watch for changes.
        debounce_ms: Debounce delay for rapid saves.
        excluded_patterns: Glob patterns to exclude.
    """

    mode: SyncMode = SyncMode.WATCHDOG
    watched_paths: list[str] = Field(
        default_factory=lambda: [
            ".discussions/",
            ".plans/",
            ".sessions/",
            ".adrs/",
            "docs/specs/",
            "shared/contracts/",
        ]
    )
    debounce_ms: int = 100
    excluded_patterns: list[str] = Field(
        default_factory=lambda: ["*.pyc", "__pycache__", ".git"]
    )


class SyncStatus(BaseModel):
    """Status of the synchronization service.

    Attributes:
        mode: Current sync mode.
        is_running: Whether sync service is active.
        last_sync_at: Timestamp of last sync.
        documents_synced: Count of synced documents.
        errors: Recent sync errors.
    """

    mode: SyncMode
    is_running: bool = False
    last_sync_at: datetime | None = None
    documents_synced: int = 0
    errors: list[str] = Field(default_factory=list)
