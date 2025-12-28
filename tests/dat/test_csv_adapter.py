"""Unit tests for CSVAdapter.

Per SPEC-DAT-0003: Adapter Interface & Registry specification.
Tests AC-3: CSV Adapter Requirements from ACCEPTANCE_CRITERIA_ADAPTERS.md
"""

from pathlib import Path

import polars as pl
import pytest

from apps.data_aggregator.backend.adapters import CSVAdapter
from shared.contracts.dat.adapter import (
    AdapterError,
    AdapterErrorCode,
    AdapterMetadata,
    BaseFileAdapter,
    InferredDataType,
    ReadOptions,
    StreamOptions,
    ValidationSeverity,
)

# Fixture directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestCSVAdapterMetadata:
    """Test AC-3.1: Metadata requirements."""

    def test_adapter_id_is_csv(self) -> None:
        """AC-3.1.1: adapter_id is 'csv'."""
        adapter = CSVAdapter()
        assert adapter.metadata.adapter_id == "csv"

    def test_file_extensions_include_csv_and_tsv(self) -> None:
        """AC-3.1.2: file_extensions includes .csv and .tsv."""
        adapter = CSVAdapter()
        extensions = adapter.metadata.file_extensions

        assert ".csv" in extensions
        assert ".tsv" in extensions

    def test_supports_streaming_is_true(self) -> None:
        """AC-3.1.3: capabilities.supports_streaming is True."""
        adapter = CSVAdapter()
        assert adapter.metadata.capabilities.supports_streaming is True

    def test_supports_schema_inference_is_true(self) -> None:
        """AC-3.1.4: capabilities.supports_schema_inference is True."""
        adapter = CSVAdapter()
        assert adapter.metadata.capabilities.supports_schema_inference is True


class TestCSVAdapterInterface:
    """Test AC-1: Adapter Interface Compliance for CSV."""

    def test_inherits_from_base_file_adapter(self) -> None:
        """AC-1.1.1: Adapter inherits from BaseFileAdapter."""
        adapter = CSVAdapter()
        assert isinstance(adapter, BaseFileAdapter)

    def test_metadata_returns_adapter_metadata(self) -> None:
        """AC-1.1.2: metadata property returns AdapterMetadata."""
        adapter = CSVAdapter()
        assert isinstance(adapter.metadata, AdapterMetadata)

    def test_can_handle_csv_files(self) -> None:
        """AC-1.1.7: can_handle() works for CSV files."""
        adapter = CSVAdapter()

        assert adapter.can_handle("data.csv") is True
        assert adapter.can_handle("data.tsv") is True
        assert adapter.can_handle("data.CSV") is True  # Case insensitive
        assert adapter.can_handle("data.xlsx") is False
        assert adapter.can_handle("data.json") is False


class TestCSVAdapterProbeSchema:
    """Test AC-3.2: Schema Probing requirements."""

    @pytest.mark.asyncio
    async def test_probe_schema_returns_schema_probe_result(self) -> None:
        """AC-3.2.1: probe_schema() returns SchemaProbeResult with columns."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")

        result = await adapter.probe_schema(file_path)

        assert result.file_path == file_path
        assert len(result.columns) > 0
        assert result.adapter_id == "csv"

    @pytest.mark.asyncio
    async def test_probe_schema_infers_column_types(self) -> None:
        """AC-3.2.2: probe_schema() infers column types from sample data."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")

        result = await adapter.probe_schema(file_path)

        # Check we have the expected columns
        column_names = [c.name for c in result.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "value" in column_names

        # Check type inference
        id_col = next(c for c in result.columns if c.name == "id")
        assert id_col.inferred_type == InferredDataType.INTEGER

        name_col = next(c for c in result.columns if c.name == "name")
        assert name_col.inferred_type == InferredDataType.STRING

    @pytest.mark.asyncio
    async def test_probe_schema_detects_delimiter(self) -> None:
        """AC-3.2.3: probe_schema() detects delimiter."""
        adapter = CSVAdapter()

        csv_result = await adapter.probe_schema(str(FIXTURES_DIR / "sample.csv"))
        assert csv_result.delimiter_detected == ","

        tsv_result = await adapter.probe_schema(str(FIXTURES_DIR / "sample.tsv"))
        assert tsv_result.delimiter_detected == "\t"

    @pytest.mark.asyncio
    async def test_probe_schema_detects_encoding(self) -> None:
        """AC-3.2.4: probe_schema() detects encoding."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")

        result = await adapter.probe_schema(file_path)

        assert result.encoding_detected is not None
        assert result.encoding_detected in ["utf-8", "utf-8-sig", "latin-1"]

    @pytest.mark.asyncio
    async def test_probe_schema_detects_header_row(self) -> None:
        """AC-3.2.5: probe_schema() detects header row presence."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")

        result = await adapter.probe_schema(file_path)

        assert result.has_header_row is True

    @pytest.mark.asyncio
    async def test_probe_schema_file_not_found(self) -> None:
        """probe_schema() raises AdapterError for missing file."""
        adapter = CSVAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.probe_schema("nonexistent.csv")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND


