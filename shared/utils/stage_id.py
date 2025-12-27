"""Deterministic stage/artifact ID generation.

Per ADR-0004: IDs are computed as SHA-256 hash of stable JSON serialization.
- Same inputs always yield same ID (deterministic)
- IDs are first 16 characters of hex digest
- Seed is fixed at 42 for reproducibility
"""

import hashlib
import json
from typing import Any

__version__ = "0.1.0"

DEFAULT_SEED = 42


def compute_stage_id(
    inputs: dict[str, Any],
    seed: int = DEFAULT_SEED,
    prefix: str = "",
) -> str:
    """Compute a deterministic stage ID from inputs.
    
    Args:
        inputs: Dictionary of inputs to hash
        seed: Random seed for determinism (default: 42)
        prefix: Optional prefix for the ID (e.g., "ds_", "pipe_")
        
    Returns:
        Deterministic ID string (prefix + 16 hex chars)
        
    Example:
        >>> compute_stage_id({"files": ["a.csv"], "level": "wafer"}, prefix="ds_")
        'ds_a1b2c3d4e5f67890'
    """
    # Add seed to inputs for reproducibility
    hashable = {**inputs, "_seed": seed}
    
    # Stable JSON serialization (sorted keys, no whitespace)
    serialized = json.dumps(hashable, sort_keys=True, separators=(",", ":"))
    
    # SHA-256 hash, truncated to 16 chars
    hash_digest = hashlib.sha256(serialized.encode()).hexdigest()[:16]
    
    return f"{prefix}{hash_digest}"


def compute_dataset_id(
    *,
    run_id: str | None = None,
    columns: list[str] | None = None,
    row_count: int | None = None,
    aggregation_levels: list[str] | None = None,
    parent_ids: list[str] | None = None,
    analysis_type: str | None = None,
    factors: list[str] | None = None,
    response_columns: list[str] | None = None,
    seed: int = DEFAULT_SEED,
) -> str:
    """Compute a deterministic DataSet ID.
    
    Includes only non-None values in the hash computation.
    """
    inputs: dict[str, Any] = {}
    
    if run_id is not None:
        inputs["run_id"] = run_id
    if columns is not None:
        inputs["columns"] = sorted(columns)
    if row_count is not None:
        inputs["row_count"] = row_count
    if aggregation_levels is not None:
        inputs["aggregation_levels"] = aggregation_levels
    if parent_ids is not None:
        inputs["parent_ids"] = sorted(parent_ids)
    if analysis_type is not None:
        inputs["analysis_type"] = analysis_type
    if factors is not None:
        inputs["factors"] = sorted(factors)
    if response_columns is not None:
        inputs["response_columns"] = sorted(response_columns)
    
    return compute_stage_id(inputs, seed=seed, prefix="ds_")


def compute_pipeline_id(
    name: str,
    steps: list[dict[str, Any]],
    seed: int = DEFAULT_SEED,
) -> str:
    """Compute a deterministic Pipeline ID."""
    inputs = {
        "name": name,
        "steps": steps,
    }
    return compute_stage_id(inputs, seed=seed, prefix="pipe_")
