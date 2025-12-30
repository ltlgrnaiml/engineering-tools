"""DAT File Adapter contracts - extensible file parsing interface.

Per ADR-0012: Profile-Driven Extraction & AdapterFactory Pattern.
Per ADR-0041: Large File Streaming Strategy (10MB threshold).

This module defines the base contract for all file adapters in DAT.
Adapters are responsible for:
- Probing file schemas without reading all data
- Reading files into Polars DataFrames
- Streaming large files in chunks
- Validating file compatibility

Supported adapters (initial):
- CSV/TSV (csv_adapter.py)
- Excel (.xlsx, .xls) (excel_adapter.py)
- JSON/JSONL (json_adapter.py)

Future adapters (TODO):
- SQL Database queries
- Parquet (direct passthrough)
- Additional formats as needed

To add a new adapter:
1. Create adapter class implementing BaseFileAdapter
2. Register in AdapterRegistry via create_default_registry()
3. Add tests in tests/dat/test_adapters.py
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, AsyncIterator, Literal

from pydantic import BaseModel, Field, field_validator

__version__ = "1.0.0"


# =============================================================================
# Adapter Capabilities & Metadata
# =============================================================================


class CompressionType(str, Enum):
    """Supported compression types for file reading."""

    NONE = "none"
    GZIP = "gzip"
    ZSTD = "zstd"
    LZ4 = "lz4"
    SNAPPY = "snappy"
    BZ2 = "bz2"


class AdapterCapabilities(BaseModel):
    """Capabilities of a file adapter.

    Used by the registry to determine which adapter to use
    and what features are available.
    """

    supports_streaming: bool = Field(
        False,
        description="Can process files in chunks without loading fully into memory",
    )
    supports_schema_inference: bool = Field(
        True,
        description="Can automatically detect column types",
    )
    supports_random_access: bool = Field(
        False,
        description="Can read arbitrary row ranges efficiently (e.g., via LIMIT/OFFSET)",
    )
    supports_column_selection: bool = Field(
        True,
        description="Can read only specified columns without loading all data",
    )
    max_recommended_file_size_mb: int | None = Field(
        None,
        ge=1,
        description="Maximum file size (MB) recommended for this adapter. None = no limit.",
    )
    supported_compressions: list[CompressionType] = Field(
        default_factory=list,
        description="Compression formats this adapter can handle",
    )
    supports_multiple_sheets: bool = Field(
        False,
        description="Can handle multiple sheets/tables in one file (e.g., Excel)",
    )


class AdapterMetadata(BaseModel):
    """Metadata about a file adapter for registry and UI display.

    Per ADR-0012: Adapters are selected via handles-first pattern.
    The registry uses file_extensions and mime_types to auto-select adapters.
    """

    adapter_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[a-z][a-z0-9_]*$",
        description="Unique identifier for this adapter (e.g., 'csv', 'excel', 'json')",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name for UI display",
    )
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Adapter version (semver format)",
    )
    file_extensions: list[str] = Field(
        ...,
        min_length=1,
        description="File extensions this adapter handles (with dot, e.g., '.csv')",
    )
    mime_types: list[str] = Field(
        default_factory=list,
        description="MIME types this adapter handles",
    )
    capabilities: AdapterCapabilities = Field(
        default_factory=AdapterCapabilities,
        description="What this adapter can do",
    )
    description: str = Field(
        "",
        max_length=500,
        description="Brief description of the adapter",
    )
    author: str = Field(
        "system",
        description="Adapter author for attribution",
    )
    icon: str | None = Field(
        None,
        description="Icon identifier for UI (e.g., 'file-spreadsheet')",
    )

    @field_validator("file_extensions")
    @classmethod
    def validate_extensions(cls, v: list[str]) -> list[str]:
        """Ensure extensions start with dot and are lowercase."""
        result = []
        for ext in v:
            if not ext.startswith("."):
                ext = f".{ext}"
            result.append(ext.lower())
        return result


# =============================================================================
# Schema Probing Contracts
# =============================================================================


class InferredDataType(str, Enum):
    """Data types that can be inferred from file contents."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    BINARY = "binary"
    NULL = "null"
    UNKNOWN = "unknown"


class ColumnInfo(BaseModel):
    """Information about a discovered column.

    Populated during schema probing to help users understand
    their data before full parsing.
    """

    name: str = Field(..., description="Column name as found in file")
    position: int = Field(..., ge=0, description="0-indexed column position")
    inferred_type: InferredDataType = Field(
        InferredDataType.UNKNOWN,
        description="Best-guess data type based on sample",
    )
    nullable: bool = Field(
        True,
        description="Whether null/empty values were found",
    )
    sample_values: list[Any] = Field(
        default_factory=list,
        max_length=10,
        description="Sample values from the column (max 10)",
    )
    null_count: int = Field(
        0,
        ge=0,
        description="Number of null values in sample",
    )
    distinct_count_estimate: int | None = Field(
        None,
        ge=0,
        description="Estimated distinct values (from sample)",
    )
    min_value: Any = Field(None, description="Minimum value found in sample")
    max_value: Any = Field(None, description="Maximum value found in sample")
    avg_length: float | None = Field(
        None,
        ge=0,
        description="Average string length for string columns",
    )


