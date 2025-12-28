"""Parse stage - full data extraction.

Per ADR-0003: Parse uses profile defaults if context.json missing.
Per ADR-0013: Cancellation preserves completed work, no partial data.
Per ADR-0014: Output saved as Parquet.
"""
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import polars as pl

from shared.contracts.dat.cancellation import (
    CancellationResult,
    CheckpointType,
)
from ..adapters.factory import AdapterFactory
from ..core.checkpoint_manager import CheckpointManager
from ..profiles.profile_loader import DATProfile, get_profile_by_id

logger = logging.getLogger(__name__)


@dataclass
class ParseConfig:
    """Configuration for parse stage."""
    selected_files: list[Path]
    selected_tables: dict[str, list[str]]  # file path -> table names
    column_mappings: dict[str, str] | None = None
    profile_id: str | None = None  # Profile for default fallback
    context_overrides: dict[str, Any] = field(default_factory=dict)


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


class CancellationToken:
    """Token for checking cancellation status."""
    
    def __init__(self):
        self._cancelled = False
    
    def cancel(self):
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
            logger.debug(f"No context.json and no profile defaults available")

    # 3. Apply explicit overrides (highest priority)
    if context_overrides:
        context.update(context_overrides)
        logger.debug(f"Applied {len(context_overrides)} context overrides")

    return context


async def execute_parse(
    run_id: str,
    config: ParseConfig,
    workspace_path: Path,
    progress_callback: Callable[[float, str], None] | None = None,
    cancel_token: CancellationToken | None = None,
) -> ParseResult | CancellationResult:
    """Execute full parse with progress and cancellation support.

    Per ADR-0003: Uses profile defaults if context.json is missing.
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
            tables = AdapterFactory.get_tables(file_path)
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

            # Read table - use 'table' parameter for cross-adapter compatibility
            df = AdapterFactory.read_file(file_path, table=table)

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
    if all_dfs:
        combined = pl.concat(all_dfs, how="diagonal")
    else:
        combined = pl.DataFrame()

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
