"""Unit tests for ParquetAdapter.

Per SPEC-0026: Adapter Interface & Registry specification.
Tests P0-2.8: Parquet Adapter Requirements.
"""

from pathlib import Path

import polars as pl
import pytest

from apps.data_aggregator.backend.adapters import ParquetAdapter
from shared.contracts.dat.adapter import (
    AdapterError,
    AdapterErrorCode,
    AdapterMetadata,
    BaseFileAdapter,
    ReadOptions,
    StreamOptions,
)

# Fixture directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestParquetAdapterMetadata:
    """Test Parquet adapter metadata requirements."""

    def test_adapter_id_is_parquet(self) -> None:
        """adapter_id is 'parquet'."""
        adapter = ParquetAdapter()
        assert adapter.metadata.adapter_id == "parquet"

    def test_file_extensions_include_parquet_and_pq(self) -> None:
        """file_extensions includes .parquet and .pq."""
        adapter = ParquetAdapter()
        extensions = adapter.metadata.file_extensions

        assert ".parquet" in extensions
        assert ".pq" in extensions

    def test_supports_streaming_is_true(self) -> None:
        """capabilities.supports_streaming is True."""
        adapter = ParquetAdapter()
        assert adapter.metadata.capabilities.supports_streaming is True

    def test_supports_schema_inference_is_true(self) -> None:
        """capabilities.supports_schema_inference is True."""
        adapter = ParquetAdapter()
        assert adapter.metadata.capabilities.supports_schema_inference is True


class TestParquetAdapterInterface:
    """Test Adapter Interface Compliance for Parquet."""

    def test_inherits_from_base_file_adapter(self) -> None:
        """Adapter inherits from BaseFileAdapter."""
        adapter = ParquetAdapter()
        assert isinstance(adapter, BaseFileAdapter)

    def test_metadata_returns_adapter_metadata(self) -> None:
        """metadata property returns AdapterMetadata."""
        adapter = ParquetAdapter()
        assert isinstance(adapter.metadata, AdapterMetadata)

    def test_can_handle_parquet_files(self) -> None:
        """can_handle() works for Parquet files."""
        adapter = ParquetAdapter()

        assert adapter.can_handle("data.parquet") is True
        assert adapter.can_handle("data.pq") is True
        assert adapter.can_handle("data.PARQUET") is True  # Case insensitive
        assert adapter.can_handle("data.csv") is False
        assert adapter.can_handle("data.json") is False


class TestParquetAdapterProbeSchema:
    """Test schema probing requirements."""

    @pytest.mark.asyncio
    async def test_probe_schema_returns_schema_probe_result(self) -> None:
        """probe_schema() returns SchemaProbeResult with columns."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")

        result = await adapter.probe_schema(file_path)

        assert result.file_path == file_path
        assert len(result.columns) > 0
        assert result.adapter_id == "parquet"

    @pytest.mark.asyncio
    async def test_probe_schema_has_exact_row_count(self) -> None:
        """probe_schema() returns exact row count from metadata."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")

        result = await adapter.probe_schema(file_path)

        assert result.row_count_exact is True
        assert result.row_count_estimate == 5

    @pytest.mark.asyncio
    async def test_probe_schema_file_not_found(self) -> None:
        """probe_schema() raises AdapterError for missing file."""
        adapter = ParquetAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.probe_schema("nonexistent.parquet")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND


class TestParquetAdapterReadDataframe:
    """Test reading requirements."""

    @pytest.mark.asyncio
    async def test_read_dataframe_returns_tuple(self) -> None:
        """read_dataframe() returns (DataFrame, ReadResult) tuple."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")

        df, result = await adapter.read_dataframe(file_path)

        assert isinstance(df, pl.DataFrame)
        assert result.file_path == file_path
        assert result.rows_read == 5
        assert result.columns_read == 4

    @pytest.mark.asyncio
    async def test_read_dataframe_respects_columns_option(self) -> None:
        """read_dataframe() respects columns option."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")
        options = ReadOptions(columns=["id", "name"])

        df, result = await adapter.read_dataframe(file_path, options)

        assert list(df.columns) == ["id", "name"]
        assert result.columns_read == 2

    @pytest.mark.asyncio
    async def test_read_dataframe_respects_row_limit(self) -> None:
        """read_dataframe() respects row_limit option."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")
        options = ReadOptions(row_limit=3)

        df, result = await adapter.read_dataframe(file_path, options)

        assert len(df) == 3
        assert result.was_truncated is True

    @pytest.mark.asyncio
    async def test_read_dataframe_file_not_found(self) -> None:
        """read_dataframe() raises AdapterError for missing file."""
        adapter = ParquetAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.read_dataframe("nonexistent.parquet")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND


class TestParquetAdapterStreaming:
    """Test streaming requirements."""

    @pytest.mark.asyncio
    async def test_stream_dataframe_yields_tuples(self) -> None:
        """stream_dataframe() yields (DataFrame, StreamChunk) tuples."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")
        options = StreamOptions(chunk_size_rows=2)

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            assert isinstance(df, pl.DataFrame)
            chunks.append((df, chunk_meta))

        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_stream_dataframe_respects_chunk_size(self) -> None:
        """stream_dataframe() respects chunk_size_rows option."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")
        options = StreamOptions(chunk_size_rows=2)

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            chunks.append(len(df))

        # Each chunk should be <= chunk_size
        for chunk_size in chunks:
            assert chunk_size <= 2

    @pytest.mark.asyncio
    async def test_stream_dataframe_tracks_total_rows(self) -> None:
        """stream_dataframe() tracks total_rows_so_far correctly."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")
        options = StreamOptions(chunk_size_rows=2)

        total_rows = 0
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            total_rows += len(df)
            assert chunk_meta.total_rows_so_far == total_rows


class TestParquetAdapterValidation:
    """Test validation requirements."""

    @pytest.mark.asyncio
    async def test_validate_file_returns_result(self) -> None:
        """validate_file() returns FileValidationResult."""
        adapter = ParquetAdapter()
        file_path = str(FIXTURES_DIR / "sample.parquet")

        result = await adapter.validate_file(file_path)

        assert result.file_path == file_path
        assert result.adapter_id == "parquet"
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_file_detects_nonexistent(self) -> None:
        """validate_file() detects non-existent files."""
        adapter = ParquetAdapter()

        result = await adapter.validate_file("nonexistent.parquet")

        assert result.is_valid is False
        assert result.error_count > 0
        assert any(i.code == "FILE_NOT_FOUND" for i in result.issues)
