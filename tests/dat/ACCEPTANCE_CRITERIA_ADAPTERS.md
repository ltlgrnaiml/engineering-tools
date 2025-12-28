# DAT Adapter Implementation Acceptance Criteria

**Document Type:** Test Acceptance Criteria  
**Scope:** DAT File Adapters (CSV, Excel, JSON)  
**Created:** 2025-12-28  
**Implements:** ADR-0011, ADR-0040, SPEC-DAT-0003, SPEC-DAT-0004

---

## Overview

This document defines the acceptance criteria for validating the DAT file adapter implementation. All criteria must pass for 100% compliance.

---

## AC-1: Adapter Interface Compliance

### AC-1.1: BaseFileAdapter Implementation
- [ ] **AC-1.1.1**: All adapters inherit from `BaseFileAdapter` abstract class
- [ ] **AC-1.1.2**: All adapters implement `metadata` property returning `AdapterMetadata`
- [ ] **AC-1.1.3**: All adapters implement `probe_schema()` async method
- [ ] **AC-1.1.4**: All adapters implement `read_dataframe()` async method
- [ ] **AC-1.1.5**: All adapters implement `stream_dataframe()` async generator
- [ ] **AC-1.1.6**: All adapters implement `validate_file()` async method
- [ ] **AC-1.1.7**: All adapters implement `can_handle()` method (inherited, uses metadata)

### AC-1.2: AdapterMetadata Requirements
- [ ] **AC-1.2.1**: `adapter_id` follows pattern `^[a-z][a-z0-9_]*$`
- [ ] **AC-1.2.2**: `file_extensions` list is non-empty and starts with dot
- [ ] **AC-1.2.3**: `version` follows semver pattern `^\d+\.\d+\.\d+$`
- [ ] **AC-1.2.4**: `capabilities` accurately reflects adapter features

---

## AC-2: AdapterRegistry Requirements

### AC-2.1: Registration
- [ ] **AC-2.1.1**: `register()` adds adapter to registry
- [ ] **AC-2.1.2**: `register()` maps file extensions to adapter_id
- [ ] **AC-2.1.3**: `register()` maps MIME types to adapter_id (if provided)
- [ ] **AC-2.1.4**: Duplicate adapter_id raises `ValueError`

### AC-2.2: Lookup
- [ ] **AC-2.2.1**: `get_adapter(adapter_id)` returns correct adapter
- [ ] **AC-2.2.2**: `get_adapter()` raises `AdapterNotFoundError` for unknown ID
- [ ] **AC-2.2.3**: `get_adapter_for_file(path)` selects by extension
- [ ] **AC-2.2.4**: `get_adapter_for_file(path, mime_type)` prefers MIME type
- [ ] **AC-2.2.5**: `get_adapter_for_file()` raises `AdapterNotFoundError` for unknown format
- [ ] **AC-2.2.6**: `list_adapters()` returns all registered `AdapterMetadata`

### AC-2.3: Default Registry
- [ ] **AC-2.3.1**: `create_default_registry()` registers CSV adapter
- [ ] **AC-2.3.2**: `create_default_registry()` registers Excel adapter
- [ ] **AC-2.3.3**: `create_default_registry()` registers JSON adapter

---

## AC-3: CSV Adapter Requirements

### AC-3.1: Metadata
- [ ] **AC-3.1.1**: `adapter_id` is `"csv"`
- [ ] **AC-3.1.2**: `file_extensions` includes `.csv` and `.tsv`
- [ ] **AC-3.1.3**: `capabilities.supports_streaming` is `True`
- [ ] **AC-3.1.4**: `capabilities.supports_schema_inference` is `True`

### AC-3.2: Schema Probing
- [ ] **AC-3.2.1**: `probe_schema()` returns `SchemaProbeResult` with columns
- [ ] **AC-3.2.2**: `probe_schema()` infers column types from sample data
- [ ] **AC-3.2.3**: `probe_schema()` detects delimiter (comma, tab, semicolon)
- [ ] **AC-3.2.4**: `probe_schema()` detects encoding (UTF-8, Latin-1)
- [ ] **AC-3.2.5**: `probe_schema()` detects header row presence
- [ ] **AC-3.2.6**: `probe_schema()` completes in < 5 seconds for any file size
- [ ] **AC-3.2.7**: `probe_schema()` only reads first 1000 rows for inference

### AC-3.3: Reading
- [ ] **AC-3.3.1**: `read_dataframe()` returns `(DataFrame, ReadResult)` tuple
- [ ] **AC-3.3.2**: `read_dataframe()` respects `columns` option (column selection)
- [ ] **AC-3.3.3**: `read_dataframe()` respects `row_limit` option
- [ ] **AC-3.3.4**: `read_dataframe()` respects `skip_rows` option
- [ ] **AC-3.3.5**: `read_dataframe()` handles different encodings
- [ ] **AC-3.3.6**: `read_dataframe()` handles different delimiters
- [ ] **AC-3.3.7**: `read_dataframe()` handles null values per `null_values` option

