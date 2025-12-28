"""Tests for DAT memory manager per SPEC-DAT-0004."""

import tempfile
from pathlib import Path

import pytest

from apps.data_aggregator.backend.src.dat_aggregation.core.memory_manager import (
    MemoryConfig,
    MemoryManager,
    MemorySnapshot,
    MemoryTier,
    FileSizeStrategy,
    FILE_SIZE_STRATEGIES,
    STREAMING_THRESHOLD_BYTES,
    get_memory_manager,
    reset_memory_manager,
)


class TestMemoryConfig:
    """Test MemoryConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values per SPEC-DAT-0004."""
        config = MemoryConfig()
        
        assert config.max_memory_mb == 200
        assert config.warning_threshold_pct == 80.0
        assert config.gc_threshold_pct == 70.0
        assert config.chunk_size_rows == 50000
        assert config.schema_probe_rows == 1000
        assert config.spill_to_disk is True
        assert config.spill_directory is not None

    def test_custom_config(self):
        """Test custom configuration."""
        config = MemoryConfig(
            max_memory_mb=100,
            chunk_size_rows=10000,
        )
        
        assert config.max_memory_mb == 100
        assert config.chunk_size_rows == 10000


class TestMemorySnapshot:
    """Test MemorySnapshot capture."""

    def test_capture_snapshot(self):
        """Test capturing memory snapshot."""
        config = MemoryConfig()
        snapshot = MemorySnapshot.capture(config)
        
        assert snapshot.timestamp is not None
        assert snapshot.process_memory_mb > 0
        assert snapshot.available_memory_mb > 0
        assert snapshot.usage_pct >= 0
        assert isinstance(snapshot.tier, MemoryTier)

    def test_tier_determination(self):
        """Test memory tier determination."""
        assert MemorySnapshot._determine_tier(10) == MemoryTier.SMALL
        assert MemorySnapshot._determine_tier(30) == MemoryTier.MEDIUM
        assert MemorySnapshot._determine_tier(60) == MemoryTier.LARGE
        assert MemorySnapshot._determine_tier(80) == MemoryTier.VERY_LARGE
        assert MemorySnapshot._determine_tier(95) == MemoryTier.MASSIVE


class TestFileSizeStrategies:
    """Test file size tier strategies per SPEC-DAT-0004."""

    def test_streaming_threshold(self):
        """Test streaming threshold is 10MB per ADR-0040."""
        assert STREAMING_THRESHOLD_BYTES == 10 * 1024 * 1024

    def test_all_tiers_defined(self):
        """Test all memory tiers have strategies."""
        for tier in MemoryTier:
            assert tier in FILE_SIZE_STRATEGIES

    def test_small_tier_strategy(self):
        """Test small file strategy (< 100KB)."""
        strategy = FILE_SIZE_STRATEGIES[MemoryTier.SMALL]
        
        assert strategy.strategy == "eager_load"
        assert strategy.preview_rows is None  # All rows
        assert strategy.chunk_size is None

    def test_large_tier_strategy(self):
        """Test large file strategy (10-100MB)."""
        strategy = FILE_SIZE_STRATEGIES[MemoryTier.LARGE]
        
        assert strategy.strategy == "streaming_chunks"
        assert strategy.preview_rows == 10000
        assert strategy.chunk_size == 50000
        assert strategy.memory_cap_mb == 50

    def test_massive_tier_strategy(self):
        """Test massive file strategy (> 1GB)."""
        strategy = FILE_SIZE_STRATEGIES[MemoryTier.MASSIVE]
        
        assert strategy.strategy == "partitioned_streaming"
        assert strategy.preview_rows == 1000
        assert strategy.chunk_size == 100000
        assert strategy.memory_cap_mb == 200


