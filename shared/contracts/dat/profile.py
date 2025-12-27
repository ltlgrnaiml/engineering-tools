"""DAT Extraction Profile contracts - domain-agnostic configuration.

Per ADR-0004: Profiles define deterministic extraction behavior.
Per ADR-0005: All domain-specific knowledge lives in profiles, not code.
Per ADR-0017: Profile IDs are deterministic hashes of profile content.

An ExtractionProfile is the single source of truth for:
- File patterns (which files to parse)
- Column mappings (how to extract columns)
- Aggregation rules (how to combine data)
- Validation rules (data quality checks)

Profiles are domain-agnostic containers that can hold ANY domain's rules.
The actual domain knowledge is injected when creating/editing the profile.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

__version__ = "0.1.0"


class FilePatternType(str, Enum):
    """How to match files for parsing."""

    GLOB = "glob"  # e.g., "*.csv", "**/*.dat"
    REGEX = "regex"  # e.g., r"wafer_\d+\.csv"
    EXTENSION = "extension"  # e.g., ".csv", ".txt"


class FilePattern(BaseModel):
    """Pattern for matching source files to parse.

    Patterns are evaluated in order; first match wins.
    Supports negative patterns (exclude) for fine-grained control.
    """

    pattern: str = Field(..., description="The pattern string (glob, regex, or extension)")
    pattern_type: FilePatternType = FilePatternType.GLOB
    exclude: bool = Field(False, description="If True, matching files are excluded")
    encoding: str | None = Field(None, description="Override default encoding for matches")
    parser_hint: str | None = Field(
        None,
        description="Parser to use: 'csv', 'excel', 'fixed_width', 'custom'",
    )
    priority: int = Field(0, description="Higher priority patterns evaluated first")

    @field_validator("pattern")
    @classmethod
    def validate_pattern(cls, v: str) -> str:
        """Ensure pattern is not empty."""
        if not v.strip():
            raise ValueError("Pattern cannot be empty")
        return v


class ColumnDataType(str, Enum):
    """Data types for column mapping."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    CATEGORICAL = "categorical"
    AUTO = "auto"  # Infer from data


class ColumnMapping(BaseModel):
    """Maps a source column to a standardized output column.

    Column mappings define:
    - Which source columns to extract (by name or position)
    - How to rename/transform them
    - Data type coercion rules
    - Validation constraints

    This is where domain-specific column names are translated to
    standardized names used across tools.
    """

    source_name: str | None = Field(
        None,
        description="Source column name (mutually exclusive with source_index)",
    )
    source_index: int | None = Field(
        None,
        ge=0,
        description="Source column index for positional matching",
    )
    source_pattern: str | None = Field(
        None,
        description="Regex pattern to match multiple source columns",
    )
    target_name: str = Field(..., description="Output column name (standardized)")
    data_type: ColumnDataType = ColumnDataType.AUTO
    nullable: bool = Field(True, description="Allow null/missing values")
    default_value: Any = Field(None, description="Default for missing values")
    required: bool = Field(False, description="Fail if column not found in source")

    # Transformation
    trim_whitespace: bool = Field(True, description="Strip leading/trailing whitespace")
    lowercase: bool = Field(False, description="Convert strings to lowercase")
    uppercase: bool = Field(False, description="Convert strings to uppercase")
    replace_pattern: str | None = Field(None, description="Regex pattern to replace")
    replace_with: str | None = Field(None, description="Replacement string")

    # Validation
    min_value: float | None = Field(None, description="Minimum numeric value")
    max_value: float | None = Field(None, description="Maximum numeric value")
    allowed_values: list[Any] | None = Field(None, description="Whitelist of allowed values")
    regex_validation: str | None = Field(None, description="Regex pattern values must match")

    # Metadata
    description: str | None = None
    unit: str | None = Field(None, description="Unit of measure (e.g., 'nm', '%')")
    category: str | None = Field(None, description="Logical grouping (e.g., 'identifier', 'measurement')")

    @model_validator(mode="after")
    def validate_source_specification(self) -> "ColumnMapping":
        """Ensure exactly one source specification method is used."""
        sources = [
            self.source_name is not None,
            self.source_index is not None,
            self.source_pattern is not None,
        ]
        if sum(sources) == 0:
            raise ValueError("Must specify source_name, source_index, or source_pattern")
        if sum(sources) > 1:
            raise ValueError("Specify only one of source_name, source_index, or source_pattern")
        return self

    @model_validator(mode="after")
    def validate_numeric_range(self) -> "ColumnMapping":
        """Ensure min_value <= max_value if both specified."""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(f"min_value ({self.min_value}) > max_value ({self.max_value})")
        return self


