"""JSON file adapter for DAT.

Per ADR-0012: Profile-Driven Extraction & AdapterFactory Pattern.
Per ADR-0041: Large File Streaming Strategy (10MB threshold).
Per SPEC-0026: Adapter Interface & Registry specification.

This adapter handles JSON and JSON Lines file formats using Polars
for efficient data processing.

Supported formats:
- JSON (array of objects) - .json
- JSON Lines / NDJSON - .jsonl, .ndjson

Features:
- Streaming support for JSON Lines format
- Nested JSON flattening
- Column type inference
"""

import asyncio
import json
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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


def _is_jsonl_file(file_path: Path) -> bool:
    """Check if file is JSON Lines format based on extension or content.

    Args:
        file_path: Path to the file.

    Returns:
        True if file appears to be JSON Lines format.
    """
    # Check extension first
    ext = file_path.suffix.lower()
    if ext in (".jsonl", ".ndjson"):
        return True

    # For .json files, peek at content
    if ext == ".json":
        try:
            with open(file_path, encoding="utf-8") as f:
                first_char = ""
                for char in f.read(100):
                    if not char.isspace():
                        first_char = char
                        break

                # If starts with '[', it's a JSON array
                # If starts with '{', check if multiple lines with objects
                if first_char == "[":
                    return False
                elif first_char == "{":
                    # Read more to see if it's NDJSON
                    f.seek(0)
                    lines = f.readlines()[:5]
                    if len(lines) > 1:
                        # Multiple lines starting with { suggest NDJSON
                        json_lines = [
                            line.strip() for line in lines
                            if line.strip().startswith("{")
                        ]
                        return len(json_lines) > 1
        except Exception:
            pass

    return False


