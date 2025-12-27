"""SOV API routes."""
from fastapi import APIRouter, HTTPException

from ..core.analysis_manager import AnalysisManager
from ..analysis.anova import ANOVAConfig
from .schemas import (
    CreateAnalysisRequest,
    CreateAnalysisResponse,
    RunAnalysisRequest,
    AnalysisResponse,
    ANOVAResultResponse,
    ANOVARowResponse,
    ExportRequest,
)

router = APIRouter()
manager = AnalysisManager()


@router.post("/v1/analyses", response_model=CreateAnalysisResponse)
async def create_analysis(request: CreateAnalysisRequest):
    """Create a new SOV analysis."""
    analysis = await manager.create_analysis(
        name=request.name,
        dataset_id=request.dataset_id,
    )
    return CreateAnalysisResponse(
        analysis_id=analysis["analysis_id"],
        name=analysis["name"],
        created_at=analysis["created_at"],
        dataset_id=analysis.get("dataset_id"),
        status=analysis["status"],
    )


@router.get("/v1/analyses")
async def list_analyses(limit: int = 50):
    """List SOV analyses."""
    return await manager.list_analyses(limit=limit)


@router.get("/v1/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get SOV analysis details."""
    analysis = await manager.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    results = None
    if analysis.get("results"):
        results = [
            ANOVAResultResponse(
                response_column=r["response_column"],
                rows=[ANOVARowResponse(**row) for row in r["rows"]],
                total_variance=r["total_variance"],
                r_squared=r["r_squared"],
                factors=r["factors"],
            )
            for r in analysis["results"]
        ]
    
    return AnalysisResponse(
        analysis_id=analysis["analysis_id"],
        name=analysis["name"],
        created_at=analysis["created_at"],
        completed_at=analysis.get("completed_at"),
        dataset_id=analysis.get("dataset_id"),
        status=analysis["status"],
        results=results,
    )


@router.post("/v1/analyses/{analysis_id}/run")
async def run_analysis(analysis_id: str, request: RunAnalysisRequest):
    """Run ANOVA analysis."""
    analysis = await manager.get_analysis(analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    config = ANOVAConfig(
        factors=request.factors,
        response_columns=request.response_columns,
        alpha=request.alpha,
        anova_type=request.anova_type,
    )
    
    try:
        results = await manager.run_analysis(analysis_id, config)
        
        return [
            ANOVAResultResponse(
                response_column=r.response_column,
                rows=[
                    ANOVARowResponse(
                        source=row.source,
                        sum_squares=row.sum_squares,
                        df=row.df,
                        mean_square=row.mean_square,
                        f_statistic=row.f_statistic,
                        p_value=row.p_value,
                        variance_pct=row.variance_pct,
                        significant=row.significant,
                    )
                    for row in r.rows
                ],
                total_variance=r.total_variance,
                r_squared=r.r_squared,
                factors=r.factors,
            )
            for r in results
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/v1/analyses/{analysis_id}/export")
async def export_dataset(analysis_id: str, request: ExportRequest):
    """Export analysis results as DataSet."""
    try:
        manifest = await manager.export_as_dataset(
            analysis_id=analysis_id,
            name=request.name,
        )
        return manifest
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
