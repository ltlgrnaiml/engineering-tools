"""API schemas for SOV Analyzer."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class CreateAnalysisRequest(BaseModel):
    """Request to create a new analysis."""
    name: str | None = None
    dataset_id: str | None = None


class CreateAnalysisResponse(BaseModel):
    """Response for created analysis."""
    analysis_id: str
    name: str
    created_at: datetime
    dataset_id: str | None = None
    status: str


class RunAnalysisRequest(BaseModel):
    """Request to run ANOVA analysis."""
    factors: list[str]
    response_columns: list[str]
    alpha: float = 0.05
    anova_type: Literal["one-way", "two-way", "n-way"] = "one-way"


class ANOVARowResponse(BaseModel):
    """Single row of ANOVA results."""
    source: str
    sum_squares: float
    df: int
    mean_square: float | None
    f_statistic: float | None
    p_value: float | None
    variance_pct: float
    significant: bool


class ANOVAResultResponse(BaseModel):
    """ANOVA result for a response variable."""
    response_column: str
    rows: list[ANOVARowResponse]
    total_variance: float
    r_squared: float
    factors: list[str]


class AnalysisResponse(BaseModel):
    """Full analysis response."""
    analysis_id: str
    name: str
    created_at: datetime
    completed_at: datetime | None = None
    dataset_id: str | None = None
    status: str
    results: list[ANOVAResultResponse] | None = None


class ExportRequest(BaseModel):
    """Request to export results as DataSet."""
    name: str | None = None
