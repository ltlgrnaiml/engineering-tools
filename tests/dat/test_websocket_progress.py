"""Tests for DAT WebSocket progress tracking per SPEC-0027."""

import pytest
from datetime import datetime, timezone

from apps.data_aggregator.backend.src.dat_aggregation.api.websocket import (
    ProgressEventType,
    ProgressUpdate,
    ProgressTracker,
    ConnectionManager,
    progress_manager,
)


class TestProgressUpdate:
    """Test ProgressUpdate dataclass."""

    def test_create_progress_update(self):
        """Test creating a progress update."""
        update = ProgressUpdate(
            stage_id="test-stage-123",
            event_type=ProgressEventType.PROGRESS,
            progress_pct=50.0,
            rows_processed=5000,
        )
        
        assert update.stage_id == "test-stage-123"
        assert update.event_type == ProgressEventType.PROGRESS
        assert update.progress_pct == 50.0
        assert update.rows_processed == 5000

    def test_to_dict(self):
        """Test converting to dictionary."""
        update = ProgressUpdate(
            stage_id="test-stage",
            event_type=ProgressEventType.STARTED,
            message="Processing started",
        )
        
        data = update.to_dict()
        
        assert data["stage_id"] == "test-stage"
        assert data["event_type"] == "started"
        assert data["message"] == "Processing started"
        assert "timestamp" in data

    def test_to_json(self):
        """Test converting to JSON string."""
        update = ProgressUpdate(
            stage_id="test-stage",
            event_type=ProgressEventType.COMPLETED,
        )
        
        json_str = update.to_json()
        
        assert '"stage_id": "test-stage"' in json_str
        assert '"event_type": "completed"' in json_str


class TestProgressTracker:
    """Test ProgressTracker functionality."""

    def test_create_tracker(self):
        """Test creating a progress tracker."""
        tracker = ProgressTracker(
            stage_id="parse-123",
            total_rows=10000,
        )
        
        assert tracker.stage_id == "parse-123"
        assert tracker.total_rows == 10000

    def test_started_event(self):
        """Test started event creation."""
        tracker = ProgressTracker(stage_id="parse-123")
        
        update = tracker.started("Beginning parse")
        
        assert update.event_type == ProgressEventType.STARTED
        assert update.message == "Beginning parse"

    def test_update_progress(self):
        """Test updating progress."""
        tracker = ProgressTracker(
            stage_id="parse-123",
            total_rows=10000,
        )
        
        update = tracker.update(rows=2500)
        
        assert update.rows_processed == 2500
        assert update.progress_pct == 25.0
        assert update.event_type == ProgressEventType.PROGRESS

    def test_chunk_complete(self):
        """Test chunk completion event."""
        tracker = ProgressTracker(
            stage_id="parse-123",
            total_rows=10000,
        )
        
        update = tracker.update(rows=5000, chunk_complete=True)
        
        assert update.event_type == ProgressEventType.CHUNK_COMPLETE
        assert update.chunks_completed == 1
        assert update.progress_pct == 50.0

    def test_multiple_updates(self):
        """Test multiple progress updates accumulate."""
        tracker = ProgressTracker(
            stage_id="parse-123",
            total_rows=10000,
        )
        
        tracker.update(rows=2000)
        tracker.update(rows=3000)
        update = tracker.update(rows=5000)
        
        assert update.rows_processed == 10000
        assert update.progress_pct == 100.0

    def test_completed_event(self):
        """Test completed event creation."""
        tracker = ProgressTracker(
            stage_id="parse-123",
            total_rows=10000,
        )
        tracker.update(rows=10000)
        
        update = tracker.completed("All rows processed")
        
        assert update.event_type == ProgressEventType.COMPLETED
        assert update.progress_pct == 100.0
        assert update.message == "All rows processed"

    def test_cancelled_event(self):
        """Test cancelled event creation."""
        tracker = ProgressTracker(
            stage_id="parse-123",
            total_rows=10000,
        )
        tracker.update(rows=5000)
        
        update = tracker.cancelled()
        
        assert update.event_type == ProgressEventType.CANCELLED
        assert update.progress_pct == 50.0

    def test_error_event(self):
        """Test error event creation."""
        tracker = ProgressTracker(stage_id="parse-123")
        
        update = tracker.error("File not found")
        
        assert update.event_type == ProgressEventType.ERROR
        assert update.message == "File not found"

    def test_current_file_tracking(self):
        """Test current file tracking."""
        tracker = ProgressTracker(stage_id="parse-123")
        
        update = tracker.update(rows=100, current_file="data.csv")
        
        assert update.current_file == "data.csv"

    def test_bytes_based_progress(self):
        """Test progress tracking by bytes."""
        tracker = ProgressTracker(
            stage_id="parse-123",
            total_bytes=1000000,  # 1MB
        )
        
        update = tracker.update(bytes_processed=500000)
        
        assert update.progress_pct == 50.0


class TestConnectionManager:
    """Test ConnectionManager functionality."""

    @pytest.fixture
    def manager(self):
        """Create fresh connection manager."""
        return ConnectionManager()

    def test_create_tracker(self, manager):
        """Test creating a progress tracker via manager."""
        tracker = manager.create_tracker(
            run_id="run-123",
            stage_id="parse-456",
            total_rows=10000,
        )
        
        assert tracker.stage_id == "parse-456"
        assert tracker.total_rows == 10000

    def test_get_tracker(self, manager):
        """Test getting a tracker."""
        manager.create_tracker(
            run_id="run-123",
            stage_id="parse-456",
        )
        
        tracker = manager.get_tracker("run-123")
        
        assert tracker is not None
        assert tracker.stage_id == "parse-456"

    def test_get_nonexistent_tracker(self, manager):
        """Test getting a non-existent tracker returns None."""
        tracker = manager.get_tracker("nonexistent")
        
        assert tracker is None

    def test_remove_tracker(self, manager):
        """Test removing a tracker."""
        manager.create_tracker(
            run_id="run-123",
            stage_id="parse-456",
        )
        
        manager.remove_tracker("run-123")
        
        assert manager.get_tracker("run-123") is None

    def test_connection_count_empty(self, manager):
        """Test connection count when empty."""
        assert manager.get_connection_count("run-123") == 0

    def test_has_connections_empty(self, manager):
        """Test has_connections when empty."""
        assert manager.has_connections("run-123") is False


class TestProgressEventTypes:
    """Test progress event type enum."""

    def test_all_event_types_defined(self):
        """Test all expected event types exist."""
        assert ProgressEventType.STARTED.value == "started"
        assert ProgressEventType.PROGRESS.value == "progress"
        assert ProgressEventType.CHUNK_COMPLETE.value == "chunk_complete"
        assert ProgressEventType.COMPLETED.value == "completed"
        assert ProgressEventType.CANCELLED.value == "cancelled"
        assert ProgressEventType.ERROR.value == "error"


class TestGlobalProgressManager:
    """Test global progress manager singleton."""

    def test_progress_manager_exists(self):
        """Test global progress manager is available."""
        assert progress_manager is not None
        assert isinstance(progress_manager, ConnectionManager)