class SheetInfo(BaseModel):
    """Information about a sheet/table in a multi-sheet file.

    Used for Excel files and similar formats.
    """

    sheet_name: str = Field(..., description="Sheet/table name")
    sheet_index: int = Field(..., ge=0, description="0-indexed sheet position")
    row_count_estimate: int | None = Field(None, ge=0)
    column_count: int | None = Field(None, ge=0)
    is_empty: bool = Field(False, description="Whether sheet appears empty")


class SchemaProbeResult(BaseModel):
    """Result of probing a file's schema.

    Per ADR-0041: Schema probing is always fast regardless of file size.
    Only reads enough data to infer schema (typically first 1000 rows).
    """

    # File metadata
    file_path: str = Field(..., description="Path to the probed file (relative)")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    adapter_id: str = Field(..., description="Adapter that performed the probe")

    # Schema information
    columns: list[ColumnInfo] = Field(
        default_factory=list,
        description="Discovered columns with type information",
    )
    row_count_estimate: int | None = Field(
        None,
        ge=0,
        description="Estimated total rows (may be exact for small files)",
    )
    row_count_exact: bool = Field(
        False,
        description="Whether row_count_estimate is exact or estimated",
    )

    # Format-specific metadata
    encoding_detected: str | None = Field(
        None,
        description="Detected file encoding (e.g., 'utf-8', 'latin-1')",
    )
    delimiter_detected: str | None = Field(
        None,
        description="Detected delimiter for CSV/TSV files",
    )
    has_header_row: bool = Field(
        True,
        description="Whether first row appears to be headers",
    )
    sheets: list[SheetInfo] | None = Field(
        None,
        description="Sheet information for multi-sheet files (Excel)",
    )
    compression_detected: CompressionType | None = Field(
        None,
        description="Detected compression format",
    )

    # Probe metadata
    probed_at: datetime = Field(..., description="When the probe was performed")
    probe_duration_ms: float = Field(..., ge=0, description="How long the probe took")
    sample_rows_read: int = Field(
        0,
        ge=0,
        description="Number of rows read during probe",
    )

    # Errors/warnings
    errors: list[str] = Field(
        default_factory=list,
        description="Errors encountered during probing",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warnings (non-fatal issues)",
    )

    @property
    def is_valid(self) -> bool:
        """Check if probe was successful (no errors)."""
        return len(self.errors) == 0

    @property
    def column_count(self) -> int:
        """Number of columns discovered."""
        return len(self.columns)


# =============================================================================
# File Validation Contracts
# =============================================================================


class ValidationSeverity(str, Enum):
    """Severity level for validation issues."""

    ERROR = "error"  # Cannot process file
    WARNING = "warning"  # Can process but may have issues
    INFO = "info"  # Informational only


class ValidationIssue(BaseModel):
    """A single validation issue found in a file."""

    severity: ValidationSeverity
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable description")
    line_number: int | None = Field(None, ge=1, description="Line number if applicable")
    column_name: str | None = Field(None, description="Column name if applicable")
    suggestion: str | None = Field(None, description="Suggested fix")


class FileValidationResult(BaseModel):
    """Result of validating a file for processing.

    Validation checks:
    - File exists and is readable
    - File format matches expected adapter
    - File is not corrupted
    - File size is within limits
    - Character encoding is valid
    """

    file_path: str
    adapter_id: str
    is_valid: bool = Field(..., description="Overall validation result")
    issues: list[ValidationIssue] = Field(default_factory=list)

    # Quick stats
    error_count: int = Field(0, ge=0)
    warning_count: int = Field(0, ge=0)

    # Validation timing
    validated_at: datetime
    validation_duration_ms: float = Field(..., ge=0)

    @property
    def can_process(self) -> bool:
        """Check if file can be processed (no errors)."""
        return self.error_count == 0


# =============================================================================
# Read Options Contracts
# =============================================================================