class TestCSVAdapterReadDataframe:
    """Test AC-3.3: Reading requirements."""

    @pytest.mark.asyncio
    async def test_read_dataframe_returns_tuple(self) -> None:
        """AC-3.3.1: read_dataframe() returns (DataFrame, ReadResult) tuple."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")

        df, result = await adapter.read_dataframe(file_path)

        assert isinstance(df, pl.DataFrame)
        assert result.file_path == file_path
        assert result.rows_read == 10
        assert result.columns_read == 5

    @pytest.mark.asyncio
    async def test_read_dataframe_respects_columns_option(self) -> None:
        """AC-3.3.2: read_dataframe() respects columns option."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = ReadOptions(columns=["id", "name"])

        df, result = await adapter.read_dataframe(file_path, options)

        assert list(df.columns) == ["id", "name"]
        assert result.columns_read == 2

    @pytest.mark.asyncio
    async def test_read_dataframe_respects_row_limit(self) -> None:
        """AC-3.3.3: read_dataframe() respects row_limit option."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = ReadOptions(row_limit=5)

        df, result = await adapter.read_dataframe(file_path, options)

        assert len(df) == 5
        assert result.rows_read == 5
        assert result.was_truncated is True

    @pytest.mark.asyncio
    async def test_read_dataframe_respects_skip_rows(self) -> None:
        """AC-3.3.4: read_dataframe() respects skip_rows option."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = ReadOptions(skip_rows=2)

        df, result = await adapter.read_dataframe(file_path, options)

        # Should skip first 2 data rows (after header)
        assert len(df) == 8

    @pytest.mark.asyncio
    async def test_read_dataframe_handles_null_values(self) -> None:
        """AC-3.3.7: read_dataframe() handles null values per null_values option."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = ReadOptions(null_values=["", "NULL", "null"])

        df, result = await adapter.read_dataframe(file_path, options)

        # Check that NULL and empty values are treated as null
        value_col = df["value"]
        null_count = value_col.null_count()
        assert null_count >= 2  # At least 2 null values in sample

    @pytest.mark.asyncio
    async def test_read_dataframe_file_not_found(self) -> None:
        """read_dataframe() raises AdapterError for missing file."""
        adapter = CSVAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.read_dataframe("nonexistent.csv")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND


class TestCSVAdapterStreaming:
    """Test AC-3.4: Streaming requirements."""

    @pytest.mark.asyncio
    async def test_stream_dataframe_yields_tuples(self) -> None:
        """AC-3.4.1: stream_dataframe() yields (DataFrame, StreamChunk) tuples."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = StreamOptions(chunk_size_rows=3)

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            assert isinstance(df, pl.DataFrame)
            chunks.append((df, chunk_meta))

        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_stream_dataframe_respects_chunk_size(self) -> None:
        """AC-3.4.2: stream_dataframe() respects chunk_size_rows option."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = StreamOptions(chunk_size_rows=3)

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            chunks.append((df, chunk_meta))

        # First chunks should have chunk_size rows (except possibly last)
        for df, meta in chunks[:-1]:
            assert len(df) <= 3

    @pytest.mark.asyncio
    async def test_stream_dataframe_sets_is_last_chunk(self) -> None:
        """AC-3.4.3: stream_dataframe() sets is_last_chunk correctly."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = StreamOptions(chunk_size_rows=3)

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            chunks.append(chunk_meta)

        # Only last chunk should have is_last_chunk=True
        for meta in chunks[:-1]:
            assert meta.is_last_chunk is False
        assert chunks[-1].is_last_chunk is True

    @pytest.mark.asyncio
    async def test_stream_dataframe_tracks_total_rows(self) -> None:
        """AC-3.4.4: stream_dataframe() tracks total_rows_so_far correctly."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")
        options = StreamOptions(chunk_size_rows=3)

        total_rows = 0
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            total_rows += len(df)
            assert chunk_meta.total_rows_so_far == total_rows


class TestCSVAdapterValidation:
    """Test AC-3.5: Validation requirements."""

    @pytest.mark.asyncio
    async def test_validate_file_returns_result(self) -> None:
        """AC-3.5.1: validate_file() returns FileValidationResult."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "sample.csv")

        result = await adapter.validate_file(file_path)

        assert result.file_path == file_path
        assert result.adapter_id == "csv"
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_file_detects_nonexistent(self) -> None:
        """AC-3.5.2: validate_file() detects non-existent files."""
        adapter = CSVAdapter()

        result = await adapter.validate_file("nonexistent.csv")

        assert result.is_valid is False
        assert result.error_count > 0
        assert any(i.code == "FILE_NOT_FOUND" for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_file_detects_empty(self) -> None:
        """validate_file() detects empty files."""
        adapter = CSVAdapter()
        file_path = str(FIXTURES_DIR / "empty.csv")

        result = await adapter.validate_file(file_path)

        assert result.is_valid is False
        assert any(i.code == "EMPTY_FILE" for i in result.issues)