class AggregationFunction(str, Enum):
    """Available aggregation functions."""

    SUM = "sum"
    MEAN = "mean"
    MEDIAN = "median"
    MIN = "min"
    MAX = "max"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    STD = "std"
    VAR = "var"
    FIRST = "first"
    LAST = "last"
    LIST = "list"  # Collect into list
    CONCAT = "concat"  # Concatenate strings


class AggregationRule(BaseModel):
    """Rule for aggregating data across grouping levels.

    Aggregation rules define how columns are combined when grouping
    by hierarchical levels (e.g., wafer → lot → product).
    """

    column: str = Field(..., description="Column to aggregate (target_name from ColumnMapping)")
    function: AggregationFunction = AggregationFunction.MEAN
    output_name: str | None = Field(
        None,
        description="Output column name (default: {column}_{function})",
    )
    fill_value: Any = Field(None, description="Value to use for empty groups")
    filter_expression: str | None = Field(
        None,
        description="Filter rows before aggregation (pandas query syntax)",
    )
    percentile: float | None = Field(
        None,
        ge=0,
        le=100,
        description="Percentile value (only for percentile function)",
    )

    @model_validator(mode="after")
    def generate_default_output_name(self) -> "AggregationRule":
        """Generate output name if not specified."""
        if self.output_name is None:
            self.output_name = f"{self.column}_{self.function.value}"
        return self


class AggregationLevel(BaseModel):
    """A level in the aggregation hierarchy.

    Example hierarchy: measurement → wafer → lot → product
    Each level groups by different columns and applies aggregation rules.
    """

    name: str = Field(..., description="Level name (e.g., 'wafer', 'lot')")
    group_by_columns: list[str] = Field(
        ...,
        min_length=1,
        description="Columns to group by at this level",
    )
    aggregation_rules: list[AggregationRule] = Field(
        default_factory=list,
        description="How to aggregate non-grouping columns",
    )
    filter_expression: str | None = Field(
        None,
        description="Filter rows before grouping (pandas query syntax)",
    )
    sort_by: list[str] = Field(
        default_factory=list,
        description="Columns to sort output by",
    )
    sort_ascending: bool = Field(True, description="Sort direction")


class ValidationSeverity(str, Enum):
    """Severity level for validation failures."""

    ERROR = "error"  # Fail the stage
    WARNING = "warning"  # Log and continue
    INFO = "info"  # Log only


class ValidationRule(BaseModel):
    """Data quality validation rule.

    Validation rules are checked after parsing/aggregation to ensure
    data quality. Failed rules with ERROR severity stop processing.
    """

    name: str = Field(..., description="Human-readable rule name")
    expression: str = Field(
        ...,
        description="Boolean expression (pandas eval syntax) that should be True",
    )
    severity: ValidationSeverity = ValidationSeverity.ERROR
    message: str = Field(
        ...,
        description="Message to show when validation fails",
    )
    applies_to_stage: list[Literal["parse", "aggregate", "export"]] = Field(
        default=["parse", "aggregate"],
        description="Which stages to apply this validation",
    )