class ReadOptions(BaseModel):
    """Options for reading a file into a DataFrame.

    These are adapter-agnostic options. Each adapter may support
    additional format-specific options via the `extra` field.
    """

    # Column selection
    columns: list[str] | None = Field(
        None,
        description="Columns to read (None = all columns)",
    )
    exclude_columns: list[str] | None = Field(
        None,
        description="Columns to exclude",
    )

    # Row limiting
    row_limit: int | None = Field(
        None,
        ge=1,
        description="Maximum rows to read (None = all rows)",
    )
    skip_rows: int = Field(
        0,
        ge=0,
        description="Number of rows to skip from start",
    )

    # Type handling
    infer_schema_length: int = Field(
        1000,
        ge=100,
        le=100000,
        description="Number of rows to use for schema inference",
    )
    null_values: list[str] = Field(
        default_factory=lambda: ["", "NULL", "null", "NA", "N/A", "NaN", "nan", "None"],
        description="Values to interpret as null",
    )

    # Encoding
    encoding: str = Field(
        "utf-8",
        description="File encoding (adapter may auto-detect)",
    )
    encoding_errors: Literal["strict", "ignore", "replace"] = Field(
        "replace",
        description="How to handle encoding errors",
    )

    # Format-specific extras
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Adapter-specific options (e.g., delimiter for CSV)",
    )


class StreamOptions(BaseModel):
    """Options for streaming a file in chunks.

    Per ADR-0041: Files > 10MB should use streaming mode.
    """

    chunk_size_rows: int = Field(
        50000,
        ge=1,
        le=1000000,
        description="Number of rows per chunk",
    )
    columns: list[str] | None = Field(
        None,
        description="Columns to read (None = all)",
    )
    max_memory_mb: int = Field(
        200,
        ge=50,
        le=2000,
        description="Maximum memory to use for buffering",
    )
    extra: dict[str, Any] = Field(
        default_factory=dict,
        description="Adapter-specific options",
    )


# =============================================================================
# Adapter Read Results
# =============================================================================


class ReadResult(BaseModel):
    """Result metadata from reading a file.

    The actual DataFrame is returned separately; this contains
    metadata about the read operation.
    """

    file_path: str
    adapter_id: str
    rows_read: int = Field(..., ge=0)
    columns_read: int = Field(..., ge=0)
    bytes_read: int = Field(..., ge=0)
    read_duration_ms: float = Field(..., ge=0)
    warnings: list[str] = Field(default_factory=list)
    was_truncated: bool = Field(
        False,
        description="Whether row_limit caused truncation",
    )


class StreamChunk(BaseModel):
    """Metadata for a single chunk during streaming.

    The actual DataFrame chunk is yielded separately.
    """

    chunk_index: int = Field(..., ge=0)
    rows_in_chunk: int = Field(..., ge=0)
    total_rows_so_far: int = Field(..., ge=0)
    is_last_chunk: bool = Field(False)
    chunk_duration_ms: float = Field(..., ge=0)


# =============================================================================
# Base Adapter Interface (Abstract)
# =============================================================================


