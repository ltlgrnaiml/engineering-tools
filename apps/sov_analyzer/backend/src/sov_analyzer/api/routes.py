"""SOV API routes.

Per ADR-0029: All routes use versioned /v1/ prefix.
Per API-003: Error responses MUST use standard error schema.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from shared.contracts.core.error_response import (
    ErrorResponse,
    ErrorCategory,
    ErrorDetail,
    NotFoundErrorResponse,
    ValidationErrorResponse,
    create_error_response,
)
from ..core.analysis_manager import AnalysisManager
from ..analysis.anova import ANOVAConfig, VarianceValidationError
from .schemas import (
    CreateAnalysisRequest,
    CreateAnalysisResponse,
    RunAnalysisRequest,
    AnalysisResponse,
    ANOVAResultResponse,
    ANOVARowResponse,
    ExportRequest,
)

# Per ADR-0029: Tool-specific routes use /v1/ prefix
router = APIRouter(prefix="/v1")
manager = AnalysisManager()

TOOL_NAME = "sov"


def _raise_error(
    status_code: int,
    message: str,
    category: ErrorCategory | None = None,
    field: str | None = None,
) -> None:
    """Raise HTTPException with standardized error response.
    
    Per API-003: All error responses use standard ErrorResponse schema.
    """
    details = []
    if field:
        details.append(ErrorDetail(field=field, message=message))
    
    error = create_error_response(
        status_code=status_code,
        message=message,
        category=category,
        details=details,
        tool=TOOL_NAME,
    )
    raise HTTPException(
        status_code=status_code,
        detail=error.model_dump(mode="json"),
    )


@router.post("/analyses", response_model=CreateAnalysisResponse)
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


@router.get("/analyses")
async def list_analyses(
    limit: int = 50,
    cursor: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    """List SOV analyses with cursor-based pagination.
    
    Args:
        limit: Maximum number of results to return (default 50, max 100).
        cursor: Cursor for pagination (analysis_id to start after).
        sort_by: Field to sort by (created_at, name).
        sort_order: Sort order (asc, desc).
        
    Returns:
        Paginated list with next_cursor for continuation.
    """
    limit = min(limit, 100)  # Cap at 100
    
    analyses = await manager.list_analyses(
        limit=limit + 1,  # Fetch one extra to check for more
        cursor=cursor,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    
    has_more = len(analyses) > limit
    if has_more:
        analyses = analyses[:limit]
    
    next_cursor = analyses[-1]["analysis_id"] if has_more and analyses else None
    
    return {
        "items": analyses,
        "limit": limit,
        "has_more": has_more,
        "next_cursor": next_cursor,
    }


@router.get("/analyses/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get SOV analysis details."""
    analysis = await manager.get_analysis(analysis_id)
    if not analysis:
        _raise_error(
            status_code=404,
            message=f"Analysis not found: {analysis_id}",
            category=ErrorCategory.NOT_FOUND,
        )
    
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


@router.post("/analyses/{analysis_id}/run")
async def run_analysis(analysis_id: str, request: RunAnalysisRequest):
    """Run ANOVA analysis."""
    analysis = await manager.get_analysis(analysis_id)
    if not analysis:
        _raise_error(
            status_code=404,
            message=f"Analysis not found: {analysis_id}",
            category=ErrorCategory.NOT_FOUND,
        )
    
    config = ANOVAConfig(
        factors=request.factors,
        response_columns=request.response_columns,
        alpha=request.alpha,
        anova_type=request.anova_type,
        seed=request.seed,  # Per ADR-0022: Deterministic computation
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
    except VarianceValidationError as e:
        _raise_error(
            status_code=422,
            message=f"Variance validation failed: {e}",
            category=ErrorCategory.VALIDATION,
            field="variance",
        )
    except ValueError as e:
        _raise_error(
            status_code=400,
            message=str(e),
            category=ErrorCategory.VALIDATION,
        )


@router.post("/analyses/{analysis_id}/export")
async def export_dataset(analysis_id: str, request: ExportRequest):
    """Export analysis results as DataSet."""
    try:
        manifest = await manager.export_as_dataset(
            analysis_id=analysis_id,
            name=request.name,
        )
        return manifest
    except ValueError as e:
        _raise_error(
            status_code=400,
            message=str(e),
            category=ErrorCategory.VALIDATION,
        )
