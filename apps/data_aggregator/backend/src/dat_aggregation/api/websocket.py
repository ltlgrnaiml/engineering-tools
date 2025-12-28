"""WebSocket endpoints for DAT progress tracking.

This module implements real-time progress updates for long-running DAT operations
per SPEC-DAT-0004. It provides WebSocket connections for streaming progress
during Parse and Export stages.

Endpoint: /ws/dat/runs/{run_id}/progress
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable

from fastapi import WebSocket, WebSocketDisconnect

__version__ = "1.0.0"


class ProgressEventType(str, Enum):
    """Types of progress events."""

    STARTED = "started"
    PROGRESS = "progress"
    CHUNK_COMPLETE = "chunk_complete"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class ProgressUpdate:
    """Progress update payload per SPEC-DAT-0004.

    Attributes:
        stage_id: Current stage ID.
        event_type: Type of progress event.
        progress_pct: Completion percentage (0-100).
        rows_processed: Total rows processed so far.
        chunks_completed: Number of chunks completed.
        current_file: File currently being processed.
        estimated_remaining_ms: Estimated time remaining in milliseconds.
        message: Optional status message.
        timestamp: ISO-8601 UTC timestamp.
    """

    stage_id: str
    event_type: ProgressEventType
    progress_pct: float = 0.0
    rows_processed: int = 0
    chunks_completed: int = 0
    current_file: str | None = None
    estimated_remaining_ms: int | None = None
    message: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "stage_id": self.stage_id,
            "event_type": self.event_type.value,
            "progress_pct": round(self.progress_pct, 1),
            "rows_processed": self.rows_processed,
            "chunks_completed": self.chunks_completed,
            "current_file": self.current_file,
            "estimated_remaining_ms": self.estimated_remaining_ms,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
        }

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict())


@dataclass
class ProgressTracker:
    """Tracks progress for a single operation.

    Attributes:
        stage_id: The stage being tracked.
        total_rows: Total rows to process (if known).
        total_bytes: Total bytes to process (if known).
        start_time: When processing started.
    """

    stage_id: str
    total_rows: int | None = None
    total_bytes: int | None = None
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    _rows_processed: int = 0
    _bytes_processed: int = 0
    _chunks_completed: int = 0
    _current_file: str | None = None

    def update(
        self,
        rows: int = 0,
        bytes_processed: int = 0,
        chunk_complete: bool = False,
        current_file: str | None = None,
    ) -> ProgressUpdate:
        """Update progress and return a ProgressUpdate.

        Args:
            rows: Additional rows processed.
            bytes_processed: Additional bytes processed.
            chunk_complete: Whether a chunk just completed.
            current_file: Current file being processed.

        Returns:
            ProgressUpdate with current state.
        """
        self._rows_processed += rows
        self._bytes_processed += bytes_processed
        if chunk_complete:
            self._chunks_completed += 1
        if current_file:
            self._current_file = current_file

        # Calculate progress percentage
        progress_pct = 0.0
        if self.total_rows and self.total_rows > 0:
            progress_pct = (self._rows_processed / self.total_rows) * 100
        elif self.total_bytes and self.total_bytes > 0:
            progress_pct = (self._bytes_processed / self.total_bytes) * 100

        # Estimate remaining time
        elapsed = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        estimated_remaining_ms = None
        if progress_pct > 0 and elapsed > 0:
            total_estimated = elapsed / (progress_pct / 100)
            remaining = total_estimated - elapsed
            estimated_remaining_ms = int(remaining * 1000)

        event_type = ProgressEventType.CHUNK_COMPLETE if chunk_complete else ProgressEventType.PROGRESS

        return ProgressUpdate(
            stage_id=self.stage_id,
            event_type=event_type,
            progress_pct=min(progress_pct, 100.0),
            rows_processed=self._rows_processed,
            chunks_completed=self._chunks_completed,
            current_file=self._current_file,
            estimated_remaining_ms=estimated_remaining_ms,
        )

    def started(self, message: str | None = None) -> ProgressUpdate:
        """Create a started event."""
        return ProgressUpdate(
            stage_id=self.stage_id,
            event_type=ProgressEventType.STARTED,
            message=message or "Processing started",
        )

    def completed(self, message: str | None = None) -> ProgressUpdate:
        """Create a completed event."""
        return ProgressUpdate(
            stage_id=self.stage_id,
            event_type=ProgressEventType.COMPLETED,
            progress_pct=100.0,
            rows_processed=self._rows_processed,
            chunks_completed=self._chunks_completed,
            message=message or "Processing completed",
        )

    def cancelled(self, message: str | None = None) -> ProgressUpdate:
        """Create a cancelled event."""
        return ProgressUpdate(
            stage_id=self.stage_id,
            event_type=ProgressEventType.CANCELLED,
            progress_pct=self._calculate_progress(),
            rows_processed=self._rows_processed,
            chunks_completed=self._chunks_completed,
            message=message or "Processing cancelled",
        )

    def error(self, message: str) -> ProgressUpdate:
        """Create an error event."""
        return ProgressUpdate(
            stage_id=self.stage_id,
            event_type=ProgressEventType.ERROR,
            progress_pct=self._calculate_progress(),
            rows_processed=self._rows_processed,
            chunks_completed=self._chunks_completed,
            message=message,
        )

    def _calculate_progress(self) -> float:
        """Calculate current progress percentage."""
        if self.total_rows and self.total_rows > 0:
            return min((self._rows_processed / self.total_rows) * 100, 100.0)
        elif self.total_bytes and self.total_bytes > 0:
            return min((self._bytes_processed / self.total_bytes) * 100, 100.0)
        return 0.0


class ConnectionManager:
    """Manages WebSocket connections for progress updates.

    Thread-safe manager that handles multiple concurrent connections
    per run_id and broadcasts progress updates.
    """

    def __init__(self):
        """Initialize connection manager."""
        self._connections: dict[str, list[WebSocket]] = {}
        self._trackers: dict[str, ProgressTracker] = {}
        self._lock = asyncio.Lock()

    async def connect(self, run_id: str, websocket: WebSocket) -> None:
        """Accept and register a new WebSocket connection.

        Args:
            run_id: The run ID to subscribe to.
            websocket: The WebSocket connection.
        """
        await websocket.accept()
        async with self._lock:
            if run_id not in self._connections:
                self._connections[run_id] = []
            self._connections[run_id].append(websocket)

    async def disconnect(self, run_id: str, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            run_id: The run ID to unsubscribe from.
            websocket: The WebSocket connection to remove.
        """
        async with self._lock:
            if run_id in self._connections:
                if websocket in self._connections[run_id]:
                    self._connections[run_id].remove(websocket)
                if not self._connections[run_id]:
                    del self._connections[run_id]

    async def broadcast(self, run_id: str, update: ProgressUpdate) -> None:
        """Broadcast a progress update to all connections for a run.

        Args:
            run_id: The run ID to broadcast to.
            update: The progress update to send.
        """
        async with self._lock:
            connections = self._connections.get(run_id, [])

        # Send to all connections (outside lock to avoid blocking)
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_text(update.to_json())
            except Exception:
                disconnected.append(websocket)

        # Clean up disconnected
        for websocket in disconnected:
            await self.disconnect(run_id, websocket)

    def create_tracker(
        self,
        run_id: str,
        stage_id: str,
        total_rows: int | None = None,
        total_bytes: int | None = None,
    ) -> ProgressTracker:
        """Create a progress tracker for a run.

        Args:
            run_id: The run ID.
            stage_id: The stage ID.
            total_rows: Total rows to process.
            total_bytes: Total bytes to process.

        Returns:
            ProgressTracker instance.
        """
        tracker = ProgressTracker(
            stage_id=stage_id,
            total_rows=total_rows,
            total_bytes=total_bytes,
        )
        self._trackers[run_id] = tracker
        return tracker

    def get_tracker(self, run_id: str) -> ProgressTracker | None:
        """Get the progress tracker for a run.

        Args:
            run_id: The run ID.

        Returns:
            ProgressTracker or None if not found.
        """
        return self._trackers.get(run_id)

    def remove_tracker(self, run_id: str) -> None:
        """Remove the progress tracker for a run.

        Args:
            run_id: The run ID.
        """
        self._trackers.pop(run_id, None)

    def get_connection_count(self, run_id: str) -> int:
        """Get number of active connections for a run.

        Args:
            run_id: The run ID.

        Returns:
            Number of active connections.
        """
        return len(self._connections.get(run_id, []))

    def has_connections(self, run_id: str) -> bool:
        """Check if there are any active connections for a run.

        Args:
            run_id: The run ID.

        Returns:
            True if there are active connections.
        """
        return run_id in self._connections and len(self._connections[run_id]) > 0


