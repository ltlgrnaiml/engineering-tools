"""Parse stage - full data extraction.

Per ADR-0013: Cancellation preserves completed work, no partial data.
Per ADR-0014: Output saved as Parquet.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import polars as pl

from ..adapters.factory import AdapterFactory


@dataclass
class ParseConfig:
    """Configuration for parse stage."""
    selected_files: list[Path]
    selected_tables: dict[str, list[str]]  # file path -> table names
    column_mappings: dict[str, str] | None = None


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


async def execute_parse(
    run_id: str,
    config: ParseConfig,
    workspace_path: Path,
    progress_callback: Callable[[float, str], None] | None = None,
    cancel_token: CancellationToken | None = None,
) -> ParseResult:
    """Execute full parse with progress and cancellation support.
    
    Per ADR-0013: If cancelled, only fully completed tables are kept.
    
    Args:
        run_id: DAT run ID
        config: Parse configuration
        workspace_path: Path to workspace directory
        progress_callback: Optional callback for progress updates (percent, message)
        cancel_token: Optional token to check for cancellation
        
    Returns:
        ParseResult with combined data and metadata
    """
    all_dfs: list[pl.DataFrame] = []
    source_files: list[str] = []
    total_files = len(config.selected_files)
    
    for i, file_path in enumerate(config.selected_files):
        # Check cancellation before each file
        if cancel_token and cancel_token.is_cancelled:
            break
        
        if progress_callback:
            progress_callback(
                (i / total_files) * 100,
                f"Processing {file_path.name}..."
            )
        
        tables = config.selected_tables.get(str(file_path), [])
        if not tables:
            # If no tables specified, read all tables
            tables = AdapterFactory.get_tables(file_path)
        
        for table in tables:
            if cancel_token and cancel_token.is_cancelled:
                break
            
            # Read table
            df = AdapterFactory.read_file(file_path, sheet=table)
            
            # Apply column mappings if provided
            if config.column_mappings:
                rename_map = {k: v for k, v in config.column_mappings.items() if k in df.columns}
                if rename_map:
                    df = df.rename(rename_map)
            
            all_dfs.append(df)
            source_files.append(f"{file_path.name}:{table}")
    
    # Combine all DataFrames
    if all_dfs:
        combined = pl.concat(all_dfs, how="diagonal")
    else:
        combined = pl.DataFrame()
    
    # Compute parse ID
    from shared.utils.stage_id import compute_stage_id
    parse_id = compute_stage_id({
        "run_id": run_id,
        "files": sorted(source_files),
        "row_count": len(combined),
    }, prefix="parse_")
    
    # Save to workspace
    output_dir = workspace_path / "tools" / "dat" / "runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / f"{parse_id}.parquet"
    combined.write_parquet(output_path)
    
    if progress_callback:
        progress_callback(100, "Parse complete")
    
    return ParseResult(
        data=combined,
        row_count=len(combined),
        column_count=len(combined.columns),
        source_files=source_files,
        completed=not (cancel_token and cancel_token.is_cancelled),
        parse_id=parse_id,
        output_path=str(output_path),
    )