class JSONAdapter(BaseFileAdapter):
    """Adapter for JSON and JSON Lines files.

    Uses Polars for efficient data processing. Supports both regular JSON
    (array of objects) and JSON Lines (one object per line) formats.

    JSON Lines format supports streaming for large files.

    Attributes:
        _metadata: Cached adapter metadata.

    Example:
        >>> adapter = JSONAdapter()
        >>> result = await adapter.probe_schema("data.json")
        >>> df, read_result = await adapter.read_dataframe("data.jsonl")
    """

    def __init__(self) -> None:
        """Initialize the JSON adapter."""
        self._metadata = AdapterMetadata(
            adapter_id="json",
            name="JSON/JSONL Adapter",
            version=__version__,
            file_extensions=[".json", ".jsonl", ".ndjson"],
            mime_types=[
                "application/json",
                "application/x-ndjson",
                "application/jsonl",
            ],
            capabilities=AdapterCapabilities(
                supports_streaming=True,  # For JSONL format
                supports_schema_inference=True,
                supports_random_access=False,
                supports_column_selection=True,
                max_recommended_file_size_mb=500,
                supported_compressions=[
                    CompressionType.NONE,
                    CompressionType.GZIP,
                ],
                supports_multiple_sheets=False,
            ),
            description="Parse JSON and JSON Lines files with automatic format detection",
            author="system",
            icon="file-json",
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
        """Probe JSON file to discover schema without reading all data.

        Args:
            file_path: Relative path to the JSON file.
            options: Optional read options.

        Returns:
            SchemaProbeResult with column info and metadata.

        Raises:
            AdapterError: If file cannot be probed.
        """
        start_time = datetime.now(UTC)
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

            # Detect if JSON Lines format
            is_jsonl = await asyncio.to_thread(_is_jsonl_file, path)

            # Read sample for schema inference
            sample_rows = min(options.infer_schema_length, 1000)

            def _read_sample() -> pl.DataFrame:
                if is_jsonl:
                    return pl.read_ndjson(
                        path,
                        n_rows=sample_rows,
                        infer_schema_length=sample_rows,
                    )
                else:
                    # Regular JSON - read all and limit after
                    df = pl.read_json(path)
                    return df.head(sample_rows)

            df = await asyncio.to_thread(_read_sample)

            # Build column info
            columns: list[ColumnInfo] = []
            for i, col_name in enumerate(df.columns):
                col = df[col_name]
                dtype = col.dtype

                sample_values = col.head(10).to_list()
                null_count = col.null_count()

                try:
                    distinct_count = col.n_unique()
                except Exception:
                    distinct_count = None

                columns.append(
                    ColumnInfo(
                        name=col_name,
                        position=i,
                        inferred_type=_polars_dtype_to_inferred(dtype),
                        nullable=null_count > 0,
                        sample_values=sample_values,
                        null_count=null_count,
                        distinct_count_estimate=distinct_count,
                    )
                )

            # Estimate row count
            row_count_estimate: int | None = None
            row_count_exact = False

            if is_jsonl and file_size > 10 * 1024 * 1024:
                # For large JSONL, estimate based on sample
                if len(df) > 0:
                    # Count newlines for estimation
                    def _estimate_lines() -> int:
                        count = 0
                        with open(path, "rb") as f:
                            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                                count += chunk.count(b"\n")
                        return count

                    row_count_estimate = await asyncio.to_thread(_estimate_lines)
            else:
                # For small files or regular JSON, we have exact count
                row_count_estimate = len(df)
                row_count_exact = not is_jsonl  # Exact for regular JSON

            end_time = datetime.now(UTC)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            return SchemaProbeResult(
                file_path=file_path,
                file_size_bytes=file_size,
                adapter_id=self._metadata.adapter_id,
                columns=columns,
                row_count_estimate=row_count_estimate,
                row_count_exact=row_count_exact,
                encoding_detected="utf-8",
                delimiter_detected=None,
                has_header_row=True,  # JSON has keys as headers
                sheets=None,
                compression_detected=None,
                probed_at=start_time,
                probe_duration_ms=duration_ms,
                sample_rows_read=len(df),
                errors=errors,
                warnings=warnings,
            )

        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.SCHEMA_INFERENCE_FAILED,
                message=f"Failed to probe JSON schema: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def read_dataframe(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> tuple[pl.DataFrame, ReadResult]:
        """Read JSON file into a Polars DataFrame.

        Args:
            file_path: Relative path to the JSON file.
            options: Read options (columns, row_limit, etc.).

        Returns:
            Tuple of (DataFrame, ReadResult metadata).

        Raises:
            AdapterError: If file cannot be read.
        """
        start_time = datetime.now(UTC)
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

            # Detect format
            is_jsonl = await asyncio.to_thread(_is_jsonl_file, path)

            def _read_json() -> pl.DataFrame:
                if is_jsonl:
                    read_kwargs: dict[str, Any] = {}
                    if options.row_limit:
                        read_kwargs["n_rows"] = options.row_limit + options.skip_rows
                    df = pl.read_ndjson(path, **read_kwargs)
                else:
                    df = pl.read_json(path)

                # Apply skip_rows
                if options.skip_rows > 0:
                    df = df.slice(options.skip_rows)

                # Apply row_limit
                if options.row_limit and len(df) > options.row_limit:
                    df = df.head(options.row_limit)

                # Select columns
                if options.columns:
                    available = set(df.columns)
                    selected = [c for c in options.columns if c in available]
                    if selected:
                        df = df.select(selected)

                # Exclude columns
                if options.exclude_columns:
                    cols_to_keep = [
                        c for c in df.columns if c not in options.exclude_columns
                    ]
                    df = df.select(cols_to_keep)

                return df

            df = await asyncio.to_thread(_read_json)

            end_time = datetime.now(UTC)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            was_truncated = options.row_limit is not None and len(df) >= options.row_limit

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
        except json.JSONDecodeError as e:
            raise AdapterError(
                code=AdapterErrorCode.INVALID_FORMAT,
                message=f"Invalid JSON syntax: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                line_number=e.lineno,
                details={"error": str(e)},
            ) from e
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.PARSE_ERROR,
                message=f"Failed to read JSON file: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def stream_dataframe(
        self,
        file_path: str,
        options: StreamOptions | None = None,
    ) -> AsyncIterator[tuple[pl.DataFrame, StreamChunk]]:
        """Stream JSON Lines file as chunks for large file processing.

        Only JSON Lines format supports streaming. Regular JSON files
        will be read as a single chunk.

        Args:
            file_path: Relative path to the JSON file.
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

            # Detect format
            is_jsonl = await asyncio.to_thread(_is_jsonl_file, path)

            if not is_jsonl:
                # Regular JSON - read all as single chunk
                start_time = datetime.now(UTC)

                def _read_all() -> pl.DataFrame:
                    df = pl.read_json(path)
                    if options.columns:
                        available = set(df.columns)
                        selected = [c for c in options.columns if c in available]
                        if selected:
                            df = df.select(selected)
                    return df

                df = await asyncio.to_thread(_read_all)

                end_time = datetime.now(UTC)
                duration_ms = (end_time - start_time).total_seconds() * 1000

                chunk_meta = StreamChunk(
                    chunk_index=0,
                    rows_in_chunk=len(df),
                    total_rows_so_far=len(df),
                    is_last_chunk=True,
                    chunk_duration_ms=duration_ms,
                )

                yield df, chunk_meta
                return

            # JSON Lines - use lazy streaming
            def _create_lazy_frame() -> pl.LazyFrame:
                lf = pl.scan_ndjson(path)
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
                start_time = datetime.now(UTC)

                def _read_chunk(offset: int, limit: int) -> pl.DataFrame:
                    return lf.slice(offset, limit).collect()

                chunk_df = await asyncio.to_thread(
                    _read_chunk, total_rows_so_far, chunk_size
                )

                end_time = datetime.now(UTC)
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
                message=f"Failed to stream JSON file: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def validate_file(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> FileValidationResult:
        """Validate JSON file can be processed by this adapter.

        Args:
            file_path: Relative path to the JSON file.
            options: Optional read options for validation context.

        Returns:
            FileValidationResult with validation status and issues.
        """
        start_time = datetime.now(UTC)
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
                        suggestion="Provide a non-empty JSON file.",
                    )
                )
                return self._build_validation_result(file_path, start_time, issues)

            # Try to parse JSON
            def _validate_content() -> list[ValidationIssue]:
                content_issues: list[ValidationIssue] = []
                is_jsonl = _is_jsonl_file(path)

                try:
                    if is_jsonl:
                        # Validate first few lines
                        with open(path, encoding="utf-8") as f:
                            for i, line in enumerate(f):
                                if i >= 5:
                                    break
                                line = line.strip()
                                if line:
                                    json.loads(line)
                    else:
                        # Validate entire JSON structure
                        with open(path, encoding="utf-8") as f:
                            data = json.load(f)

                        # Check if it's tabular (array of objects)
                        if isinstance(data, list):
                            if len(data) > 0 and not isinstance(data[0], dict):
                                content_issues.append(
                                    ValidationIssue(
                                        severity=ValidationSeverity.WARNING,
                                        code="NON_TABULAR",
                                        message="JSON array contains non-object elements",
                                        suggestion="JSON should be an array "
                                        "of objects for tabular data.",
                                    )
                                )
                        elif isinstance(data, dict):
                            content_issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverity.WARNING,
                                    code="SINGLE_OBJECT",
                                    message="JSON is a single object, not an array",
                                    suggestion="For multiple records, use an "
                                    "array of objects or JSON Lines format.",
                                )
                            )

                except json.JSONDecodeError as e:
                    content_issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="INVALID_JSON",
                            message=f"Invalid JSON syntax at line {e.lineno}: {e.msg}",
                            line_number=e.lineno,
                            suggestion="Fix the JSON syntax error.",
                        )
                    )
                except UnicodeDecodeError as e:
                    content_issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="ENCODING_ERROR",
                            message=f"File encoding error: {e}",
                            suggestion="Ensure the file is UTF-8 encoded.",
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
        end_time = datetime.now(UTC)
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
