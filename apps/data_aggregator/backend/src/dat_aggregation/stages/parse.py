"""Parse stage - full data extraction.

Per ADR-0003: Parse uses profile defaults if context.json missing.
Per ADR-0011: Profile-driven extraction via ProfileExecutor.
Per ADR-0013: Cancellation preserves completed work, no partial data.
Per ADR-0014: Output saved as Parquet.
Per ADR-0040: Files >10MB use streaming.
"""
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import polars as pl

from apps.data_aggregator.backend.adapters import create_default_registry
from shared.contracts.dat.adapter import ReadOptions
from shared.contracts.dat.cancellation import (
    CancellationResult,
    CheckpointType,
)

from ..core.checkpoint_manager import CheckpointManager
from ..profiles.profile_loader import DATProfile, get_profile_by_id
from ..profiles.profile_executor import ProfileExecutor
from ..profiles.context_extractor import ContextExtractor
from ..profiles.validation_engine import ValidationEngine
from ..profiles.transform_pipeline import TransformPipeline
from ..profiles.output_builder import OutputBuilder
from ..profiles.population_strategies import apply_population_strategy

# Per ADR-0040: Large file streaming threshold
STREAMING_THRESHOLD_BYTES = 10 * 1024 * 1024  # 10MB

# Per ADR-0014: Parse always outputs Parquet
OUTPUT_FORMAT = "parquet"

logger = logging.getLogger(__name__)


@dataclass
class ParseConfig:
    """Configuration for parse stage."""
    selected_files: list[Path]
    selected_tables: dict[str, list[str]]  # file path -> table names
    column_mappings: dict[str, str] | None = None
    profile_id: str | None = None  # Profile for profile-driven extraction
    context_overrides: dict[str, Any] = field(default_factory=dict)
    use_profile_extraction: bool = True  # Per ADR-0011: Use ProfileExecutor when profile specified


@dataclass
class ParseResult:
    """Result of parse stage."""
    data: pl.DataFrame
    row_count: int
    column_count: int
    source_files: list[str]
    completed: bool
    parse_id: str
    output_path: str
    extracted_tables: dict[str, pl.DataFrame] | None = None  # ADR-0011: tables
    validation_summary: Any | None = None  # Validation results


