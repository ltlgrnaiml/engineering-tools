"""Analysis manager for SOV tool.

Per ADR-0024: Input via DataSetRef; output with lineage tracking.
"""
import json
import uuid
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import polars as pl

from shared.contracts.core.dataset import ColumnMeta, DataSetManifest, DataSetRef
from shared.storage.artifact_store import ArtifactStore
from shared.utils.stage_id import compute_dataset_id

from ..analysis.anova import (
    ANOVAConfig,
    ANOVAResult,
    run_anova_analysis,
)
from .visualization_service import VisualizationService


class AnalysisManager:
    """Manages SOV analysis runs."""

    def __init__(self, workspace_path: Path | None = None):
        if workspace_path is None:
            workspace_path = Path.cwd() / "workspace"
        self.workspace = workspace_path
        self.sov_workspace = self.workspace / "tools" / "sov"
        self.sov_workspace.mkdir(parents=True, exist_ok=True)
        self.store = ArtifactStore(workspace_path)
        self.viz_service = VisualizationService()

    def _analysis_dir(self, analysis_id: str) -> Path:
        """Get directory for an analysis."""
        path = self.sov_workspace / "analyses" / analysis_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    async def create_analysis(
        self,
        name: str | None = None,
        dataset_id: str | None = None,
        dataset_ref: DataSetRef | None = None,
    ) -> dict:
        """Create a new SOV analysis.

        Per ADR-0024: Input via DataSetRef for lineage tracking.

        Args:
            name: Optional human-readable name.
            dataset_id: Optional input DataSet ID (legacy).
            dataset_ref: Optional DataSetRef for input (preferred per ADR-0024).

        Returns:
            Analysis metadata dict.
        """
        analysis_id = str(uuid.uuid4())
        analysis_dir = self._analysis_dir(analysis_id)

        # Use DataSetRef if provided, else fall back to dataset_id
        input_dataset_id = dataset_ref.dataset_id if dataset_ref else dataset_id

        metadata = {
            "analysis_id": analysis_id,
            "name": name or f"SOV Analysis {analysis_id[:8]}",
            "created_at": datetime.now(UTC).isoformat(),
            "dataset_id": input_dataset_id,
            "parent_dataset_ids": [input_dataset_id] if input_dataset_id else [],
            "status": "created",
            "results": None,
        }

        with open(analysis_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata

    async def get_analysis(self, analysis_id: str) -> dict | None:
        """Get analysis by ID."""
        metadata_path = self._analysis_dir(analysis_id) / "metadata.json"
        if not metadata_path.exists():
            return None
        with open(metadata_path) as f:
            return json.load(f)

    async def list_analyses(
        self,
        limit: int = 50,
        cursor: str | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> list[dict]:
        """List analyses with cursor-based pagination.
        
        Args:
            limit: Maximum number of results.
            cursor: Analysis ID to start after (for pagination).
            sort_by: Field to sort by (created_at, name).
            sort_order: Sort order (asc, desc).
            
        Returns:
            List of analysis metadata dicts.
        """
        analyses_dir = self.sov_workspace / "analyses"
        if not analyses_dir.exists():
            return []

        # Load all analyses
        all_analyses = []
        for analysis_dir in analyses_dir.iterdir():
            if analysis_dir.is_dir():
                metadata = await self.get_analysis(analysis_dir.name)
                if metadata:
                    all_analyses.append(metadata)

        # Sort
        reverse = sort_order == "desc"
        if sort_by == "name":
            all_analyses.sort(key=lambda x: x.get("name", ""), reverse=reverse)
        else:  # default: created_at
            all_analyses.sort(key=lambda x: x.get("created_at", ""), reverse=reverse)

        # Apply cursor
        if cursor:
            cursor_idx = next(
                (i for i, a in enumerate(all_analyses) if a["analysis_id"] == cursor),
                -1,
            )
            if cursor_idx >= 0:
                all_analyses = all_analyses[cursor_idx + 1:]

        return all_analyses[:limit]

    async def run_analysis(
        self,
        analysis_id: str,
        config: ANOVAConfig,
        data: pl.DataFrame | None = None,
    ) -> list[ANOVAResult]:
        """Run ANOVA analysis.
        
        Per ADR-0024: Input column metadata is preserved for output.
        
        Args:
            analysis_id: Analysis ID
            config: ANOVA configuration
            data: Optional DataFrame (if not provided, loads from dataset_id)
            
        Returns:
            List of ANOVA results
        """
        metadata = await self.get_analysis(analysis_id)
        if not metadata:
            raise ValueError(f"Analysis not found: {analysis_id}")

        # Load data if not provided
        input_column_meta = None
        if data is None:
            dataset_id = metadata.get("dataset_id")
            if not dataset_id:
                raise ValueError("No data provided and no dataset_id set")
            data, manifest = await self.store.read_dataset_with_manifest(dataset_id)
            # Preserve input column metadata per ADR-0024
            if manifest:
                input_column_meta = {col.name: col for col in manifest.columns}
                metadata["input_column_meta"] = [
                    col.model_dump() for col in manifest.columns
                ]

        # Run ANOVA
        results = await run_anova_analysis(data, config)

        # Save results
        analysis_dir = self._analysis_dir(analysis_id)
        results_data = [
            {
                "response_column": r.response_column,
                "rows": [asdict(row) for row in r.rows],
                "total_variance": r.total_variance,
                "r_squared": r.r_squared,
                "factors": r.factors,
            }
            for r in results
        ]

        with open(analysis_dir / "results.json", "w") as f:
            json.dump(results_data, f, indent=2)

        # Generate visualization specs per ADR-0025
        viz_specs = self.viz_service.generate_all_visualizations(
            results=results,
            analysis_id=analysis_id,
            dataset_id=metadata.get("dataset_id"),
        )
        viz_specs_data = [spec.model_dump(mode="json") for spec in viz_specs]

        # Update metadata
        metadata["status"] = "completed"
        metadata["results"] = results_data
        metadata["visualization_specs"] = viz_specs_data
        metadata["completed_at"] = datetime.now(UTC).isoformat()

        with open(analysis_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)

        return results

    async def export_as_dataset(
        self,
        analysis_id: str,
        name: str | None = None,
    ) -> dict:
        """Export analysis results as a DataSet.
        
        Args:
            analysis_id: Analysis ID
            name: Optional name for the DataSet
            
        Returns:
            DataSet manifest dict
        """

        metadata = await self.get_analysis(analysis_id)
        if not metadata or not metadata.get("results"):
            raise ValueError("Analysis not found or not completed")

        # Convert results to DataFrame
        rows = []
        for result in metadata["results"]:
            for row in result["rows"]:
                rows.append({
                    "response_column": result["response_column"],
                    "source": row["source"],
                    "sum_squares": row["sum_squares"],
                    "df": row["df"],
                    "mean_square": row["mean_square"],
                    "f_statistic": row["f_statistic"],
                    "p_value": row["p_value"],
                    "variance_pct": row["variance_pct"],
                    "significant": row["significant"],
                })

        data = pl.DataFrame(rows)

        # Compute dataset ID
        dataset_id = compute_dataset_id(
            run_id=analysis_id,
            columns=data.columns,
            row_count=len(data),
        )

        # Create manifest with lineage per ADR-0024
        now = datetime.now(UTC)
        parent_ids = metadata.get("parent_dataset_ids", [])
        if not parent_ids and metadata.get("dataset_id"):
            parent_ids = [metadata.get("dataset_id")]

        # Get visualization specs from metadata (generated during run_analysis)
        viz_specs = metadata.get("visualization_specs", [])

        # Build column metadata with SOV annotations per ADR-0024
        input_column_meta = metadata.get("input_column_meta", [])
        input_meta_map = {c["name"]: c for c in input_column_meta} if input_column_meta else {}

        result_factors = metadata["results"][0]["factors"] if metadata["results"] else []
        result_responses = [r["response_column"] for r in metadata["results"]] if metadata["results"] else []

        columns = []
        for col in data.columns:
            # Start with input metadata if available
            base_meta = input_meta_map.get(col, {})

            # Determine SOV-specific annotations
            description = base_meta.get("description")
            if col in result_factors:
                description = f"ANOVA factor: {col}"
            elif col in result_responses:
                description = f"ANOVA response: {col}"
            elif col in ("source", "sum_squares", "df", "mean_square", "f_statistic", "p_value", "variance_pct", "significant"):
                description = f"ANOVA result field: {col}"

            columns.append(ColumnMeta(
                name=col,
                dtype=str(data[col].dtype),
                nullable=data[col].null_count() > 0,
                description=description,
                source_tool="sov",
                unit=base_meta.get("unit"),
            ))

        manifest = DataSetManifest(
            dataset_id=dataset_id,
            name=name or f"SOV Results - {analysis_id[:8]}",
            created_at=now,
            created_by_tool="sov",
            columns=columns,
            row_count=len(data),
            parent_dataset_ids=parent_ids,
            analysis_type="anova",
            factors=metadata["results"][0]["factors"] if metadata["results"] else None,
            response_columns=[r["response_column"] for r in metadata["results"]],
            visualization_specs=viz_specs,  # Per ADR-0025: Include viz contracts
        )

        # Write to shared storage
        await self.store.write_dataset(dataset_id, data, manifest)

        return manifest.model_dump()
