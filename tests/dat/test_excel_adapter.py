"""Unit tests for ExcelAdapter.

Per SPEC-0026: Adapter Interface & Registry specification.
Tests AC-4: Excel Adapter Requirements from ACCEPTANCE_CRITERIA_ADAPTERS.md

Note: Excel tests require actual Excel files which are not easily created
in fixtures. Some tests are marked as skip if fixtures are missing.
"""

from pathlib import Path

import pytest

from apps.data_aggregator.backend.adapters import ExcelAdapter
from shared.contracts.dat.adapter import (
    AdapterError,
    AdapterErrorCode,
    AdapterMetadata,
    BaseFileAdapter,
    StreamOptions,
)

# Fixture directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestExcelAdapterMetadata:
    """Test AC-4.1: Metadata requirements."""

    def test_adapter_id_is_excel(self) -> None:
        """AC-4.1.1: adapter_id is 'excel'."""
        adapter = ExcelAdapter()
        assert adapter.metadata.adapter_id == "excel"

    def test_file_extensions_include_xlsx_and_xls(self) -> None:
        """AC-4.1.2: file_extensions includes .xlsx and .xls."""
        adapter = ExcelAdapter()
        extensions = adapter.metadata.file_extensions

        assert ".xlsx" in extensions
        assert ".xls" in extensions

    def test_supports_streaming_is_false(self) -> None:
        """AC-4.1.3: capabilities.supports_streaming is False."""
        adapter = ExcelAdapter()
        assert adapter.metadata.capabilities.supports_streaming is False

    def test_supports_multiple_sheets_is_true(self) -> None:
        """AC-4.1.4: capabilities.supports_multiple_sheets is True."""
        adapter = ExcelAdapter()
        assert adapter.metadata.capabilities.supports_multiple_sheets is True


class TestExcelAdapterInterface:
    """Test AC-1: Adapter Interface Compliance for Excel."""

    def test_inherits_from_base_file_adapter(self) -> None:
        """AC-1.1.1: Adapter inherits from BaseFileAdapter."""
        adapter = ExcelAdapter()
        assert isinstance(adapter, BaseFileAdapter)

    def test_metadata_returns_adapter_metadata(self) -> None:
        """AC-1.1.2: metadata property returns AdapterMetadata."""
        adapter = ExcelAdapter()
        assert isinstance(adapter.metadata, AdapterMetadata)

    def test_can_handle_excel_files(self) -> None:
        """AC-1.1.7: can_handle() works for Excel files."""
        adapter = ExcelAdapter()

        assert adapter.can_handle("data.xlsx") is True
        assert adapter.can_handle("data.xls") is True
        assert adapter.can_handle("data.XLSX") is True  # Case insensitive
        assert adapter.can_handle("data.csv") is False
        assert adapter.can_handle("data.json") is False


class TestExcelAdapterStreaming:
    """Test AC-4.4: Streaming requirements."""

    @pytest.mark.asyncio
    async def test_stream_dataframe_raises_not_supported(self) -> None:
        """AC-4.4.1: stream_dataframe() raises AdapterError with STREAMING_NOT_SUPPORTED."""
        adapter = ExcelAdapter()

        with pytest.raises(AdapterError) as exc_info:
            async for _ in adapter.stream_dataframe("data.xlsx"):
                pass

        assert exc_info.value.code == AdapterErrorCode.STREAMING_NOT_SUPPORTED

    @pytest.mark.asyncio
    async def test_stream_error_message_indicates_excel(self) -> None:
        """AC-4.4.2: Error message indicates Excel doesn't support streaming."""
        adapter = ExcelAdapter()

        with pytest.raises(AdapterError) as exc_info:
            async for _ in adapter.stream_dataframe("data.xlsx"):
                pass

        assert "excel" in exc_info.value.message.lower()
        assert "streaming" in exc_info.value.message.lower()


class TestExcelAdapterValidation:
    """Test AC-4.5: Validation requirements."""

    @pytest.mark.asyncio
    async def test_validate_file_detects_nonexistent(self) -> None:
        """AC-4.5.2: validate_file() detects non-existent files."""
        adapter = ExcelAdapter()

        result = await adapter.validate_file("nonexistent.xlsx")

        assert result.is_valid is False
        assert result.error_count > 0
        assert any(i.code == "FILE_NOT_FOUND" for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_file_returns_result_structure(self) -> None:
        """AC-4.5.1: validate_file() returns FileValidationResult structure."""
        adapter = ExcelAdapter()

        # Even for nonexistent file, should return proper structure
        result = await adapter.validate_file("test.xlsx")

        assert result.adapter_id == "excel"
        assert result.validated_at is not None
        assert result.validation_duration_ms >= 0


class TestExcelAdapterProbeSchema:
    """Test AC-4.2: Schema Probing requirements."""

    @pytest.mark.asyncio
    async def test_probe_schema_file_not_found(self) -> None:
        """probe_schema() raises AdapterError for missing file."""
        adapter = ExcelAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.probe_schema("nonexistent.xlsx")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND


class TestExcelAdapterReadDataframe:
    """Test AC-4.3: Reading requirements."""

    @pytest.mark.asyncio
    async def test_read_dataframe_file_not_found(self) -> None:
        """read_dataframe() raises AdapterError for missing file."""
        adapter = ExcelAdapter()

        with pytest.raises(AdapterError) as exc_info:
            await adapter.read_dataframe("nonexistent.xlsx")

        assert exc_info.value.code == AdapterErrorCode.FILE_NOT_FOUND