### AC-3.4: Streaming
- [ ] **AC-3.4.1**: `stream_dataframe()` yields `(DataFrame, StreamChunk)` tuples
- [ ] **AC-3.4.2**: `stream_dataframe()` respects `chunk_size_rows` option
- [ ] **AC-3.4.3**: `stream_dataframe()` sets `is_last_chunk` correctly
- [ ] **AC-3.4.4**: `stream_dataframe()` tracks `total_rows_so_far` correctly
- [ ] **AC-3.4.5**: `stream_dataframe()` works for files > 10MB

### AC-3.5: Validation
- [ ] **AC-3.5.1**: `validate_file()` returns `FileValidationResult`
- [ ] **AC-3.5.2**: `validate_file()` detects non-existent files
- [ ] **AC-3.5.3**: `validate_file()` detects invalid CSV format
- [ ] **AC-3.5.4**: `validate_file()` detects encoding errors

---

## AC-4: Excel Adapter Requirements

### AC-4.1: Metadata
- [ ] **AC-4.1.1**: `adapter_id` is `"excel"`
- [ ] **AC-4.1.2**: `file_extensions` includes `.xlsx` and `.xls`
- [ ] **AC-4.1.3**: `capabilities.supports_streaming` is `False`
- [ ] **AC-4.1.4**: `capabilities.supports_multiple_sheets` is `True`

### AC-4.2: Schema Probing
- [ ] **AC-4.2.1**: `probe_schema()` returns `SchemaProbeResult` with columns
- [ ] **AC-4.2.2**: `probe_schema()` includes `sheets` list with `SheetInfo`
- [ ] **AC-4.2.3**: `probe_schema()` probes default/first sheet if not specified
- [ ] **AC-4.2.4**: `probe_schema()` respects `extra.sheet_name` option
- [ ] **AC-4.2.5**: `probe_schema()` completes in < 5 seconds

### AC-4.3: Reading
- [ ] **AC-4.3.1**: `read_dataframe()` returns `(DataFrame, ReadResult)` tuple
- [ ] **AC-4.3.2**: `read_dataframe()` reads first sheet by default
- [ ] **AC-4.3.3**: `read_dataframe()` respects `extra.sheet_name` option
- [ ] **AC-4.3.4**: `read_dataframe()` respects `extra.sheet_index` option
- [ ] **AC-4.3.5**: `read_dataframe()` respects `columns` option
- [ ] **AC-4.3.6**: `read_dataframe()` respects `row_limit` option

### AC-4.4: Streaming
- [ ] **AC-4.4.1**: `stream_dataframe()` raises `AdapterError` with `STREAMING_NOT_SUPPORTED`
- [ ] **AC-4.4.2**: Error message indicates Excel doesn't support streaming

### AC-4.5: Validation
- [ ] **AC-4.5.1**: `validate_file()` returns `FileValidationResult`
- [ ] **AC-4.5.2**: `validate_file()` detects non-existent files
- [ ] **AC-4.5.3**: `validate_file()` detects corrupt/invalid Excel files
- [ ] **AC-4.5.4**: `validate_file()` detects password-protected files (if applicable)

---

## AC-5: JSON Adapter Requirements

### AC-5.1: Metadata
- [ ] **AC-5.1.1**: `adapter_id` is `"json"`
- [ ] **AC-5.1.2**: `file_extensions` includes `.json`, `.jsonl`, `.ndjson`
- [ ] **AC-5.1.3**: `capabilities.supports_streaming` is `True`
- [ ] **AC-5.1.4**: `capabilities.supports_schema_inference` is `True`

### AC-5.2: Schema Probing
- [ ] **AC-5.2.1**: `probe_schema()` returns `SchemaProbeResult` with columns
- [ ] **AC-5.2.2**: `probe_schema()` handles JSON array of objects
- [ ] **AC-5.2.3**: `probe_schema()` handles JSON Lines format
- [ ] **AC-5.2.4**: `probe_schema()` handles nested JSON (flattens to columns)
- [ ] **AC-5.2.5**: `probe_schema()` completes in < 5 seconds

### AC-5.3: Reading
- [ ] **AC-5.3.1**: `read_dataframe()` returns `(DataFrame, ReadResult)` tuple
- [ ] **AC-5.3.2**: `read_dataframe()` handles JSON array of objects
- [ ] **AC-5.3.3**: `read_dataframe()` handles JSON Lines (.jsonl, .ndjson)
- [ ] **AC-5.3.4**: `read_dataframe()` respects `columns` option
- [ ] **AC-5.3.5**: `read_dataframe()` respects `row_limit` option