# Global connection manager instance
progress_manager = ConnectionManager()


def get_progress_callback(run_id: str) -> Callable[[ProgressUpdate], None]:
    """Create a progress callback for use in processing functions.

    This allows non-async code to queue progress updates.

    Args:
        run_id: The run ID.

    Returns:
        Callback function that accepts ProgressUpdate.
    """
    import threading

    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=loop.run_forever, daemon=True)
    thread.start()

    def callback(update: ProgressUpdate) -> None:
        asyncio.run_coroutine_threadsafe(
            progress_manager.broadcast(run_id, update),
            loop,
        )

    return callback


async def websocket_progress_endpoint(websocket: WebSocket, run_id: str) -> None:
    """WebSocket endpoint handler for progress updates.

    This function handles the WebSocket connection lifecycle:
    1. Accept connection
    2. Send current progress if available
    3. Keep connection alive until disconnect or completion

    Args:
        websocket: The WebSocket connection.
        run_id: The run ID to subscribe to.
    """
    await progress_manager.connect(run_id, websocket)
    try:
        # Send current progress if tracker exists
        tracker = progress_manager.get_tracker(run_id)
        if tracker:
            current = tracker.update()
            await websocket.send_text(current.to_json())

        # Keep connection alive - client can send pings
        while True:
            try:
                # Wait for client messages (pings) with timeout
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0,  # 30 second timeout
                )
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat"}))
    except WebSocketDisconnect:
        pass
    finally:
        await progress_manager.disconnect(run_id, websocket)