class ExtractionProfile(BaseModel):
    """Complete extraction profile defining parsing and aggregation rules.

    This is the core domain-agnostic configuration container for DAT.
    All domain-specific knowledge (column names, aggregation hierarchies,
    validation rules) is captured here, not in code.

    Per ADR-0004: profile_id is deterministic hash of profile content.
    Per ADR-0005: Profiles are the single source of domain knowledge.
    """

    # Identity
    profile_id: str = Field(
        ...,
        description="Deterministic hash of profile content (first 16 chars of SHA-256)",
    )
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    version: str = Field("1.0.0", description="Profile version (semver)")

    # Timestamps (per ADR-0008)
    created_at: datetime
    updated_at: datetime | None = None

    # File matching
    file_patterns: list[FilePattern] = Field(
        ...,
        min_length=1,
        description="Patterns for matching source files",
    )

    # Column extraction
    column_mappings: list[ColumnMapping] = Field(
        default_factory=list,
        description="How to extract and transform columns",
    )
    passthrough_unmapped: bool = Field(
        False,
        description="Include columns not explicitly mapped (with original names)",
    )
    ignore_columns: list[str] = Field(
        default_factory=list,
        description="Columns to explicitly ignore (not passthrough)",
    )

    # Aggregation
    aggregation_levels: list[AggregationLevel] = Field(
        default_factory=list,
        description="Hierarchical aggregation levels (bottom-up order)",
    )
    default_aggregation_level: str | None = Field(
        None,
        description="Default level for output (if not specified at export)",
    )

    # Parsing options
    csv_options: dict[str, Any] = Field(
        default_factory=lambda: {
            "delimiter": ",",
            "header_row": 0,
            "skip_rows": 0,
            "encoding": "utf-8",
        },
        description="Default CSV parsing options",
    )
    excel_options: dict[str, Any] = Field(
        default_factory=lambda: {
            "sheet_name": 0,
            "header_row": 0,
            "skip_rows": 0,
        },
        description="Default Excel parsing options",
    )

    # Validation
    validation_rules: list[ValidationRule] = Field(
        default_factory=list,
        description="Data quality validation rules",
    )

    # Metadata
    tags: list[str] = Field(default_factory=list)
    domain: str | None = Field(
        None,
        description="Domain identifier (e.g., 'semiconductor', 'finance')",
    )
    owner: str | None = Field(None, description="Profile owner/maintainer")

    @model_validator(mode="after")
    def validate_default_aggregation_level(self) -> "ExtractionProfile":
        """Ensure default_aggregation_level exists in aggregation_levels."""
        if self.default_aggregation_level is not None:
            level_names = {level.name for level in self.aggregation_levels}
            if self.default_aggregation_level not in level_names:
                raise ValueError(
                    f"default_aggregation_level '{self.default_aggregation_level}' "
                    f"not found in aggregation_levels: {level_names}"
                )
        return self

    @model_validator(mode="after")
    def validate_aggregation_rule_columns(self) -> "ExtractionProfile":
        """Ensure aggregation rules reference valid columns."""
        if not self.column_mappings and not self.passthrough_unmapped:
            return self  # Can't validate without column mappings

        target_names = {cm.target_name for cm in self.column_mappings}
        for level in self.aggregation_levels:
            for rule in level.aggregation_rules:
                if rule.column not in target_names and not self.passthrough_unmapped:
                    raise ValueError(
                        f"Aggregation rule references unknown column '{rule.column}' "
                        f"in level '{level.name}'"
                    )
        return self


class ExtractionProfileRef(BaseModel):
    """Lightweight reference to a profile for list responses."""

    profile_id: str
    name: str
    version: str
    domain: str | None = None
    file_pattern_count: int
    column_mapping_count: int
    aggregation_level_count: int
    created_at: datetime
    updated_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class ProfileValidationResult(BaseModel):
    """Result of validating a profile against source data."""

    profile_id: str
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    matched_files: int = Field(0, ge=0)
    matched_columns: int = Field(0, ge=0)
    unmapped_columns: list[str] = Field(default_factory=list)
    sample_data: dict[str, list[Any]] = Field(
        default_factory=dict,
        description="First N values from each mapped column",
    )


class CreateProfileRequest(BaseModel):
    """Request to create a new extraction profile."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    file_patterns: list[FilePattern]
    column_mappings: list[ColumnMapping] = Field(default_factory=list)
    aggregation_levels: list[AggregationLevel] = Field(default_factory=list)
    validation_rules: list[ValidationRule] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    domain: str | None = None


class UpdateProfileRequest(BaseModel):
    """Request to update an existing profile (creates new version)."""

    name: str | None = None
    description: str | None = None
    file_patterns: list[FilePattern] | None = None
    column_mappings: list[ColumnMapping] | None = None
    aggregation_levels: list[AggregationLevel] | None = None
    validation_rules: list[ValidationRule] | None = None
    tags: list[str] | None = None
    bump_version: Literal["major", "minor", "patch"] = "minor"
