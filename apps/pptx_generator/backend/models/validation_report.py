"""Validation Report models.

Models for Four Bars validation status and reports.
"""

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ValidationStatus(str, Enum):
    """Validation status for a bar."""

    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class ValidationWarning(BaseModel):
    """A validation warning with suggested fix.

    Attributes:
        severity: Warning severity (info, warning, error).
        message: Warning message.
        suggested_fix: Suggested action to fix the issue.
    """

    severity: str = Field(..., description="Severity level")
    message: str = Field(..., description="Warning message")
    suggested_fix: str | None = Field(None, description="Suggested fix")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "severity": "warning",
            "message": "Context 'wafer' not mapped",
            "suggested_fix": "Add mapping for 'wafer' context in step 6",
        }
    })


class BarStatus(BaseModel):
    """Status for one of the Four Bars.

    Attributes:
        status: Overall status (green, yellow, red).
        coverage_percentage: Percentage of requirements met.
        missing_items: List of items not satisfied.
        warnings: List of validation warnings.
    """

    status: ValidationStatus = Field(..., description="Overall status")
    coverage_percentage: float = Field(..., ge=0.0, le=100.0, description="Coverage percentage")
    missing_items: list[str] = Field(default_factory=list, description="Missing items")
    warnings: list[ValidationWarning] = Field(
        default_factory=list, description="Validation warnings"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "yellow",
            "coverage_percentage": 66.7,
            "missing_items": ["wafer"],
            "warnings": [
                {
                    "severity": "warning",
                    "message": "Context 'wafer' not mapped",
                    "suggested_fix": "Add mapping in context editor",
                }
            ],
        }
    })


class FourBarsStatus(BaseModel):
    """Complete Four Bars validation status.

    Attributes:
        required_context: Status of context bar.
        required_metrics: Status of metrics bar.
        required_data_levels: Status of data levels bar.
        required_renderers: Status of renderers bar.
    """

    required_context: BarStatus = Field(..., description="Context bar status")
    required_metrics: BarStatus = Field(..., description="Metrics bar status")
    required_data_levels: BarStatus = Field(..., description="Data levels bar status")
    required_renderers: BarStatus = Field(..., description="Renderers bar status")

    def is_all_green(self) -> bool:
        """Check if all four bars are green.

        Returns:
            True if all bars are green.
        """
        return (
            self.required_context.status == ValidationStatus.GREEN
            and self.required_metrics.status == ValidationStatus.GREEN
            and self.required_data_levels.status == ValidationStatus.GREEN
            and self.required_renderers.status == ValidationStatus.GREEN
        )

    def get_blocking_issues(self) -> list[str]:
        """Get list of all blocking issues (red status items).

        Returns:
            List of blocking issue descriptions.
        """
        issues = []
        if self.required_context.status == ValidationStatus.RED:
            issues.extend(self.required_context.missing_items)
        if self.required_metrics.status == ValidationStatus.RED:
            issues.extend(self.required_metrics.missing_items)
        if self.required_data_levels.status == ValidationStatus.RED:
            issues.extend(self.required_data_levels.missing_items)
        if self.required_renderers.status == ValidationStatus.RED:
            issues.extend(self.required_renderers.missing_items)
        return issues

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "required_context": {
                "status": "green",
                "coverage_percentage": 100.0,
                "missing_items": [],
                "warnings": [],
            },
            "required_metrics": {
                "status": "green",
                "coverage_percentage": 100.0,
                "missing_items": [],
                "warnings": [],
            },
            "required_data_levels": {
                "status": "green",
                "coverage_percentage": 100.0,
                "missing_items": [],
                "warnings": [],
            },
            "required_renderers": {
                "status": "green",
                "coverage_percentage": 100.0,
                "missing_items": [],
                "warnings": [],
            },
        }
    })


# Validation test
if __name__ == "__main__":
    # Test all green
    all_green = FourBarsStatus(
        required_context=BarStatus(status=ValidationStatus.GREEN, coverage_percentage=100.0),
        required_metrics=BarStatus(status=ValidationStatus.GREEN, coverage_percentage=100.0),
        required_data_levels=BarStatus(status=ValidationStatus.GREEN, coverage_percentage=100.0),
        required_renderers=BarStatus(status=ValidationStatus.GREEN, coverage_percentage=100.0),
    )
    assert all_green.is_all_green()
    assert len(all_green.get_blocking_issues()) == 0

    # Test with red bar
    has_red = FourBarsStatus(
        required_context=BarStatus(
            status=ValidationStatus.RED,
            coverage_percentage=66.7,
            missing_items=["wafer"],
        ),
        required_metrics=BarStatus(status=ValidationStatus.GREEN, coverage_percentage=100.0),
        required_data_levels=BarStatus(status=ValidationStatus.GREEN, coverage_percentage=100.0),
        required_renderers=BarStatus(status=ValidationStatus.GREEN, coverage_percentage=100.0),
    )
    assert not has_red.is_all_green()
    assert "wafer" in has_red.get_blocking_issues()

    print("All validation report tests passed!")