class CancellationToken:
    """Token for checking cancellation status."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled


def _load_context_with_fallback(
    run_id: str,
    workspace_path: Path,
    profile: DATProfile | None,
    context_overrides: dict[str, Any],
) -> dict[str, Any]:
    """Load context from context.json, falling back to profile defaults per ADR-0003.

    Args:
        run_id: DAT run ID.
        workspace_path: Path to workspace directory.
        profile: Optional profile for default values.
        context_overrides: Explicit context overrides (highest priority).

    Returns:
        Merged context dictionary.
    """
    context: dict[str, Any] = {}

    # 1. Start with profile defaults (lowest priority)
    if profile and profile.context_defaults:
        context.update(profile.context_defaults.defaults)
        logger.debug(f"Loaded {len(profile.context_defaults.defaults)} profile defaults")

    # 2. Load context.json if it exists
    context_path = workspace_path / "tools" / "dat" / "runs" / run_id / "context.json"
    if context_path.exists():
        try:
            with open(context_path, encoding="utf-8") as f:
                file_context = json.load(f)
            context.update(file_context)
            logger.debug(f"Loaded context from {context_path}")
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Failed to load context.json: {e}, using profile defaults")
    else:
        if profile and profile.context_defaults:
            logger.info(
                f"context.json not found at {context_path}, "
                f"using profile defaults per ADR-0003"
            )
        else:
            logger.debug("No context.json and no profile defaults available")

    # 3. Apply explicit overrides (highest priority)
    if context_overrides:
        context.update(context_overrides)
        logger.debug(f"Applied {len(context_overrides)} context overrides")

    return context


async def _execute_profile_extraction(
    run_id: str,
    config: ParseConfig,
    profile: DATProfile,
    context: dict[str, Any],
    workspace_path: Path,
    checkpoint_mgr: CheckpointManager,
    progress_callback: Callable[[float, str], None] | None = None,
    cancel_token: CancellationToken | None = None,
) -> ParseResult | CancellationResult:
    """Execute profile-driven extraction per ADR-0011.

    Uses ProfileExecutor to extract tables defined in profile YAML.
    Applies validation, transforms, and builds outputs.

    Args:
        run_id: DAT run ID.
        config: Parse configuration.
        profile: Loaded DATProfile.
        context: Context dictionary.
        workspace_path: Path to workspace directory.
        checkpoint_mgr: Checkpoint manager for cancel-safe operations.
        progress_callback: Optional callback for progress updates.
        cancel_token: Optional token to check for cancellation.

    Returns:
        ParseResult with extracted tables, or CancellationResult if cancelled.
    """
    if progress_callback:
        progress_callback(0, "Starting profile-driven extraction...")

    # Check cancellation before starting
    if cancel_token and cancel_token.is_cancelled:
        return checkpoint_mgr.complete_cancellation(
            preserved_artifacts=[],
            discarded_count=len(profile.get_all_tables()),
        )

    # Per DESIGN §4: Extract context using 4-level priority
    # Priority 1: User overrides, Priority 2: JSONPath, Priority 3: Regex, Priority 4: Defaults
    context_extractor = ContextExtractor()
    executor = ProfileExecutor()
    
    for file_path in config.selected_files:
        # Load file content for JSONPath extraction (Priority 2)
        file_content = await executor._load_file(file_path, profile)
        
        file_context = context_extractor.extract(
            profile=profile,
            file_path=file_path,
            file_content=file_content,  # Now passing content for Priority 2
            user_overrides=config.context_overrides,
        )
        context.update(file_context)

    if progress_callback:
        progress_callback(10, "Context extracted, executing profile...")
    
    # Get selected tables from config or use all
    selected_tables = None
    if config.selected_tables:
        # Flatten all selected tables
        selected_tables = []
        for tables in config.selected_tables.values():
            selected_tables.extend(tables)

    extracted_tables = await executor.execute(
        profile=profile,
        files=config.selected_files,
        context=context,
        selected_tables=selected_tables,
    )

    if progress_callback:
        progress_callback(55, f"Extracted {len(extracted_tables)} tables, applying population...")

    # Per DESIGN §3: Apply population strategy if defined
    for table_id, df in extracted_tables.items():
        extracted_tables[table_id] = apply_population_strategy(
            df, profile.default_strategy, {}
        )

    if progress_callback:
        progress_callback(60, "Population strategy applied, validating...")

    # Validate extraction
    validation_engine = ValidationEngine()
    validation_summary = validation_engine.validate_extraction(extracted_tables, profile)
    
    # Per DESIGN §7: Handle validation failures based on on_validation_fail policy
    quarantine_tables: dict[str, pl.DataFrame] = {}
    if not validation_summary.valid:
        on_fail = getattr(profile, 'on_validation_fail', 'continue')
        
        if on_fail == "stop":
            err_count = validation_summary.error_count
            logger.error(f"Validation failed with {err_count} errors - stopping")
            raise ValueError(
                f"Validation failed: {validation_summary.error_count} errors, "
                f"{validation_summary.warning_count} warnings"
            )
        elif on_fail == "quarantine":
            # Move invalid rows to quarantine table
            quarantine_table_name = getattr(profile, 'quarantine_table', 'validation_failures')
            for result in validation_summary.table_results:
                if not result.valid and result.table_id in extracted_tables:
                    # Mark table as quarantined
                    quarantine_tables[result.table_id] = extracted_tables[result.table_id]
                    logger.warning(f"Table {result.table_id} quarantined due to validation errors")
            logger.info(f"Quarantined {len(quarantine_tables)} tables to {quarantine_table_name}")
        # else: continue - proceed with warnings logged

    if progress_callback:
        progress_callback(70, "Validation complete, applying transforms...")

    # Apply transforms per DESIGN §6
    transform_pipeline = TransformPipeline()
    for table_id, df in extracted_tables.items():
        # 1. Apply normalization (NaN replacement, numeric coercion, row filters, units)
        df = transform_pipeline.apply_normalization(df, profile)
        
        # 2. Per DESIGN §6: Apply global column renames if defined
        if hasattr(profile, 'column_renames') and profile.column_renames:
            df = transform_pipeline.apply_column_renames(df, profile.column_renames)
        
        # 3. Per DESIGN §6: Apply calculated columns if defined
        if hasattr(profile, 'calculated_columns') and profile.calculated_columns:
            df = transform_pipeline.apply_calculated_columns(df, profile.calculated_columns)
        
        # 4. Per DESIGN §6: Apply type coercion if defined
        if hasattr(profile, 'type_coercion') and profile.type_coercion:
            df = transform_pipeline.apply_type_coercion(df, profile.type_coercion)
        
        extracted_tables[table_id] = df

    if progress_callback:
        progress_callback(80, "Transforms applied, building outputs...")

    # Per DESIGN §8: Build outputs using profile-defined aggregations and joins
    output_builder = OutputBuilder()
    profile_outputs = output_builder.build_outputs(
        extracted_tables,
        profile,
        context=context,
    )
    
    # Combine all tables (including profile outputs) for final result
    all_tables = {**extracted_tables, **profile_outputs}
    combined = output_builder.combine_all_tables(all_tables, context)

    # Compute parse ID
    from shared.utils.stage_id import compute_stage_id

    source_files = [str(f) for f in config.selected_files]
    parse_id = compute_stage_id(
        {
            "run_id": run_id,
            "profile_id": profile.profile_id,
            "files": sorted(source_files),
            "tables": sorted(extracted_tables.keys()),
            "row_count": len(combined),
        },
        prefix="parse_",
    )

    # Save to workspace
    output_dir = workspace_path / "tools" / "dat" / "runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{parse_id}.parquet"
    if not combined.is_empty():
        combined.write_parquet(output_path)
    else:
        # Write empty parquet with schema
        combined.write_parquet(output_path)

    # Save individual tables as well
    tables_dir = output_dir / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    for table_id, df in extracted_tables.items():
        table_path = tables_dir / f"{table_id}.parquet"
        df.write_parquet(table_path)

    # Mark operation complete
    checkpoint_mgr.complete_operation()

    if progress_callback:
        progress_callback(100, "Profile extraction complete")

    logger.info(
        f"Profile extraction complete: {len(extracted_tables)} tables, "
        f"{len(combined)} rows, validation={'PASS' if validation_summary.valid else 'WARN'}"
    )

    return ParseResult(
        data=combined,
        row_count=len(combined),
        column_count=len(combined.columns),
        source_files=source_files,
        completed=True,
        parse_id=parse_id,
        output_path=str(output_path),
        extracted_tables=extracted_tables,
        validation_summary=validation_summary,
    )


async def execute_parse(
    run_id: str,
    config: ParseConfig,
    workspace_path: Path,
    progress_callback: Callable[[float, str], None] | None = None,
    cancel_token: CancellationToken | None = None,
) -> ParseResult | CancellationResult:
    """Execute full parse with progress and cancellation support.

    Per ADR-0003: Uses profile defaults if context.json is missing.
    Per ADR-0011: Uses ProfileExecutor for profile-driven extraction.
    Per ADR-0013: If cancelled, only fully completed tables are kept.
                  Uses CheckpointManager for cancel-safe operations.

    Args:
        run_id: DAT run ID.
        config: Parse configuration.
        workspace_path: Path to workspace directory.
        progress_callback: Optional callback for progress updates (percent, message).
        cancel_token: Optional token to check for cancellation.

    Returns:
        ParseResult with combined data and metadata, or CancellationResult if cancelled.
    """
    # Initialize checkpoint manager for cancel-safe operations per ADR-0013
    checkpoint_mgr = CheckpointManager(
        workspace_path=workspace_path,
        run_id=run_id,
        stage_id="parse",
    )
    checkpoint_mgr.start_operation("parse")

    # Load profile if specified
    profile: DATProfile | None = None
    if config.profile_id:
        profile = get_profile_by_id(config.profile_id)
        if profile:
            logger.info(f"Using profile: {profile.title} ({config.profile_id})")
        else:
            logger.warning(f"Profile not found: {config.profile_id}")

    # Load context with profile default fallback per ADR-0003
    context = _load_context_with_fallback(
        run_id=run_id,
        workspace_path=workspace_path,
        profile=profile,
        context_overrides=config.context_overrides,
    )

    # Per ADR-0011: Use ProfileExecutor for profile-driven extraction
    if profile and config.use_profile_extraction:
        return await _execute_profile_extraction(
            run_id=run_id,
            config=config,
            profile=profile,
            context=context,
            workspace_path=workspace_path,
            checkpoint_mgr=checkpoint_mgr,
            progress_callback=progress_callback,
            cancel_token=cancel_token,
        )

    # Legacy path: direct adapter reads (when no profile or profile extraction disabled)
    registry = create_default_registry()

    all_dfs: list[pl.DataFrame] = []
    source_files: list[str] = []
    completed_tables: list[str] = []
    total_files = len(config.selected_files)
    tables_processed = 0

    # Pre-calculate actual tables to process for accurate progress tracking
    file_tables_map: dict[Path, list[str]] = {}
    for file_path in config.selected_files:
        tables = config.selected_tables.get(str(file_path), [])
        if not tables:
            # Get tables from adapter using async probe_schema
            adapter = registry.get_adapter_for_file(str(file_path))
            if adapter.metadata.capabilities.supports_multiple_sheets:
                result = await adapter.probe_schema(str(file_path))
                tables = [s.sheet_name for s in result.sheets] if result.sheets else [file_path.name]
            else:
                tables = [file_path.name]
        file_tables_map[file_path] = tables

    total_tables = sum(len(tables) for tables in file_tables_map.values())

    for i, file_path in enumerate(config.selected_files):
        # Check cancellation before each file (safe point per ADR-0013)
        if cancel_token and cancel_token.is_cancelled:
            logger.info(f"Cancellation detected at file boundary: {file_path.name}")
            return checkpoint_mgr.complete_cancellation(
                preserved_artifacts=completed_tables,
                discarded_count=total_tables - tables_processed,
            )

        if progress_callback:
            progress_pct = (i / total_files) * 100
            progress_callback(progress_pct, f"Processing {file_path.name}...")

        tables = file_tables_map[file_path]

        for table in tables:
            # Check cancellation before each table (safe point per ADR-0013)
            if cancel_token and cancel_token.is_cancelled:
                logger.info(f"Cancellation detected at table boundary: {table}")
                return checkpoint_mgr.complete_cancellation(
                    preserved_artifacts=completed_tables,
                    discarded_count=total_tables - tables_processed,
                )

            # Read table using async adapter - stream if large per ADR-0040
            adapter = registry.get_adapter_for_file(str(file_path))
            options = ReadOptions(extra={"sheet_name": table} if table != file_path.name else {})

            file_size = file_path.stat().st_size
            if file_size > STREAMING_THRESHOLD_BYTES:
                # Stream large files in chunks per ADR-0040
                logger.info(f"Streaming large file ({file_size / 1024 / 1024:.1f}MB): {file_path.name}")
                chunks: list[pl.DataFrame] = []
                async for chunk in adapter.stream_dataframe(str(file_path), options, chunk_size=50000):
                    if cancel_token and cancel_token.is_cancelled:
                        break
                    chunks.append(chunk)
                df = pl.concat(chunks) if chunks else pl.DataFrame()
            else:
                # Eager load small files
                df, _ = await adapter.read_dataframe(str(file_path), options)

            # Apply column mappings if provided
            if config.column_mappings:
                rename_map = {
                    k: v for k, v in config.column_mappings.items() if k in df.columns
                }
                if rename_map:
                    df = df.rename(rename_map)

            all_dfs.append(df)
            table_ref = f"{file_path.name}:{table}"
            source_files.append(table_ref)
            completed_tables.append(table_ref)
            tables_processed += 1

            # Save checkpoint after each table completion per ADR-0013
            checkpoint_mgr.save_checkpoint(
                checkpoint_type=CheckpointType.TABLE_COMPLETE,
                items_completed=tables_processed,
                items_total=total_tables,
                current_item=table_ref,
                data_for_hash={"rows": len(df), "cols": len(df.columns)},
                metadata={"file": file_path.name, "table": table},
            )

    # Combine all DataFrames
    combined = pl.concat(all_dfs, how="diagonal") if all_dfs else pl.DataFrame()

    # Compute parse ID
    from shared.utils.stage_id import compute_stage_id

    parse_id = compute_stage_id(
        {
            "run_id": run_id,
            "files": sorted(source_files),
            "row_count": len(combined),
        },
        prefix="parse_",
    )

    # Save to workspace
    output_dir = workspace_path / "tools" / "dat" / "runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{parse_id}.parquet"
    combined.write_parquet(output_path)

    # Mark operation complete
    checkpoint_mgr.complete_operation()

    if progress_callback:
        progress_callback(100, "Parse complete")

    return ParseResult(
        data=combined,
        row_count=len(combined),
        column_count=len(combined.columns),
        source_files=source_files,
        completed=True,
        parse_id=parse_id,
        output_path=str(output_path),
    )