### AC-5.4: Streaming
- [ ] **AC-5.4.1**: `stream_dataframe()` yields `(DataFrame, StreamChunk)` tuples
- [ ] **AC-5.4.2**: `stream_dataframe()` works for JSON Lines files
- [ ] **AC-5.4.3**: `stream_dataframe()` respects `chunk_size_rows` option
- [ ] **AC-5.4.4**: Regular JSON files fall back to single-chunk read

### AC-5.5: Validation
- [ ] **AC-5.5.1**: `validate_file()` returns `FileValidationResult`
- [ ] **AC-5.5.2**: `validate_file()` detects non-existent files
- [ ] **AC-5.5.3**: `validate_file()` detects invalid JSON syntax
- [ ] **AC-5.5.4**: `validate_file()` detects non-tabular JSON

---

## AC-6: Cross-Cutting Requirements

### AC-6.1: Path Safety (ADR-0017)
- [ ] **AC-6.1.1**: All file paths are validated as relative paths
- [ ] **AC-6.1.2**: Absolute paths raise `AdapterError` with `FILE_NOT_FOUND`
- [ ] **AC-6.1.3**: Path traversal (`..`) is rejected

### AC-6.2: Error Handling (ADR-0026)
- [ ] **AC-6.2.1**: All errors return `AdapterError` with appropriate `AdapterErrorCode`
- [ ] **AC-6.2.2**: `FILE_NOT_FOUND` for missing files
- [ ] **AC-6.2.3**: `INVALID_FORMAT` for format errors
- [ ] **AC-6.2.4**: `ENCODING_ERROR` for encoding issues
- [ ] **AC-6.2.5**: `STREAMING_NOT_SUPPORTED` when streaming unavailable

### AC-6.3: Type Safety (ADR-0009)
- [ ] **AC-6.3.1**: All public functions have type hints
- [ ] **AC-6.3.2**: All public functions have Google-style docstrings
- [ ] **AC-6.3.3**: All classes have `__version__` attribute
- [ ] **AC-6.3.4**: Ruff linting passes with no errors

### AC-6.4: Async/Concurrency (ADR-0012)
- [ ] **AC-6.4.1**: All I/O operations are async
- [ ] **AC-6.4.2**: File reads use `asyncio.to_thread()` for blocking operations
- [ ] **AC-6.4.3**: No raw `multiprocessing` usage

---

## AC-7: Test Coverage Requirements

### AC-7.1: Unit Tests
- [ ] **AC-7.1.1**: Each adapter has dedicated test file
- [ ] **AC-7.1.2**: Test coverage > 90% for each adapter
- [ ] **AC-7.1.3**: All AC items above have corresponding test

### AC-7.2: Test Fixtures
- [ ] **AC-7.2.1**: Small CSV fixture (< 1KB, 10 rows)
- [ ] **AC-7.2.2**: Medium CSV fixture (1-10MB range simulation)
- [ ] **AC-7.2.3**: Excel fixture with multiple sheets
- [ ] **AC-7.2.4**: JSON array fixture
- [ ] **AC-7.2.5**: JSON Lines fixture
- [ ] **AC-7.2.6**: Invalid/corrupt file fixtures for error testing

### AC-7.3: Integration Tests
- [ ] **AC-7.3.1**: Registry integration test with all adapters
- [ ] **AC-7.3.2**: Round-trip test: probe → read → validate

---

## Validation Commands

```bash
# Run all adapter tests
pytest tests/dat/test_adapters.py -v

# Run with coverage
pytest tests/dat/test_adapters.py --cov=apps/data_aggregator/backend/adapters --cov-report=term-missing

# Run specific adapter tests
pytest tests/dat/test_adapters.py -k "csv" -v
pytest tests/dat/test_adapters.py -k "excel" -v
pytest tests/dat/test_adapters.py -k "json" -v

# Lint check
ruff check apps/data_aggregator/backend/adapters/

# Type check
mypy apps/data_aggregator/backend/adapters/
```

---

## Compliance Score Calculation

| Category | Weight | Max Points |
|----------|--------|------------|
| AC-1: Interface Compliance | 15% | 11 |
| AC-2: Registry | 15% | 9 |
| AC-3: CSV Adapter | 20% | 19 |
| AC-4: Excel Adapter | 15% | 13 |
| AC-5: JSON Adapter | 15% | 17 |
| AC-6: Cross-Cutting | 10% | 12 |
| AC-7: Test Coverage | 10% | 10 |
| **Total** | **100%** | **91** |

**Compliance Score = (Passed Criteria / Total Criteria) × 100**

Target: **100% Compliance** (91/91 criteria passing)