class BaseFileAdapter(ABC):
    """Base class for all file adapters.

    Per ADR-0012: All adapters must implement this interface.
    Per ADR-0041: Adapters must support streaming for large files.

    Implementation notes:
    - All methods are async for consistency with FastAPI
    - Methods should raise AdapterError on failure
    - File paths are always relative (per ADR-0018 path-safety)

    Example implementation:
        class CSVAdapter(BaseFileAdapter):
            @property
            def metadata(self) -> AdapterMetadata:
                return AdapterMetadata(
                    adapter_id="csv",
                    name="CSV Adapter",
                    version="1.0.0",
                    file_extensions=[".csv", ".tsv"],
                    ...
                )

            async def probe_schema(self, file_path, options=None):
                # Implementation using polars.scan_csv
                ...
    """

    @property
    @abstractmethod
    def metadata(self) -> AdapterMetadata:
        """Return adapter metadata for registry.

        Returns:
            AdapterMetadata with adapter ID, capabilities, etc.
        """
        ...

    @abstractmethod
    async def probe_schema(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> SchemaProbeResult:
        """Probe file to discover schema without reading all data.

        This should be fast regardless of file size - only read
        enough rows to infer the schema (typically 1000 rows).

        Args:
            file_path: Relative path to the file
            options: Optional read options (only encoding/extras used)

        Returns:
            SchemaProbeResult with column info and metadata

        Raises:
            AdapterError: If file cannot be probed
        """
        ...

    @abstractmethod
    async def read_dataframe(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> tuple["DataFrameType", ReadResult]:
        """Read file into a Polars DataFrame.

        For files > 10MB, consider using stream_dataframe instead.

        Args:
            file_path: Relative path to the file
            options: Read options (columns, row_limit, etc.)

        Returns:
            Tuple of (DataFrame, ReadResult metadata)

        Raises:
            AdapterError: If file cannot be read
            MemoryError: If file is too large for available memory
        """
        ...

    @abstractmethod
    async def stream_dataframe(
        self,
        file_path: str,
        options: StreamOptions | None = None,
    ) -> AsyncIterator[tuple["DataFrameType", StreamChunk]]:
        """Stream file as chunks for large file processing.

        Per ADR-0041: This is the preferred method for files > 10MB.

        Args:
            file_path: Relative path to the file
            options: Stream options (chunk_size, columns, etc.)

        Yields:
            Tuple of (DataFrame chunk, StreamChunk metadata)

        Raises:
            AdapterError: If file cannot be streamed
        """
        ...

    @abstractmethod
    async def validate_file(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> FileValidationResult:
        """Validate file can be processed by this adapter.

        Performs quick checks without reading entire file:
        - File exists and is readable
        - File format matches adapter expectations
        - File is not corrupted (check header/magic bytes)
        - Encoding is valid

        Args:
            file_path: Relative path to the file
            options: Optional read options for validation context

        Returns:
            FileValidationResult with validation status and issues
        """
        ...

    def can_handle(self, file_path: str) -> bool:
        """Check if this adapter can handle a file based on extension.

        Args:
            file_path: Path to check

        Returns:
            True if file extension matches this adapter
        """
        from pathlib import Path

        ext = Path(file_path).suffix.lower()
        return ext in self.metadata.file_extensions


# =============================================================================
# Adapter Registry Contracts
# =============================================================================


class AdapterRegistryEntry(BaseModel):
    """Entry in the adapter registry for serialization."""

    adapter_id: str
    metadata: AdapterMetadata
    registered_at: datetime
    is_builtin: bool = Field(
        True,
        description="Whether this is a built-in adapter",
    )


class AdapterRegistryState(BaseModel):
    """Serializable state of the adapter registry.

    Used for DevTools display and debugging.
    """

    adapters: list[AdapterRegistryEntry] = Field(default_factory=list)
    extension_map: dict[str, str] = Field(
        default_factory=dict,
        description="File extension -> adapter_id mapping",
    )
    mime_map: dict[str, str] = Field(
        default_factory=dict,
        description="MIME type -> adapter_id mapping",
    )
    last_updated: datetime | None = None


# =============================================================================
# Adapter Errors
# =============================================================================


class AdapterErrorCode(str, Enum):
    """Error codes for adapter operations."""

    FILE_NOT_FOUND = "file_not_found"
    FILE_NOT_READABLE = "file_not_readable"
    INVALID_FORMAT = "invalid_format"
    ENCODING_ERROR = "encoding_error"
    SCHEMA_INFERENCE_FAILED = "schema_inference_failed"
    MEMORY_EXCEEDED = "memory_exceeded"
    STREAMING_NOT_SUPPORTED = "streaming_not_supported"
    COLUMN_NOT_FOUND = "column_not_found"
    PARSE_ERROR = "parse_error"
    TIMEOUT = "timeout"
    UNKNOWN = "unknown"


class AdapterError(Exception):
    """Exception raised by adapter operations.

    Per ADR-0027: Errors should be structured for programmatic handling.

    This is both an Exception (can be raised) and contains structured
    error information for programmatic handling.

    Attributes:
        code: Error code enum value.
        message: Human-readable error message.
        file_path: Path to the file that caused the error.
        adapter_id: ID of the adapter that raised the error.
        line_number: Line number where error occurred (if applicable).
        column_name: Column name related to error (if applicable).
        details: Additional error details.
        recoverable: Whether the operation can be retried.
    """

    def __init__(
        self,
        code: AdapterErrorCode,
        message: str,
        file_path: str | None = None,
        adapter_id: str | None = None,
        line_number: int | None = None,
        column_name: str | None = None,
        details: dict[str, Any] | None = None,
        recoverable: bool = False,
    ) -> None:
        """Initialize the adapter error.

        Args:
            code: Error code enum value.
            message: Human-readable error message.
            file_path: Path to the file that caused the error.
            adapter_id: ID of the adapter that raised the error.
            line_number: Line number where error occurred.
            column_name: Column name related to error.
            details: Additional error details.
            recoverable: Whether the operation can be retried.
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.file_path = file_path
        self.adapter_id = adapter_id
        self.line_number = line_number
        self.column_name = column_name
        self.details = details or {}
        self.recoverable = recoverable

    def __str__(self) -> str:
        """Return string representation of the error."""
        return f"[{self.code.value}] {self.message}"

    def __repr__(self) -> str:
        """Return repr of the error."""
        return (
            f"AdapterError(code={self.code!r}, message={self.message!r}, "
            f"file_path={self.file_path!r}, adapter_id={self.adapter_id!r})"
        )


# =============================================================================
# Type Aliases (for documentation)
# =============================================================================

# Polars DataFrame - actual type comes from polars import at runtime
DataFrameType = Any  # polars.DataFrame

# LazyFrame for streaming operations
LazyFrameType = Any  # polars.LazyFrame
