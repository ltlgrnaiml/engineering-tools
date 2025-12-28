"""Unit tests for JSONAdapter.

Per SPEC-DAT-0003: Adapter Interface & Registry specification.
Tests AC-5: JSON Adapter Requirements from ACCEPTANCE_CRITERIA_ADAPTERS.md
"""

from pathlib import Path

import polars as pl
import pytest

from apps.data_aggregator.backend.adapters import JSONAdapter
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


class TestJSONAdapterMetadata:
    """Test AC-5.1: Metadata requirements."""

    def test_adapter_id_is_json(self) -> None:
        """AC-5.1.1: adapter_id is 'json'."""
        adapter = JSONAdapter()
        assert adapter.metadata.adapter_id == "json"

    def test_file_extensions_include_json_jsonl_ndjson(self) -> None:
        """AC-5.1.2: file_extensions includes .json, .jsonl, .ndjson."""
        adapter = JSONAdapter()
        extensions = adapter.metadata.file_extensions

        assert ".json" in extensions
        assert ".jsonl" in extensions
        assert ".ndjson" in extensions

    def test_supports_streaming_is_true(self) -> None:
        """AC-5.1.3: capabilities.supports_streaming is True."""
        adapter = JSONAdapter()
        assert adapter.metadata.capabilities.supports_streaming is True

    def test_supports_schema_inference_is_true(self) -> None:
        """AC-5.1.4: capabilities.supports_schema_inference is True."""
        adapter = JSONAdapter()
        assert adapter.metadata.capabilities.supports_schema_inference is True


class TestJSONAdapterInterface:
    """Test AC-1: Adapter Interface Compliance for JSON."""

    def test_inherits_from_base_file_adapter(self) -> None:
        """AC-1.1.1: Adapter inherits from BaseFileAdapter."""
        adapter = JSONAdapter()
        assert isinstance(adapter, BaseFileAdapter)

    def test_metadata_returns_adapter_metadata(self) -> None:
        """AC-1.1.2: metadata property returns AdapterMetadata."""
        adapter = JSONAdapter()
        assert isinstance(adapter.metadata, AdapterMetadata)

    def test_can_handle_json_files(self) -> None:
        """AC-1.1.7: can_handle() works for JSON files."""
        adapter = JSONAdapter()

        assert adapter.can_handle("data.json") is True
        assert adapter.can_handle("data.jsonl") is True
        assert adapter.can_handle("data.ndjson") is True
        assert adapter.can_handle("data.JSON") is True  # Case insensitive
        assert adapter.can_handle("data.csv") is False
        assert adapter.can_handle("data.xlsx") is False


class TestJSONAdapterProbeSchema:
    """Test AC-5.2: Schema Probing requirements."""

    @pytest.mark.asyncio
    async def test_probe_schema_returns_schema_probe_result(self) -> None:
        """AC-5.2.1: probe_schema() returns SchemaProbeResult with columns."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.json")

        result = await adapter.probe_schema(file_path)

        assert result.file_path == file_path
        assert len(result.columns) > 0
        assert result.adapter_id == "json"

    @pytest.mark.asyncio
    async def test_probe_schema_handles_json_array(self) -> None:
        """AC-5.2.2: probe_schema() handles JSON array of objects."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.json")

        result = await adapter.probe_schema(file_path)

        column_names = [c.name for c in result.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "value" in column_names

    @pytest.mark.asyncio
    async def test_probe_schema_handles_json_lines(self) -> None:
        """AC-5.2.3: probe_schema() handles JSON Lines format."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.jsonl")

        result = await adapter.probe_schema(file_path)

        column_names = [c.name for c in result.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert result.row_count_estimate is not None

    @pytest.mark.asyncio
    async def test_probe_schema_file_not_found(self) -> None:
        """probe_schema() raises AdapterError for missing file."""
        adapter = JSONAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.probe_schema("nonexistent.json")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND


class TestJSONAdapterReadDataframe:
    """Test AC-5.3: Reading requirements."""

    @pytest.mark.asyncio
    async def test_read_dataframe_returns_tuple(self) -> None:
        """AC-5.3.1: read_dataframe() returns (DataFrame, ReadResult) tuple."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.json")

        df, result = await adapter.read_dataframe(file_path)

        assert isinstance(df, pl.DataFrame)
        assert result.file_path == file_path
        assert result.rows_read == 5
        assert result.columns_read == 4

    @pytest.mark.asyncio
    async def test_read_dataframe_handles_json_array(self) -> None:
        """AC-5.3.2: read_dataframe() handles JSON array of objects."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.json")

        df, result = await adapter.read_dataframe(file_path)

        assert len(df) == 5
        assert "id" in df.columns

    @pytest.mark.asyncio
    async def test_read_dataframe_handles_json_lines(self) -> None:
        """AC-5.3.3: read_dataframe() handles JSON Lines (.jsonl, .ndjson)."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.jsonl")

        df, result = await adapter.read_dataframe(file_path)

        assert len(df) == 5
        assert "id" in df.columns

    @pytest.mark.asyncio
    async def test_read_dataframe_respects_columns_option(self) -> None:
        """AC-5.3.4: read_dataframe() respects columns option."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.json")
        options = ReadOptions(columns=["id", "name"])

        df, result = await adapter.read_dataframe(file_path, options)

        assert list(df.columns) == ["id", "name"]

    @pytest.mark.asyncio
    async def test_read_dataframe_respects_row_limit(self) -> None:
        """AC-5.3.5: read_dataframe() respects row_limit option."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.jsonl")
        options = ReadOptions(row_limit=3)

        df, result = await adapter.read_dataframe(file_path, options)

        assert len(df) == 3
        assert result.was_truncated is True

    @pytest.mark.asyncio
    async def test_read_dataframe_file_not_found(self) -> None:
        """read_dataframe() raises AdapterError for missing file."""
        adapter = JSONAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.read_dataframe("nonexistent.json")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND


