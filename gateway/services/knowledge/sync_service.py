"""Sync Service - SPEC-0043-AR06.

File watcher for automatic document sync.
"""

from pathlib import Path
from threading import Timer

from gateway.services.knowledge.archive_service import ArchiveService
from gateway.services.knowledge.parsers import parse_document
from shared.contracts.knowledge.archive import SyncConfig, SyncStatus

DEFAULT_WATCH_PATHS = [
    Path('.sessions'),
    Path('.plans'),
    Path('.discussions'),
    Path('.adrs'),
    Path('docs/specs'),
    Path('shared/contracts'),
]


class SyncService:
    """Document synchronization with optional file watching."""

    def __init__(self, archive: ArchiveService, config: SyncConfig | None = None):
        self.archive = archive
        self.config = config or SyncConfig()
        self._observer = None
        self._debounce_timers: dict[str, Timer] = {}
        self._is_running = False

    def sync_all(self) -> int:
        """Sync all documents from configured paths. Returns count."""
        count = 0
        for watch_path in DEFAULT_WATCH_PATHS:
            if not watch_path.exists():
                continue
            for filepath in watch_path.rglob('*'):
                if filepath.is_file() and filepath.suffix in ('.md', '.json'):
                    try:
                        doc = parse_document(filepath)
                        if self.archive.upsert_document(doc):
                            self.archive.save_relationships(doc)
                            count += 1
                    except Exception:
                        continue
        return count

    def sync_path(self, path: Path) -> int:
        """Sync documents from specific path."""
        count = 0
        if path.is_file():
            doc = parse_document(path)
            if self.archive.upsert_document(doc):
                self.archive.save_relationships(doc)
                count = 1
        elif path.is_dir():
            for filepath in path.rglob('*'):
                if filepath.is_file() and filepath.suffix in ('.md', '.json'):
                    try:
                        doc = parse_document(filepath)
                        if self.archive.upsert_document(doc):
                            self.archive.save_relationships(doc)
                            count += 1
                    except Exception:
                        continue
        return count

    def rebuild_relationships(self) -> int:
        """Rebuild all relationships from existing documents.
        
        Use this to populate relationships for documents that were
        synced before relationship extraction was added.
        
        Returns:
            Number of documents processed.
        """
        docs = self.archive.list_documents()
        count = 0
        for doc in docs:
            self.archive.save_relationships(doc)
            count += 1
        return count

    def get_status(self) -> SyncStatus:
        """Get current sync status."""
        return SyncStatus(
            mode=self.config.mode,
            is_running=self._is_running,
            last_sync=None,
            documents_synced=0
        )

    def start_watching(self) -> bool:
        """Start file watcher (requires watchdog)."""
        try:
            from watchdog.events import FileSystemEventHandler
            from watchdog.observers import Observer

            class Handler(FileSystemEventHandler):
                def __init__(self, sync_svc: 'SyncService'):
                    self.sync_svc = sync_svc

                def on_modified(self, event):
                    if not event.is_directory:
                        self.sync_svc._debounced_sync(Path(event.src_path))

            self._observer = Observer()
            handler = Handler(self)
            for path in DEFAULT_WATCH_PATHS:
                if path.exists():
                    self._observer.schedule(handler, str(path), recursive=True)
            self._observer.start()
            self._is_running = True
            return True
        except ImportError:
            return False

    def stop_watching(self):
        """Stop file watcher."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._is_running = False

    def _debounced_sync(self, path: Path, delay: float = 0.5):
        """Debounce rapid file changes."""
        key = str(path)
        if key in self._debounce_timers:
            self._debounce_timers[key].cancel()
        timer = Timer(delay, lambda: self.sync_path(path))
        self._debounce_timers[key] = timer
        timer.start()
