"""Tier-0 Pydantic contracts for DAT profile schema (Option A, Contracts-as-SSOT).

Per ADR-0009 and ADR-0015: contracts are the single source of truth.
Per ADR-0011 and SPEC-DAT-0011/0012/0002: DAT profiles govern all extraction logic.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

__version__ = "1.0.0"


class RegexScope(str, Enum):
    """Where to apply regex extraction."""

    FILENAME = "filename"
    PATH = "path"
    FULL_PATH = "full_path"


class OnFailBehavior(str, Enum):
    """Behavior when a rule fails."""

    WARN = "warn"
    ERROR = "error"
    SKIP_FILE = "skip_file"


class StrategyType(str, Enum):
    """Extraction strategy types per SPEC-DAT-0012."""

    FLAT_OBJECT = "flat_object"
    HEADERS_DATA = "headers_data"
    ARRAY_OF_OBJECTS = "array_of_objects"
    REPEAT_OVER = "repeat_over"
    UNPIVOT = "unpivot"
    JOIN = "join"


class JoinHow(str, Enum):
    """Join strategy behavior."""

    LEFT = "left"
    RIGHT = "right"
    INNER = "inner"
    OUTER = "outer"


class RegexPattern(BaseModel):
    """Regex pattern for context extraction."""

    field: str = Field(..., description="Target context field")
    pattern: str = Field(..., description="Regex with named groups")
    scope: RegexScope = RegexScope.FILENAME
    required: bool = False
    description: str = ""
    example: str = ""
    transform: str | None = Field(None, description="Built-in transform name (e.g., parse_date)")
    transform_args: dict[str, Any] = Field(default_factory=dict)
    on_fail: OnFailBehavior = OnFailBehavior.WARN

    @field_validator("pattern")
    @classmethod
    def ensure_pattern_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("pattern cannot be empty")
        return value


class ContentPattern(BaseModel):
    """JSONPath-based context extraction."""

    field: str
    path: str
    required: bool = False
    default: Any | None = None
    description: str = ""
    example: str = ""
    on_fail: OnFailBehavior = OnFailBehavior.WARN


class ContextDefaults(BaseModel):
    """Context defaults configuration."""

    defaults: dict[str, Any] = Field(default_factory=dict)
    regex_patterns: list[RegexPattern] = Field(default_factory=list)
    content_patterns: list[ContentPattern] = Field(default_factory=list)
    allow_user_override: list[str] = Field(default_factory=list)


class RepeatOverConfig(BaseModel):
    """Repeat-over iteration configuration."""

    path: str = Field(..., description="JSONPath to array to iterate")
    as_var: str = Field(..., description="Variable name for array index/value")
    inject_fields: dict[str, str] = Field(
        default_factory=dict, description="Fields to inject from parent element"
    )


class JoinConfig(BaseModel):
    """Join configuration for strategy-level joins."""

    path: str = Field(..., description="JSONPath to dataset to join")
    key: str = Field(..., description="Key to join on")


class SelectConfig(BaseModel):
    """Extraction strategy configuration."""

    strategy: StrategyType
    path: str
    headers_key: str | None = None
    data_key: str | None = None
    repeat_over: RepeatOverConfig | None = None
    fields: list[str] | None = None
    flatten_nested: bool = False
    flatten_separator: str = "_"
    infer_headers: bool = False
    default_headers: list[str] | None = None
    id_vars: list[str] | None = None
    value_vars: list[str] | None = None
    var_name: str = "variable"
    value_name: str = "value"
    left: JoinConfig | None = None
    right: JoinConfig | None = None
    how: JoinHow = JoinHow.LEFT


class TableConfig(BaseModel):
    """Table extraction configuration."""

    id: str
    label: str
    description: str = ""
    select: SelectConfig
    stable_columns: list[str] = Field(default_factory=list)
    stable_columns_mode: Literal["warn", "error", "ignore"] = "warn"
    stable_columns_subset: bool = True
    validation_constraints: list[dict[str, Any]] = Field(default_factory=list)
    column_transforms: list[dict[str, Any]] = Field(default_factory=list)


class LevelConfig(BaseModel):
    """Aggregation level configuration."""

    name: str
    apply_context: str = ""
    tables: list[TableConfig] = Field(default_factory=list)


class ContextConfig(BaseModel):
    """Context mapping configuration."""

    name: str
    level: str
    paths: list[str] = Field(default_factory=list)
    key_map: dict[str, str] = Field(default_factory=dict)
    primary_keys: list[str] = Field(default_factory=list)
    time_fields: dict[str, str] | None = None


class AggregationConfig(BaseModel):
    """Aggregation output configuration."""

    id: str
    from_table: str
    group_by: list[str] = Field(default_factory=list)
    aggregations: dict[str, str] = Field(default_factory=dict)
    output_table: str = ""


class JoinOutputConfig(BaseModel):
    """Join output configuration."""

    id: str
    left_table: str
    right_table: str
    on: list[str] = Field(default_factory=list)
    how: JoinHow = JoinHow.LEFT


class OutputConfig(BaseModel):
    """Output configuration."""

    id: str
    from_level: str
    from_tables: list[str] = Field(default_factory=list)
    include_context: bool = True
    format: str = "parquet"


class GovernanceAccessConfig(BaseModel):
    """Access control configuration."""

    read: list[str] = Field(default_factory=lambda: ["all"])
    modify: list[str] = Field(default_factory=lambda: ["admin"])
    delete: list[str] = Field(default_factory=lambda: ["admin"])


class GovernanceAuditConfig(BaseModel):
    """Audit configuration."""

    log_access: bool = True
    log_modifications: bool = True
    retention_days: int = 365


class GovernanceComplianceConfig(BaseModel):
    """Compliance configuration."""

    data_classification: Literal["public", "internal", "confidential"] = "internal"
    pii_columns: list[str] = Field(default_factory=list)
    mask_in_preview: list[str] = Field(default_factory=list)


class GovernanceLimitsConfig(BaseModel):
    """Resource and complexity limits."""

    max_files_per_run: int = 1000
    max_file_size_mb: int = 500
    max_total_size_gb: int = 10
    max_rows_output: int = 10_000_000
    max_tables_per_level: int = 50
    max_columns_per_table: int = 500
    parse_timeout_seconds: int = 3600
    preview_timeout_seconds: int = 30


class GovernanceConfig(BaseModel):
    """Governance configuration."""

    access: GovernanceAccessConfig | None = None
    audit: GovernanceAuditConfig | None = None
    compliance: GovernanceComplianceConfig | None = None
    limits: GovernanceLimitsConfig | None = None


class UITableSelectionConfig(BaseModel):
    """UI table selection hints."""

    group_by_level: bool = True
    default_selected: dict[str, list[str]] = Field(default_factory=dict)
    collapsed_by_default: list[str] = Field(default_factory=list)


class UIPreviewConfig(BaseModel):
    """UI preview hints."""

    max_rows: int = 100
    max_columns: int = 50
    column_width: str = "auto"
    number_format: str = "0.0000"
    date_format: str = "YYYY-MM-DD HH:mm:ss"
    null_display: str = "—"


class UIConfig(BaseModel):
    """UI configuration hints."""

    show_file_preview: bool = True
    max_preview_files: int = 10
    highlight_matching: bool = True
    table_selection: UITableSelectionConfig | None = None
    preview: UIPreviewConfig | None = None
    show_regex_matches: bool = True
    editable_fields: list[str] = Field(default_factory=list)
    readonly_fields: list[str] = Field(default_factory=list)
    default_name_template: str = "{profile_title} - {lot_id}"
    show_row_count: bool = True
    show_column_list: bool = True
    allow_format_selection: bool = True
    formats: list[str] = Field(default_factory=lambda: ["parquet", "csv", "excel"])


class DATProfile(BaseModel):
    """Complete DAT extraction profile (Tier-0 Pydantic contract)."""

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    # Schema + versioning
    schema_version: str
    version: int

    # Meta
    profile_id: str
    title: str
    description: str = ""
    created_by: str = ""
    created_at: datetime | None = None
    modified_at: datetime | None = None
    revision: int = 1
    hash: str = ""
    owner: str = ""
    classification: Literal["public", "internal", "confidential"] = "internal"
    domain: str = ""
    tags: list[str] = Field(default_factory=list)

    # Datasource
    datasource_id: str = ""
    datasource_label: str = ""
    datasource_format: str = "json"
    datasource_filters: dict[str, Any] = Field(default_factory=dict)
    datasource_options: dict[str, Any] = Field(default_factory=dict)

    # Population
    default_strategy: str = "all"
    include_populations: list[str] = Field(default_factory=list)

    # Context
    context_defaults: ContextDefaults | None = None
    contexts: list[ContextConfig] = Field(default_factory=list)

    # Levels and tables
    levels: list[LevelConfig] = Field(default_factory=list)

    # Normalization
    nan_values: list[str] = Field(default_factory=list)
    units_policy: Literal["preserve", "normalize", "strip"] = "preserve"
    numeric_coercion: bool = True
    nan_replacement: Any | None = None
    numeric_errors: Literal["coerce", "raise", "ignore"] | None = None
    string_strip: bool | None = None
    string_case: Literal["preserve", "upper", "lower", "title"] | None = None

    # Transforms
    column_renames: dict[str, str] = Field(default_factory=dict)
    calculated_columns: list[dict[str, Any]] = Field(default_factory=list)
    type_coercion: list[dict[str, Any]] = Field(default_factory=list)
    row_filters: list[dict[str, Any]] = Field(default_factory=list)

    # Outputs
    default_outputs: list[OutputConfig] = Field(default_factory=list)
    optional_outputs: list[OutputConfig] = Field(default_factory=list)
    aggregations: list[AggregationConfig] = Field(default_factory=list)
    joins: list[JoinOutputConfig] = Field(default_factory=list)

    # UI
    ui: UIConfig | None = None

    # Validation
    schema_rules: dict[str, Any] = Field(default_factory=dict)
    row_rules: list[dict[str, Any]] = Field(default_factory=list)
    aggregate_rules: list[dict[str, Any]] = Field(default_factory=list)
    on_validation_fail: Literal["continue", "stop", "quarantine"] = "continue"
    quarantine_table: str = "validation_failures"

    # Governance
    governance: GovernanceConfig | None = None

    def get_level(self, name: str) -> LevelConfig | None:
        """Get a level configuration by name."""
        return next((level for level in self.levels if level.name == name), None)

    def get_table(self, level_name: str, table_id: str) -> TableConfig | None:
        """Get a table configuration by level and table ID."""
        level = self.get_level(level_name)
        if not level:
            return None
        return next((table for table in level.tables if table.id == table_id), None)

    def get_all_tables(self) -> list[tuple[str, TableConfig]]:
        """Get all tables across all levels."""
        result: list[tuple[str, TableConfig]] = []
        for level in self.levels:
            for table in level.tables:
                result.append((level.name, table))
        return result

    def extract_context_from_filename(self, filename: str) -> dict[str, str]:
        """Extract context values from filename using regex patterns."""
        if not self.context_defaults:
            return {}

        context: dict[str, str] = {}
        for pattern in self.context_defaults.regex_patterns:
            if pattern.scope != RegexScope.FILENAME:
                continue
            try:
                import re

                match = re.search(pattern.pattern, filename)
                if match:
                    groups = match.groupdict()
                    if pattern.field in groups:
                        context[pattern.field] = groups[pattern.field]
            except re.error as exc:  # pragma: no cover - defensive
                raise ValueError(f"Invalid regex pattern for '{pattern.field}': {exc}") from exc

        return context

    @model_validator(mode="after")
    def validate_core(self) -> "DATProfile":
        """Core schema validations."""
        if not self.profile_id:
            raise ValueError("profile_id is required")
        if not self.title:
            raise ValueError("title is required")
        if self.levels:
            table_ids = set()
            for level in self.levels:
                for table in level.tables:
                    key = (level.name, table.id)
                    if key in table_ids:
                        raise ValueError(f"Duplicate table id '{table.id}' in level '{level.name}'")
                    table_ids.add(key)
        return self


class ProfileValidationResult(BaseModel):
    """Result of validating a profile against source data."""

    profile_id: str
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    matched_files: int = Field(0, ge=0)
    matched_columns: int = Field(0, ge=0)
    unmapped_columns: list[str] = Field(default_factory=list)


__all__ = [
    "DATProfile",
    "LevelConfig",
    "TableConfig",
    "SelectConfig",
    "RepeatOverConfig",
    "ContextDefaults",
    "ContextConfig",
    "OutputConfig",
    "AggregationConfig",
    "JoinOutputConfig",
    "GovernanceConfig",
    "UIConfig",
    "ProfileValidationResult",
    "StrategyType",
]
