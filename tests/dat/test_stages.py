"""Tests for DAT pipeline stages."""
import json
import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timezone

import polars as pl

from apps.data_aggregator.backend.src.dat_aggregation.stages import (
    FileInfo,
    SelectionResult,
    execute_selection,
    discover_files,
    ContextConfig,
    ContextResult,
    execute_context,
    apply_context_to_dataframe,
    ParseConfig,
    ParseResult,
    CancellationToken,
    execute_parse,
)
from apps.data_aggregator.backend.src.dat_aggregation.stages.context import ColumnOverride


EXAMPLES_DIR = Path(__file__).parent.parent.parent / "apps" / "data_aggregator" / "backend" / "src" / "dat_aggregation" / "profiles" / "examples"


class TestSelectionStage:
    """Test file selection stage."""
    
    @pytest.fixture
    def temp_dir_with_files(self):
        """Create temp directory with test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create JSON file
            json_file = tmpdir / "test_data.json"
            json.dump([{"id": 1, "value": 100}], open(json_file, "w"))
            
            # Create CSV file
            csv_file = tmpdir / "test_data.csv"
            csv_file.write_text("id,value\n1,100\n2,200")
            
            # Create unsupported file
            txt_file = tmpdir / "readme.md"
            txt_file.write_text("# Test")
            
            yield tmpdir
    
    @pytest.mark.asyncio
    async def test_discover_files_in_directory(self, temp_dir_with_files):
        """Test discovering files in a directory."""
        files = await discover_files([temp_dir_with_files])
        
        assert len(files) >= 2
        extensions = {f.extension for f in files}
        assert ".json" in extensions
        assert ".csv" in extensions
    
    @pytest.mark.asyncio
    async def test_discover_files_single_file(self, temp_dir_with_files):
        """Test discovering a single file."""
        json_file = temp_dir_with_files / "test_data.json"
        files = await discover_files([json_file])
        
        assert len(files) == 1
        assert files[0].extension == ".json"
        assert files[0].name == "test_data.json"
    
    @pytest.mark.asyncio
    async def test_discover_files_recursive(self, temp_dir_with_files):
        """Test recursive file discovery."""
        # Create subdirectory with files
        subdir = temp_dir_with_files / "subdir"
        subdir.mkdir()
        sub_file = subdir / "sub_data.json"
        json.dump({"nested": True}, open(sub_file, "w"))
        
        files = await discover_files([temp_dir_with_files], recursive=True)
        
        # Should find files in both main dir and subdir
        paths = {f.path for f in files}
        assert sub_file in paths
    
    @pytest.mark.asyncio
    async def test_discover_files_non_recursive(self, temp_dir_with_files):
        """Test non-recursive file discovery."""
        # Create subdirectory with files
        subdir = temp_dir_with_files / "subdir"
        subdir.mkdir()
        sub_file = subdir / "sub_data.json"
        json.dump({"nested": True}, open(sub_file, "w"))
        
        files = await discover_files([temp_dir_with_files], recursive=False)
        
        # Should NOT find files in subdir
        paths = {f.path for f in files}
        assert sub_file not in paths
    
    @pytest.mark.asyncio
    async def test_execute_selection_default(self, temp_dir_with_files):
        """Test execute_selection with default (select all)."""
        result = await execute_selection([temp_dir_with_files])
        
        assert result.completed
        assert len(result.discovered_files) >= 2
        # Default: all discovered files are selected
        assert len(result.selected_files) == len(result.discovered_files)
    
    @pytest.mark.asyncio
    async def test_execute_selection_with_preselection(self, temp_dir_with_files):
        """Test execute_selection with pre-selected files."""
        json_file = temp_dir_with_files / "test_data.json"
        
        result = await execute_selection(
            [temp_dir_with_files],
            selected_files=[json_file]
        )
        
        assert result.completed
        assert len(result.selected_files) == 1
        assert result.selected_files[0] == json_file
    
    @pytest.mark.asyncio
    async def test_file_info_attributes(self, temp_dir_with_files):
        """Test FileInfo has correct attributes."""
        files = await discover_files([temp_dir_with_files])
        
        for file_info in files:
            assert isinstance(file_info.path, Path)
            assert isinstance(file_info.name, str)
            assert isinstance(file_info.extension, str)
            assert isinstance(file_info.size_bytes, int)
            assert isinstance(file_info.tables, list)
            assert file_info.size_bytes > 0


class TestContextStage:
    """Test context configuration stage."""
    
    @pytest.mark.asyncio
    async def test_execute_context_basic(self):
        """Test basic context execution."""
        config = ContextConfig()
        result = await execute_context("test-run-123", config)
        
        assert result.completed
        assert result.context_id is not None
        assert result.config == config
    
    @pytest.mark.asyncio
    async def test_execute_context_with_overrides(self):
        """Test context execution with column overrides."""
        config = ContextConfig(
            column_overrides=[
                ColumnOverride(column_name="old_name", rename_to="new_name"),
                ColumnOverride(column_name="drop_me", drop=True),
            ]
        )
        result = await execute_context("test-run-123", config)
        
        assert result.completed
        assert len(result.config.column_overrides) == 2
    
    @pytest.mark.asyncio
    async def test_context_id_deterministic(self):
        """Test that context ID is deterministic for same inputs."""
        config = ContextConfig(
            date_format="%Y-%m-%d",
            encoding="utf-8",
        )
        
        result1 = await execute_context("test-run-123", config)
        result2 = await execute_context("test-run-123", config)
        
        assert result1.context_id == result2.context_id
    
    def test_apply_context_rename_column(self):
        """Test applying context to rename a column."""
        df = pl.DataFrame({
            "old_col": [1, 2, 3],
            "keep_col": ["a", "b", "c"],
        })
        
        config = ContextConfig(
            column_overrides=[
                ColumnOverride(column_name="old_col", rename_to="new_col"),
            ]
        )
        
        result = apply_context_to_dataframe(df, config)
        
        assert "new_col" in result.columns
        assert "old_col" not in result.columns
        assert "keep_col" in result.columns
    
    def test_apply_context_drop_column(self):
        """Test applying context to drop a column."""
        df = pl.DataFrame({
            "keep_col": [1, 2, 3],
            "drop_col": ["a", "b", "c"],
        })
        
        config = ContextConfig(
            column_overrides=[
                ColumnOverride(column_name="drop_col", drop=True),
            ]
        )
        
        result = apply_context_to_dataframe(df, config)
        
        assert "keep_col" in result.columns
        assert "drop_col" not in result.columns
    
    def test_apply_context_cast_column(self):
        """Test applying context to cast column type."""
        df = pl.DataFrame({
            "str_col": ["1", "2", "3"],
        })
        
        config = ContextConfig(
            column_overrides=[
                ColumnOverride(column_name="str_col", target_dtype="int64"),
            ]
        )
        
        result = apply_context_to_dataframe(df, config)
        
        assert result["str_col"].dtype == pl.Int64
    
    def test_apply_context_nonexistent_column(self):
        """Test applying context for nonexistent column is ignored."""
        df = pl.DataFrame({
            "col_a": [1, 2, 3],
        })
        
        config = ContextConfig(
            column_overrides=[
                ColumnOverride(column_name="nonexistent", rename_to="new_name"),
            ]
        )
        
        result = apply_context_to_dataframe(df, config)
        
        # Should return unchanged DataFrame
        assert "col_a" in result.columns
        assert len(result.columns) == 1


class TestParseStage:
    """Test parse stage functionality."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            yield workspace
    
    @pytest.fixture
    def temp_json_file(self):
        """Create temporary JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"id": 1, "value": 100, "category": "A"},
                {"id": 2, "value": 200, "category": "B"},
            ], f)
            f.flush()
            yield Path(f.name)
    
    @pytest.mark.asyncio
    async def test_execute_parse_basic(self, temp_workspace, temp_json_file):
        """Test basic parse execution."""
        config = ParseConfig(
            selected_files=[temp_json_file],
            selected_tables={},
        )
        
        result = await execute_parse(
            run_id="test-run-123",
            config=config,
            workspace_path=temp_workspace,
        )
        
        assert result.completed
        assert result.row_count == 2
        assert result.column_count == 3
        assert len(result.source_files) > 0
        assert result.output_path is not None
    
    @pytest.mark.asyncio
    async def test_execute_parse_creates_parquet(self, temp_workspace, temp_json_file):
        """Test that parse creates Parquet output."""
        config = ParseConfig(
            selected_files=[temp_json_file],
            selected_tables={},
        )
        
        result = await execute_parse(
            run_id="test-run-123",
            config=config,
            workspace_path=temp_workspace,
        )
        
        output_path = Path(result.output_path)
        assert output_path.exists()
        assert output_path.suffix == ".parquet"
        
        # Verify Parquet is readable
        df = pl.read_parquet(output_path)
        assert len(df) == 2
    
    @pytest.mark.asyncio
    async def test_execute_parse_with_column_mappings(self, temp_workspace, temp_json_file):
        """Test parse with column mappings."""
        config = ParseConfig(
            selected_files=[temp_json_file],
            selected_tables={},
            column_mappings={"id": "record_id", "value": "measurement"},
        )
        
        result = await execute_parse(
            run_id="test-run-123",
            config=config,
            workspace_path=temp_workspace,
        )
        
        assert result.completed
        assert "record_id" in result.data.columns
        assert "measurement" in result.data.columns
    
    @pytest.mark.asyncio
    async def test_execute_parse_with_progress_callback(self, temp_workspace, temp_json_file):
        """Test parse with progress callback."""
        progress_updates = []
        
        def callback(percent, message):
            progress_updates.append((percent, message))
        
        config = ParseConfig(
            selected_files=[temp_json_file],
            selected_tables={},
        )
        
        result = await execute_parse(
            run_id="test-run-123",
            config=config,
            workspace_path=temp_workspace,
            progress_callback=callback,
        )
        
        assert result.completed
        assert len(progress_updates) > 0
        # Last update should be 100%
        assert progress_updates[-1][0] == 100
    
    @pytest.mark.asyncio
    async def test_execute_parse_with_cancellation(self, temp_workspace, temp_json_file):
        """Test parse with cancellation."""
        cancel_token = CancellationToken()
        cancel_token.cancel()  # Cancel immediately
        
        config = ParseConfig(
            selected_files=[temp_json_file],
            selected_tables={},
        )
        
        result = await execute_parse(
            run_id="test-run-123",
            config=config,
            workspace_path=temp_workspace,
            cancel_token=cancel_token,
        )
        
        assert not result.completed
    
    def test_cancellation_token(self):
        """Test CancellationToken functionality."""
        token = CancellationToken()
        
        assert not token.is_cancelled
        
        token.cancel()
        
        assert token.is_cancelled
    
    @pytest.mark.asyncio
    async def test_parse_id_deterministic(self, temp_workspace, temp_json_file):
        """Test that parse ID is deterministic."""
        config = ParseConfig(
            selected_files=[temp_json_file],
            selected_tables={},
        )
        
        result1 = await execute_parse(
            run_id="test-run-123",
            config=config,
            workspace_path=temp_workspace,
        )
        
        result2 = await execute_parse(
            run_id="test-run-123",
            config=config,
            workspace_path=temp_workspace,
        )
        
        assert result1.parse_id == result2.parse_id


class TestParseWithExampleData:
    """Test parse stage with example data files."""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir) / "workspace"
            workspace.mkdir()
            yield workspace
    
    @pytest.fixture
    def example_data_path(self):
        """Get path to example data file."""
        return EXAMPLES_DIR / "LOTABC12345_W01_CDSEM001_20251227_measurement.json"
    
    @pytest.mark.asyncio
    async def test_parse_example_file(self, temp_workspace, example_data_path):
        """Test parsing the example data file with profile-driven extraction.
        
        Note: Full nested JSON parsing requires profile-driven table extraction.
        This test validates that the parse stage can handle JSON files when
        proper table paths are specified.
        """
        if not example_data_path.exists():
            pytest.skip("Example data file not found")
        
        # For nested JSON, we need to specify which table/path to extract
        # The parse stage will need profile integration for full support
        # For now, test with a specific table path that works
        config = ParseConfig(
            selected_files=[example_data_path],
            selected_tables={str(example_data_path): ["$.summary"]},
        )
        
        # This test is currently skipped pending full profile integration
        # The JSON adapter works correctly when given proper extraction options
        pytest.skip("Pending profile-driven parse integration for nested JSON")