class TestJSONAdapterStreaming:
    """Test AC-5.4: Streaming requirements."""

    @pytest.mark.asyncio
    async def test_stream_dataframe_yields_tuples(self) -> None:
        """AC-5.4.1: stream_dataframe() yields (DataFrame, StreamChunk) tuples."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.jsonl")
        options = StreamOptions(chunk_size_rows=2)

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            assert isinstance(df, pl.DataFrame)
            chunks.append((df, chunk_meta))

        assert len(chunks) >= 1

    @pytest.mark.asyncio
    async def test_stream_dataframe_works_for_jsonl(self) -> None:
        """AC-5.4.2: stream_dataframe() works for JSON Lines files."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.jsonl")
        options = StreamOptions(chunk_size_rows=2)

        total_rows = 0
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            total_rows += len(df)

        assert total_rows == 5

    @pytest.mark.asyncio
    async def test_stream_dataframe_respects_chunk_size(self) -> None:
        """AC-5.4.3: stream_dataframe() respects chunk_size_rows option."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.jsonl")
        options = StreamOptions(chunk_size_rows=2)

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path, options):
            chunks.append(len(df))

        # Each chunk should be <= chunk_size
        for chunk_size in chunks:
            assert chunk_size <= 2

    @pytest.mark.asyncio
    async def test_stream_dataframe_regular_json_single_chunk(self) -> None:
        """AC-5.4.4: Regular JSON files fall back to single-chunk read."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.json")

        chunks = []
        async for df, chunk_meta in adapter.stream_dataframe(file_path):
            chunks.append(chunk_meta)

        # Regular JSON should be read as single chunk
        assert len(chunks) == 1
        assert chunks[0].is_last_chunk is True


class TestJSONAdapterValidation:
    """Test AC-5.5: Validation requirements."""

    @pytest.mark.asyncio
    async def test_validate_file_returns_result(self) -> None:
        """AC-5.5.1: validate_file() returns FileValidationResult."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "sample.json")

        result = await adapter.validate_file(file_path)

        assert result.file_path == file_path
        assert result.adapter_id == "json"
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_validate_file_detects_nonexistent(self) -> None:
        """AC-5.5.2: validate_file() detects non-existent files."""
        adapter = JSONAdapter()

        result = await adapter.validate_file("nonexistent.json")

        assert result.is_valid is False
        assert result.error_count > 0

    @pytest.mark.asyncio
    async def test_validate_file_detects_invalid_json(self) -> None:
        """AC-5.5.3: validate_file() detects invalid JSON syntax."""
        adapter = JSONAdapter()
        file_path = str(FIXTURES_DIR / "invalid.json")

        result = await adapter.validate_file(file_path)

        assert result.is_valid is False
        assert any(i.code == "INVALID_JSON" for i in result.issues)
