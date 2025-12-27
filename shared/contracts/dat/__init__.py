"""DAT (Data Aggregation Tool) contracts.

This package contains Pydantic models for DAT-specific data structures:
- Stage contracts for the parse/aggregate/export pipeline
- Extraction profiles for domain-agnostic configuration
- Table availability status tracking

All contracts are domain-agnostic; user-specific knowledge (column mappings,
aggregation rules, file patterns) is injected via profiles and configs.
"""

from shared.contracts.dat.profile import (
    AggregationRule,
    ColumnMapping,
    ExtractionProfile,
    ExtractionProfileRef,
    FilePattern,
    ProfileValidationResult,
)
from shared.contracts.dat.stage import (
    DATStageConfig,
    DATStageResult,
    DATStageState,
    DATStageType,
    ParseStageConfig,
    AggregateStageConfig,
    ExportStageConfig,
)
from shared.contracts.dat.table_status import (
    TableAvailability,
    TableAvailabilityStatus,
    TableStatusReport,
    TableHealthCheck,
)

__all__ = [
    # Stage contracts
    "DATStageType",
    "DATStageState",
    "DATStageConfig",
    "DATStageResult",
    "ParseStageConfig",
    "AggregateStageConfig",
    "ExportStageConfig",
    # Profile contracts
    "ExtractionProfile",
    "ExtractionProfileRef",
    "ColumnMapping",
    "AggregationRule",
    "FilePattern",
    "ProfileValidationResult",
    # Table status contracts
    "TableAvailability",
    "TableAvailabilityStatus",
    "TableStatusReport",
    "TableHealthCheck",
]