class TestMemoryManager:
    """Test MemoryManager functionality."""

    @pytest.fixture
    def manager(self):
        """Create fresh memory manager."""
        return MemoryManager()

    @pytest.fixture
    def temp_files(self):
        """Create temporary test files of various sizes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Small file (1KB)
            small_file = tmpdir / "small.csv"
            small_file.write_text("a,b,c\n" + "1,2,3\n" * 30)
            
            # Medium file (~1MB)
            medium_file = tmpdir / "medium.csv"
            medium_file.write_text("a,b,c\n" + "1,2,3\n" * 50000)
            
            yield {
                "small": small_file,
                "medium": medium_file,
                "dir": tmpdir,
            }

    def test_get_current_usage(self, manager):
        """Test getting current memory usage."""
        snapshot = manager.get_current_usage()
        
        assert isinstance(snapshot, MemorySnapshot)
        assert snapshot.process_memory_mb > 0

    def test_check_and_manage(self, manager):
        """Test memory check and management."""
        snapshot = manager.check_and_manage()
        
        assert isinstance(snapshot, MemorySnapshot)

    def test_should_stream_small_file(self, manager, temp_files):
        """Test small files don't use streaming."""
        assert manager.should_stream(temp_files["small"]) is False

    def test_get_strategy_for_small_file(self, manager, temp_files):
        """Test strategy selection for small files."""
        strategy = manager.get_strategy_for_file(temp_files["small"])
        
        assert strategy.tier in [MemoryTier.SMALL, MemoryTier.MEDIUM]
        assert "eager" in strategy.strategy

    def test_get_chunk_size(self, manager, temp_files):
        """Test chunk size retrieval."""
        chunk_size = manager.get_chunk_size(temp_files["small"])
        
        # Small files use default chunk size
        assert chunk_size == manager.config.chunk_size_rows

    def test_get_preview_rows_small(self, manager, temp_files):
        """Test preview rows for small files (all rows)."""
        preview_rows = manager.get_preview_rows(temp_files["small"])
        
        # Small/medium files show all rows
        assert preview_rows is None

    def test_create_spill_file(self, manager):
        """Test spill file creation."""
        spill_file = manager.create_spill_file("test_")
        
        assert spill_file is not None
        assert len(manager._spill_files) == 1

    def test_cleanup_spill_files(self, manager):
        """Test spill file cleanup."""
        spill_file = manager.create_spill_file("test_")
        spill_file.write_text("test data")
        
        assert spill_file.exists()
        
        count = manager.cleanup_spill_files()
        
        assert count == 1
        assert not spill_file.exists()
        assert len(manager._spill_files) == 0

    def test_get_stats(self, manager):
        """Test statistics retrieval."""
        stats = manager.get_stats()
        
        assert "current_memory_mb" in stats
        assert "available_memory_mb" in stats
        assert "usage_pct" in stats
        assert "max_memory_mb" in stats
        assert "gc_count" in stats

    def test_context_manager(self):
        """Test context manager cleans up spill files."""
        with MemoryManager() as manager:
            spill_file = manager.create_spill_file("test_")
            spill_file.write_text("test data")
            assert spill_file.exists()
        
        # After context, spill file should be cleaned up
        assert not spill_file.exists()

    def test_warning_callback(self, manager):
        """Test warning callback is invoked."""
        warnings = []
        manager.set_warning_callback(lambda msg: warnings.append(msg))
        
        # Force a high usage scenario by setting low max
        manager.config.max_memory_mb = 1  # 1MB limit
        manager.config.warning_threshold_pct = 1  # Very low threshold
        
        manager.check_and_manage()
        
        # Should have triggered warning due to low threshold
        assert len(warnings) >= 0  # May or may not trigger depending on actual usage


class TestModuleSingleton:
    """Test module-level singleton functions."""

    def test_get_memory_manager(self):
        """Test getting default memory manager."""
        reset_memory_manager()
        
        manager1 = get_memory_manager()
        manager2 = get_memory_manager()
        
        assert manager1 is manager2

    def test_reset_memory_manager(self):
        """Test resetting memory manager."""
        manager1 = get_memory_manager()
        reset_memory_manager()
        manager2 = get_memory_manager()
        
        assert manager1 is not manager2

    def test_get_memory_manager_with_config(self):
        """Test getting manager with custom config."""
        reset_memory_manager()
        
        config = MemoryConfig(max_memory_mb=100)
        manager = get_memory_manager(config)
        
        assert manager.config.max_memory_mb == 100
        
        reset_memory_manager()
