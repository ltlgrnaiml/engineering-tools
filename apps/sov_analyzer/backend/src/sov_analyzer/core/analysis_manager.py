"""Analysis manager for SOV tool."""
import uuid
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import polars as pl

from shared.storage.artifact_store import ArtifactStore
from ..analysis.anova import ANOVAConfig, ANOVAResult, run_anova_analysis


class AnalysisManager:
    """Manages SOV analysis runs."""
    
    def __init__(self, workspace_path: Path | None = None):
        if workspace_path is None:
            workspace_path = Path.cwd() / "workspace"
        self.workspace = workspace_path
        self.sov_workspace = self.workspace / "tools" / "sov"
        self.sov_workspace.mkdir(parents=True, exist_ok=True)
        self.store = ArtifactStore(workspace_path)
    
    def _analysis_dir(self, analysis_id: str) -> Path:
        """Get directory for an analysis."""
        path = self.sov_workspace / "analyses" / analysis_id
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    async def create_analysis(
        self,
        name: str | None = None,
        dataset_id: str | None = None,
    ) -> dict:
        """Create a new SOV analysis.
        
        Args:
            name: Optional human-readable name
            dataset_id: Optional input DataSet ID
            
        Returns:
            Analysis metadata dict
        """
        analysis_id = str(uuid.uuid4())
        analysis_dir = self._analysis_dir(analysis_id)
        
        metadata = {
            "analysis_id": analysis_id,
            "name": name or f"SOV Analysis {analysis_id[:8]}",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "dataset_id": dataset_id,
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
    
    async def list_analyses(self, limit: int = 50) -> list[dict]:
        """List recent analyses."""
        analyses_dir = self.sov_workspace / "analyses"
        if not analyses_dir.exists():
            return []
        
        analyses = []
        for analysis_dir in sorted(analyses_dir.iterdir(), reverse=True)[:limit]:
            if analysis_dir.is_dir():
                metadata = await self.get_analysis(analysis_dir.name)
                if metadata:
                    analyses.append(metadata)
        return analyses
    
    async def run_analysis(
        self,
        analysis_id: str,
        config: ANOVAConfig,
        data: pl.DataFrame | None = None,
    ) -> list[ANOVAResult]:
        """Run ANOVA analysis.
        
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
        if data is None:
            dataset_id = metadata.get("dataset_id")
            if not dataset_id:
                raise ValueError("No data provided and no dataset_id set")
            data = await self.store.read_dataset(dataset_id)
        
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
        
        # Update metadata
        metadata["status"] = "completed"
        metadata["results"] = results_data
        metadata["completed_at"] = datetime.now(timezone.utc).isoformat()
        
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
        from shared.contracts.core.dataset import DataSetManifest, ColumnMeta
        from shared.utils.stage_id import compute_dataset_id
        
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
        
        # Create manifest
        now = datetime.now(timezone.utc)
        manifest = DataSetManifest(
            dataset_id=dataset_id,
            name=name or f"SOV Results - {analysis_id[:8]}",
            description=f"ANOVA results from SOV analysis {analysis_id}",
            created_at=now,
            created_by_tool="sov",
            columns=[
                ColumnMeta(
                    name=col,
                    dtype=str(data[col].dtype),
                    nullable=data[col].null_count() > 0,
                    source_tool="sov",
                )
                for col in data.columns
            ],
            row_count=len(data),
            parent_ids=[metadata.get("dataset_id")] if metadata.get("dataset_id") else [],
        )
        
        # Write to shared storage
        await self.store.write_dataset(dataset_id, data, manifest)
        
        return manifest.model_dump()
