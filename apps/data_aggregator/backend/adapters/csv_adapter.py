"""CSV file adapter for DAT.

Per ADR-0012: Profile-Driven Extraction & AdapterFactory Pattern.
Per ADR-0041: Large File Streaming Strategy (10MB threshold).
Per SPEC-0026: Adapter Interface & Registry specification.

This adapter handles CSV and TSV file formats using Polars for efficient
data processing. Supports both eager loading and streaming for large files.

Supported formats:
- CSV (Comma-Separated Values) - .csv
- TSV (Tab-Separated Values) - .tsv

Features:
- Auto-detection of delimiter (comma, tab, semicolon, pipe)
- Auto-detection of encoding (UTF-8, Latin-1, etc.)
- Streaming support for files > 10MB
- Column type inference
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


def _detect_delimiter(file_path: Path, encoding: str = "utf-8") -> str:
    """Detect the delimiter used in a CSV file.

    Args:
        file_path: Path to the CSV file.
        encoding: File encoding.

    Returns:
        Detected delimiter character.
    """
    delimiters = [",", "\t", ";", "|"]
    counts: dict[str, int] = {d: 0 for d in delimiters}

    try:
        with open(file_path, "r", encoding=encoding, errors="replace") as f:
            # Read first few lines to detect delimiter
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                for d in delimiters:
                    counts[d] += line.count(d)
    except Exception:
        pass

    # Return delimiter with highest count, default to comma
    max_count = max(counts.values())
    if max_count == 0:
        return ","

    for d, count in counts.items():
        if count == max_count:
            return d

    return ","


def _detect_encoding(file_path: Path) -> str:
    """Detect file encoding by reading BOM or trying common encodings.

    Args:
        file_path: Path to the file.

    Returns:
        Detected encoding name.
    """
    # Check for BOM
    with open(file_path, "rb") as f:
        bom = f.read(4)

    if bom.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    elif bom.startswith(b"\xff\xfe\x00\x00"):
        return "utf-32-le"
    elif bom.startswith(b"\x00\x00\xfe\xff"):
        return "utf-32-be"
    elif bom.startswith(b"\xff\xfe"):
        return "utf-16-le"
    elif bom.startswith(b"\xfe\xff"):
        return "utf-16-be"

    # Try UTF-8 first
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.read(8192)
        return "utf-8"
    except UnicodeDecodeError:
        pass

    # Fall back to Latin-1 (always succeeds)
    return "latin-1"


class CSVAdapter(BaseFileAdapter):
    """Adapter for CSV and TSV files.

    Uses Polars for efficient data processing. Supports both eager loading
    for small files and streaming for files > 10MB.

    Attributes:
        _metadata: Cached adapter metadata.

    Example:
        >>> adapter = CSVAdapter()
        >>> result = await adapter.probe_schema("data.csv")
        >>> df, read_result = await adapter.read_dataframe("data.csv")
    """

    def __init__(self) -> None:
        """Initialize the CSV adapter."""
        self._metadata = AdapterMetadata(
            adapter_id="csv",
            name="CSV/TSV Adapter",
            version=__version__,
            file_extensions=[".csv", ".tsv"],
            mime_types=["text/csv", "text/tab-separated-values", "application/csv"],
            capabilities=AdapterCapabilities(
                supports_streaming=True,
                supports_schema_inference=True,
                supports_random_access=False,
                supports_column_selection=True,
                max_recommended_file_size_mb=None,  # No limit with streaming
                supported_compressions=[
                    CompressionType.NONE,
                    CompressionType.GZIP,
                    CompressionType.ZSTD,
                ],
                supports_multiple_sheets=False,
            ),
            description="Parse CSV and TSV files with automatic delimiter and encoding detection",
            author="system",
            icon="file-spreadsheet",
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
        """Probe CSV file to discover schema without reading all data.

        Only reads first 1000 rows by default for schema inference.
        Completes in < 5 seconds for any file size.

        Args:
            file_path: Relative path to the CSV file.
            options: Optional read options (encoding, extras).

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

            # Detect encoding and delimiter
            encoding = await asyncio.to_thread(_detect_encoding, path)
            delimiter = await asyncio.to_thread(_detect_delimiter, path, encoding)

            # Read sample for schema inference
            sample_rows = options.infer_schema_length

            def _read_sample() -> pl.DataFrame:
                return pl.read_csv(
                    path,
                    separator=delimiter,
                    encoding=encoding if encoding != "utf-8-sig" else "utf-8",
                    n_rows=sample_rows,
                    infer_schema_length=sample_rows,
                    ignore_errors=True,
                    null_values=options.null_values,
                )

            df = await asyncio.to_thread(_read_sample)

            # Build column info
            columns: list[ColumnInfo] = []
            for i, col_name in enumerate(df.columns):
                col = df[col_name]
                dtype = col.dtype

                # Get sample values (up to 10)
                sample_values = col.head(10).to_list()

                # Count nulls
                null_count = col.null_count()

                # Distinct count estimate
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

            # Estimate total rows
            row_count_estimate: int | None = None
            row_count_exact = False

            if file_size < 10 * 1024 * 1024:  # < 10MB
                # For small files, get exact count
                def _count_rows() -> int:
                    return pl.scan_csv(
                        path,
                        separator=delimiter,
                        encoding=encoding if encoding != "utf-8-sig" else "utf-8",
                    ).select(pl.len()).collect().item()

                try:
                    row_count_estimate = await asyncio.to_thread(_count_rows)
                    row_count_exact = True
                except Exception:
                    row_count_estimate = len(df)
            else:
                # Estimate based on sample
                if len(df) > 0:
                    avg_row_size = file_size / len(df)
                    row_count_estimate = int(file_size / avg_row_size) if avg_row_size > 0 else None

            # Detect if has header
            has_header = True  # Polars assumes header by default

            end_time = datetime.now(timezone.utc)
            duration_ms = (end_time - start_time).total_seconds() * 1000

            return SchemaProbeResult(
                file_path=file_path,
                file_size_bytes=file_size,
                adapter_id=self._metadata.adapter_id,
                columns=columns,
                row_count_estimate=row_count_estimate,
                row_count_exact=row_count_exact,
                encoding_detected=encoding,
                delimiter_detected=delimiter,
                has_header_row=has_header,
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
                message=f"Failed to probe schema: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def read_dataframe(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> tuple[pl.DataFrame, ReadResult]:
        """Read CSV file into a Polars DataFrame.

        For files > 10MB, consider using stream_dataframe instead.

        Args:
            file_path: Relative path to the CSV file.
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

            # Detect encoding and delimiter
            encoding = await asyncio.to_thread(_detect_encoding, path)
            delimiter_from_options = options.extra.get("delimiter")
            delimiter = delimiter_from_options or await asyncio.to_thread(
                _detect_delimiter, path, encoding
            )

            def _read_csv() -> pl.DataFrame:
                # Build read parameters
                read_kwargs: dict[str, Any] = {
                    "separator": delimiter,
                    "encoding": encoding if encoding != "utf-8-sig" else "utf-8",
                    "null_values": options.null_values,
                    "ignore_errors": True,
                }

                if options.row_limit:
                    read_kwargs["n_rows"] = options.row_limit + options.skip_rows

                if options.columns:
                    read_kwargs["columns"] = options.columns

                df = pl.read_csv(path, **read_kwargs)

                # Apply skip_rows
                if options.skip_rows > 0:
                    df = df.slice(options.skip_rows)

                # Apply row_limit after skip
                if options.row_limit and len(df) > options.row_limit:
                    df = df.head(options.row_limit)

                # Exclude columns if specified
                if options.exclude_columns:
                    cols_to_keep = [
                        c for c in df.columns if c not in options.exclude_columns
                    ]
                    df = df.select(cols_to_keep)

                return df

            df = await asyncio.to_thread(_read_csv)

            end_time = datetime.now(timezone.utc)
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
        except pl.exceptions.ComputeError as e:
            raise AdapterError(
                code=AdapterErrorCode.PARSE_ERROR,
                message=f"Failed to parse CSV: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e
        except UnicodeDecodeError as e:
            raise AdapterError(
                code=AdapterErrorCode.ENCODING_ERROR,
                message=f"Encoding error reading CSV: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.UNKNOWN,
                message=f"Failed to read CSV: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def stream_dataframe(
        self,
        file_path: str,
        options: StreamOptions | None = None,
    ) -> AsyncIterator[tuple[pl.DataFrame, StreamChunk]]:
        """Stream CSV file as chunks for large file processing.

        Per ADR-0041: This is the preferred method for files > 10MB.

        Args:
            file_path: Relative path to the CSV file.
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

            # Detect encoding and delimiter
            encoding = await asyncio.to_thread(_detect_encoding, path)
            delimiter = options.extra.get("delimiter") or await asyncio.to_thread(
                _detect_delimiter, path, encoding
            )

            # Use Polars lazy API for streaming
            # Note: scan_csv only accepts 'utf8' or 'utf8-lossy', not 'utf-8'
            def _create_lazy_frame() -> pl.LazyFrame:
                # Polars scan_csv only supports utf8/utf8-lossy
                enc_normalized = encoding.lower().replace("-", "")
                polars_encoding = "utf8" if enc_normalized == "utf8" else "utf8-lossy"
                lf = pl.scan_csv(
                    path,
                    separator=delimiter,
                    encoding=polars_encoding,
                )
                if options.columns:
                    lf = lf.select(options.columns)
                return lf

            lf = await asyncio.to_thread(_create_lazy_frame)

            # Get total row count for progress
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
                    # No more data
                    break

        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(
                code=AdapterErrorCode.PARSE_ERROR,
                message=f"Failed to stream CSV: {e}",
                file_path=file_path,
                adapter_id=self._metadata.adapter_id,
                details={"error": str(e)},
            ) from e

    async def validate_file(
        self,
        file_path: str,
        options: ReadOptions | None = None,
    ) -> FileValidationResult:
        """Validate CSV file can be processed by this adapter.

        Performs quick checks without reading entire file:
        - File exists and is readable
        - File format matches CSV expectations
        - Encoding is valid

        Args:
            file_path: Relative path to the CSV file.
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
                return self._build_validation_result(
                    file_path, start_time, issues
                )

            # Check file is readable
            if not path.is_file():
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="NOT_A_FILE",
                        message=f"Path is not a file: {file_path}",
                        suggestion="Provide a path to a regular file.",
                    )
                )
                return self._build_validation_result(
                    file_path, start_time, issues
                )

            # Check file is not empty
            file_size = path.stat().st_size
            if file_size == 0:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        code="EMPTY_FILE",
                        message="File is empty",
                        suggestion="Provide a non-empty CSV file.",
                    )
                )
                return self._build_validation_result(
                    file_path, start_time, issues
                )

            # Try to detect encoding
            encoding = await asyncio.to_thread(_detect_encoding, path)

            # Try to read first few lines
            def _validate_content() -> list[ValidationIssue]:
                content_issues: list[ValidationIssue] = []
                try:
                    with open(path, "r", encoding=encoding, errors="strict") as f:
                        lines = []
                        for i, line in enumerate(f):
                            if i >= 5:
                                break
                            lines.append(line)

                    if not lines:
                        content_issues.append(
                            ValidationIssue(
                                severity=ValidationSeverity.ERROR,
                                code="NO_DATA",
                                message="File contains no readable lines",
                            )
                        )
                except UnicodeDecodeError as e:
                    content_issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            code="ENCODING_ERROR",
                            message=f"Encoding error: {e}",
                            suggestion=f"Try specifying encoding explicitly. Detected: {encoding}",
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
