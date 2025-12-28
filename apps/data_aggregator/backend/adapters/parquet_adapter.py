"""Parquet file adapter for DAT.

Per ADR-0011: Profile-Driven Extraction & AdapterFactory Pattern.
Per ADR-0040: Large File Streaming Strategy (10MB threshold).
Per SPEC-DAT-0003: Adapter Interface & Registry specification.

This adapter handles Apache Parquet file format using Polars
for efficient data processing.

Supported formats:
- Parquet (.parquet, .pq)

Features:
- Native Polars streaming via scan_parquet
- Schema discovery from Parquet metadata (no data scan needed)
- Column pruning and row group filtering
- Efficient memory usage for large files
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncIterator

import polars as pl

from shared.contracts.dat.adapter import (
    AdapterCapabilities,
    AdapterError,
    AdapterErrorCode,
    AdapterMetadata,
    BaseFileAdapter,
    ColumnInfo,
    CompressionType,
    FileValidationResult,
    InferredDataType,
    ReadOptions,
    ReadResult,
    SchemaProbeResult,
    StreamChunk,
    StreamOptions,
    ValidationIssue,
    ValidationSeverity,
)

__version__ = "1.0.0"


def _polars_dtype_to_inferred(dtype: pl.DataType) -> InferredDataType:
    """Convert Polars dtype to InferredDataType enum.

    Args:
        dtype: Polars data type.

    Returns:
        Corresponding InferredDataType enum value.
    """
    dtype_str = str(dtype).lower()

    if "int" in dtype_str:
        return InferredDataType.INTEGER
    elif "float" in dtype_str or "decimal" in dtype_str:
        return InferredDataType.FLOAT
    elif "bool" in dtype_str:
        return InferredDataType.BOOLEAN
    elif "datetime" in dtype_str:
        return InferredDataType.DATETIME
    elif "date" in dtype_str:
        return InferredDataType.DATE
    elif "time" in dtype_str:
        return InferredDataType.TIME
    elif "binary" in dtype_str:
        return InferredDataType.BINARY
    elif "null" in dtype_str:
        return InferredDataType.NULL
    elif "str" in dtype_str or "utf8" in dtype_str:
        return InferredDataType.STRING
    else:
        return InferredDataType.UNKNOWN


class ParquetAdapter(BaseFileAdapter):
    """Adapter for Apache Parquet files.

    Uses Polars for efficient data processing. Parquet files have schema
    embedded in metadata, making schema probing extremely fast.

    Parquet format supports efficient streaming via row group iteration.

    Attributes:
        _metadata: Cached adapter metadata.

    Example:
        >>> adapter = ParquetAdapter()
        >>> result = await adapter.probe_schema("data.parquet")
        >>> df, read_result = await adapter.read_dataframe("data.parquet")
    """

    def __init__(self) -> None:
        """Initialize the Parquet adapter."""
        self._metadata = AdapterMetadata(
            adapter_id="parquet",
            name="Parquet Adapter",
            version=__version__,
            file_extensions=[".parquet", ".pq"],
            mime_types=[
                "application/vnd.apache.parquet",
                "application/x-parquet",
            ],
            capabilities=AdapterCapabilities(
                supports_streaming=True,
                supports_schema_inference=True,
                supports_random_access=True,
                supports_column_selection=True,
                max_recommended_file_size_mb=10000,  # Parquet handles large files
                supported_compressions=[
                    CompressionType.NONE,
                    CompressionType.SNAPPY,
                    CompressionType.GZIP,
                    CompressionType.ZSTD,
                    CompressionType.LZ4,
                ],
                supports_multiple_sheets=False,
            ),
            description="Parse Apache Parquet files with native streaming support",
            author="system",
            icon="file-archive",
        )

    @property
    def metadata(self) -> AdapterMetadata:
        """Return adapter metadata for registry.

        Returns:
            AdapterMetadata with adapter ID, capabilities, etc.
        """
        return self._metadata

    async def probe_schema(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> SchemaProbeResult:
        """Probe Parquet file to discover schema from metadata.

        Parquet files have schema embedded in metadata, so this operation
        is extremely fast - no data reading required.

        Args:
            file_path: Relative path to the Parquet file.
            options: Optional read options (mostly ignored for Parquet).

        Returns:
            SchemaProbeResult with column info and metadata.

        Raises:
            AdapterError: If file cannot be probed.
        """
        start_time = datetime.now(timezone.utc)
        options = options or ReadOptions()
        errors: list[str] = []
        warnings: list[str] = []

        try:
            path = Path(file_path)
            if not path.exists():
                raise AdapterError(
                    code=AdapterErrorCode.FILE_NOT_FOUND,
                    message=f"File not found: {file_path}",
                    file_path=file_path,
                    adapter_id=self._metadata.adapter_id,
                )

            file_size = path.stat().st_size

            def _probe_schema() -> tuple[pl.Schema, int]:
                # Use scan_parquet for schema - doesn't read data
                lf = pl.scan_parquet(path)
                schema = lf.collect_schema()
                # Get row count from metadata
                row_count = lf.select(pl.len()).collect().item()
                return schema, row_count

            schema, row_count = await asyncio.to_thread(_probe_schema)

            # Build column info from schema
            columns: list[ColumnInfo] = []
            for i, (col_name, dtype) in enumerate(schema.items()):
                columns.append(
                    ColumnInfo(
                        name=col_name,
                        position=i,
                        inferred_type=_polars_dtype_to_inferred(dtype),
                        nullable=True,  # Parquet columns are nullable by default
                        sample_values=[],  # Schema-only probe
                        null_count=0,  # Unknown from schema-only probe
                        distinct_count_estimate=None,
                    )
                )

            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            return SchemaProbeResult(
                file_path=file_path,
                file_size_bytes=file_size,
                adapter_id=self._metadata.adapter_id,
                columns=columns,
                row_count_estimate=row_count,
                row_count_exact=True,  # Parquet metadata has exact count
                encoding_detected=None,  # Binary format
                delimiter_detected=None,
                has_header_row=True,  # Parquet has column names in schema
                sheets=None,
                compression_detected=None,  # Could detect from metadata
                probed_at=start_time,
                probe_duration_ms=duration_ms,
                sample_rows_read=0,  # Schema-only probe
                errors=errors,
                warnings=warnings,
            )

        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.SCHEMA_INFERENCE_FAILED,
                message=f"Failed to probe Parquet schema: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def read_dataframe(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> tuple[pl.DataFrame, ReadResult]:
        """Read Parquet file into a Polars DataFrame.

        Args:
            file_path: Relative path to the Parquet file.
            options: Read options (columns, row_limit, etc.).

        Returns:
            Tuple of (DataFrame, ReadResult metadata).

        Raises:
            AdapterError: If file cannot be read.
        """
        start_time = datetime.now(timezone.utc)
        options = options or ReadOptions()
        warnings: list[str] = []

        try:
            path = Path(file_path)
            if not path.exists():
                raise AdapterError(
                    code=AdapterErrorCode.FILE_NOT_FOUND,
                    message=f"File not found: {file_path}",
                    file_path=file_path,
                    adapter_id=self._metadata.adapter_id,
                )

            file_size = path.stat().st_size

            def _read_parquet() -> pl.DataFrame:
                read_kwargs: dict[str, Any] = {}

                # Column selection (Parquet supports column pruning)
                if options.columns:
                    read_kwargs["columns"] = options.columns

                df = pl.read_parquet(path, **read_kwargs)

                # Exclude columns if specified
                if options.exclude_columns:
                    cols_to_keep = [
                        c for c in df.columns if c not in options.exclude_columns
                    ]
                    df = df.select(cols_to_keep)

                # Apply skip_rows
                if options.skip_rows > 0:
                    df = df.slice(options.skip_rows)

                # Apply row_limit
                if options.row_limit and len(df) > options.row_limit:
                    df = df.head(options.row_limit)

                return df

            df = await asyncio.to_thread(_read_parquet)

            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            was_truncated = (
                options.row_limit is not None and len(df) >= options.row_limit
            )

            result = ReadResult(
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                rows_read=len(df),
                columns_read=len(df.columns),
                bytes_read=file_size,
                read_duration_ms=duration_ms,
                warnings=warnings,
                was_truncated=was_truncated,
            )

            return df, result

        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.PARSE_ERROR,
                message=f"Failed to read Parquet file: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def stream_dataframe(
        self,
        file_path: str,
        options: StreamOptions | None = None,
    ) -> AsyncIterator[tuple[pl.DataFrame, StreamChunk]]:
        """Stream Parquet file as chunks for large file processing.

        Uses Polars lazy API to efficiently stream data in chunks.

        Args:
            file_path: Relative path to the Parquet file.
            options: Stream options (chunk_size, columns, etc.).

        Yields:
            Tuple of (DataFrame chunk, StreamChunk metadata).

        Raises:
            AdapterError: If file cannot be streamed.
        """
        options = options or StreamOptions()

        try:
            path = Path(file_path)
            if not path.exists():
                raise AdapterError(
                    code=AdapterErrorCode.FILE_NOT_FOUND,
                    message=f"File not found: {file_path}",
                    file_path=file_path,
                    adapter_id=self._metadata.adapter_id,
                )

            # Create lazy frame
            def _create_lazy_frame() -> pl.LazyFrame:
                lf = pl.scan_parquet(path)
                if options.columns:
                    lf = lf.select(options.columns)
                return lf

            lf = await asyncio.to_thread(_create_lazy_frame)

            # Get total row count
            def _get_row_count() -> int:
                return lf.select(pl.len()).collect().item()

            total_rows = await asyncio.to_thread(_get_row_count)

            # Stream in chunks
            chunk_size = options.chunk_size_rows
            total_rows_so_far = 0
            chunk_index = 0

            while total_rows_so_far < total_rows:
                start_time = datetime.now(timezone.utc)

                def _read_chunk(offset: int, limit: int) -> pl.DataFrame:
                    return lf.slice(offset, limit).collect()

                chunk_df = await asyncio.to_thread(
                    _read_chunk, total_rows_so_far, chunk_size
                )

                end_time = datetime.now(timezone.utc)
                duration_ms = (end_time - start_time).total_seconds() * 1000

                rows_in_chunk = len(chunk_df)
                total_rows_so_far += rows_in_chunk
                is_last = total_rows_so_far >= total_rows

                chunk_meta = StreamChunk(
                    chunk_index=chunk_index,
                    rows_in_chunk=rows_in_chunk,
                    total_rows_so_far=total_rows_so_far,
                    is_last_chunk=is_last,
                    chunk_duration_ms=duration_ms,
                )

                yield chunk_df, chunk_meta

                chunk_index += 1

                if rows_in_chunk < chunk_size:
                    break

        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.PARSE_ERROR,
                message=f"Failed to stream Parquet file: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def validate_file(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> FileValidationResult:
        """Validate Parquet file can be processed by this adapter.

        Args:
            file_path: Relative path to the Parquet file.
            options: Optional read options for validation context.

        Returns:
            FileValidationResult with validation status and issues.
        """
        start_time = datetime.now(timezone.utc)
        issues: list[ValidationIssue] = []

        try:
            path = Path(file_path)

            # Check file exists
            if not path.exists():
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="FILE_NOT_FOUND",
                        message=f"File does not exist: {file_path}",
                        suggestion="Check the file path and ensure the file exists.",
                    )
                )
                return self._build_validation_result(file_path, start_time, issues)

            # Check file is not empty
            file_size = path.stat().st_size
            if file_size == 0:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="EMPTY_FILE",
                        message="File is empty",
                        suggestion="Provide a non-empty Parquet file.",
                    )
                )
                return self._build_validation_result(file_path, start_time, issues)

            # Try to read schema
            def _validate_content() -> list[ValidationIssue]:
                content_issues: list[ValidationIssue] = []
                try:
                    # Try to read schema from metadata
                    lf = pl.scan_parquet(path)
                    _ = lf.collect_schema()
                except Exception as e:
                    error_msg = str(e).lower()
                    if "magic" in error_msg or "parquet" in error_msg:
                        content_issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                code="INVALID_PARQUET",
                                message="File is not a valid Parquet file",
                                suggestion="Ensure the file is a valid Parquet format.",
                            )
                        )
                    else:
                        content_issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                code="PARSE_ERROR",
                                message=f"Cannot read Parquet file: {e}",
                            )
                        )
                return content_issues

            content_issues = await asyncio.to_thread(_validate_content)
            issues.extend(content_issues)

            return self._build_validation_result(file_path, start_time, issues)

        except Exception as e:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    code="VALIDATION_FAILED",
                    message=f"Validation failed: {e}",
                )
            )
            return self._build_validation_result(file_path, start_time, issues)

    def _build_validation_result(
        self,
        file_path: str,
        start_time: datetime,
        issues: list[ValidationIssue],
    ) -> FileValidationResult:
        """Build FileValidationResult from issues list.

        Args:
            file_path: Path to the validated file.
            start_time: When validation started.
            issues: List of validation issues found.

        Returns:
            FileValidationResult with computed fields.
        """
        end_time = datetime.now(timezone.utc)
        duration_ms = (end_time - start_time).total_seconds() * 1000

        error_count = sum(
            1 for i in issues if i.severity == ValidationSeverity.ERROR
        )
        warning_count = sum(
            1 for i in issues if i.severity == ValidationSeverity.WARNING
        )

        return FileValidationResult(
            file_path=file_path,
            adapter_id=self._metadata.adapter_id,
            is_valid=error_count == 0,
            issues=issues,
            error_count=error_count,
            warning_count=warning_count,
            validated_at=start_time,
            validation_duration_ms=duration_ms,
        )
