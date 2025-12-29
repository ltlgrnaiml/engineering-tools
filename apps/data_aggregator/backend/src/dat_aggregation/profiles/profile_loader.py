"""Profile loader for DAT extraction profiles.

Per ADR-0011: Profiles are the single source of truth for extraction logic.
Loads YAML profiles and provides typed access to profile configuration.
"""
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from shared.contracts.dat.profile import ProfileValidationResult


@dataclass
class RegexPattern:
    """Regex pattern for context extraction.
    
    Per DESIGN §4: Supports transforms like parse_date, uppercase, etc.
    """
    field: str
    pattern: str
    scope: str = "filename"
    required: bool = False
    description: str = ""
    example: str = ""
    transform: str | None = None  # e.g., "parse_date", "uppercase"
    transform_args: dict[str, Any] = field(default_factory=dict)
    on_fail: str = "warn"  # warn, error, skip_file


@dataclass
class ContextDefaults:
    """Context defaults section of profile."""
    defaults: dict[str, Any] = field(default_factory=dict)
    regex_patterns: list[RegexPattern] = field(default_factory=list)


@dataclass
class TableSelect:
    """Table selection configuration."""
    strategy: str  # "flat_object", "headers_data"
    path: str
    headers_key: str | None = None
    data_key: str | None = None
    repeat_over: dict[str, str] | None = None


@dataclass
class TableConfig:
    """Configuration for a single table extraction.
    
    Per DESIGN §5, §7: Supports stable columns and value constraints.
    """
    id: str
    label: str
    description: str = ""
    select: TableSelect | None = None
    stable_columns: list[str] = field(default_factory=list)
    stable_columns_mode: str = "warn"
    stable_columns_subset: bool = True
    # Per DESIGN §7: Value validation constraints
    validation_constraints: list[dict[str, Any]] = field(default_factory=list)
    # Per DESIGN §6: Column transforms at table level
    column_transforms: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class LevelConfig:
    """Configuration for a data level (run, image, etc.)."""
    name: str
    apply_context: str = ""
    tables: list[TableConfig] = field(default_factory=list)


@dataclass
class ContextConfig:
    """Context configuration for key mapping."""
    name: str
    level: str
    paths: list[str] = field(default_factory=list)
    key_map: dict[str, str] = field(default_factory=dict)
    primary_keys: list[str] = field(default_factory=list)
    time_fields: dict[str, str] | None = None


@dataclass
class AggregationConfig:
    """Aggregation output configuration per DESIGN §8."""
    id: str
    from_table: str
    group_by: list[str] = field(default_factory=list)
    aggregations: dict[str, str] = field(default_factory=dict)  # column -> agg_func
    output_table: str = ""


@dataclass
class JoinOutputConfig:
    """Join output configuration per DESIGN §8."""
    id: str
    left_table: str
    right_table: str
    on: list[str] = field(default_factory=list)
    how: str = "left"  # left, right, inner, outer


@dataclass
class OutputConfig:
    """Output configuration per DESIGN §8."""
    id: str
    from_level: str
    from_tables: list[str] = field(default_factory=list)
    include_context: bool = True
    format: str = "parquet"  # parquet, csv, excel


@dataclass
class GovernanceAccessConfig:
    """Access control configuration per DESIGN §10."""
    read: list[str] = field(default_factory=lambda: ["all"])
    modify: list[str] = field(default_factory=lambda: ["admin"])
    delete: list[str] = field(default_factory=lambda: ["admin"])


@dataclass
class GovernanceAuditConfig:
    """Audit trail configuration per DESIGN §10."""
    log_access: bool = True
    log_modifications: bool = True
    retention_days: int = 365


@dataclass
class GovernanceComplianceConfig:
    """Compliance configuration per DESIGN §10."""
    data_classification: str = "internal"  # public, internal, confidential
    pii_columns: list[str] = field(default_factory=list)
    mask_in_preview: list[str] = field(default_factory=list)


@dataclass
class GovernanceLimitsConfig:
    """Resource and complexity limits per DESIGN §10."""
    max_files_per_run: int = 1000
    max_file_size_mb: int = 500
    max_total_size_gb: int = 10
    max_rows_output: int = 10_000_000
    max_tables_per_level: int = 50
    max_columns_per_table: int = 500
    parse_timeout_seconds: int = 3600
    preview_timeout_seconds: int = 30


@dataclass
class GovernanceConfig:
    """Governance configuration per DESIGN §10."""
    access: GovernanceAccessConfig | None = None
    audit: GovernanceAuditConfig | None = None
    compliance: GovernanceComplianceConfig | None = None
    limits: GovernanceLimitsConfig | None = None


@dataclass
class UITableSelectionConfig:
    """UI table selection hints per DESIGN §9."""
    group_by_level: bool = True
    default_selected: dict[str, list[str]] = field(default_factory=dict)
    collapsed_by_default: list[str] = field(default_factory=list)


@dataclass
class UIPreviewConfig:
    """UI preview hints per DESIGN §9."""
    max_rows: int = 100
    max_columns: int = 50
    column_width: str = "auto"  # auto, fixed, wrap
    number_format: str = "0.0000"
    date_format: str = "YYYY-MM-DD HH:mm:ss"
    null_display: str = "—"


@dataclass
class UIConfig:
    """UI hints configuration per DESIGN §9."""
    # Discovery stage
    show_file_preview: bool = True
    max_preview_files: int = 10
    highlight_matching: bool = True
    # Table selection
    table_selection: UITableSelectionConfig | None = None
    # Preview
    preview: UIPreviewConfig | None = None
    # Context stage
    show_regex_matches: bool = True
    editable_fields: list[str] = field(default_factory=list)
    readonly_fields: list[str] = field(default_factory=list)
    # Export stage
    default_name_template: str = "{profile_title} - {lot_id}"
    show_row_count: bool = True
    show_column_list: bool = True
    allow_format_selection: bool = True
    formats: list[str] = field(default_factory=lambda: ["parquet", "csv", "excel"])


@dataclass
class DATProfile:
    """Complete DAT extraction profile."""
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

    # Datasource
    datasource_id: str = ""
    datasource_label: str = ""
    datasource_format: str = "json"
    datasource_filters: dict[str, Any] = field(default_factory=dict)
    datasource_options: dict[str, Any] = field(default_factory=dict)

    # Population
    default_strategy: str = "all"
    include_populations: list[str] = field(default_factory=list)

    # Context
    context_defaults: ContextDefaults | None = None
    contexts: list[ContextConfig] = field(default_factory=list)

    # Levels and tables
    levels: list[LevelConfig] = field(default_factory=list)

    # Normalization
    nan_values: list[str] = field(default_factory=list)
    units_policy: str = "preserve"
    numeric_coercion: bool = True
    
    # Per DESIGN §6: Global transforms
    column_renames: dict[str, str] = field(default_factory=dict)
    calculated_columns: list[dict[str, Any]] = field(default_factory=list)
    type_coercion: list[dict[str, Any]] = field(default_factory=list)

    # Outputs
    default_outputs: list[OutputConfig] = field(default_factory=list)
    optional_outputs: list[OutputConfig] = field(default_factory=list)
    # Per DESIGN §8: Aggregation and join outputs
    aggregations: list[AggregationConfig] = field(default_factory=list)
    joins: list[JoinOutputConfig] = field(default_factory=list)
    
    # Per DESIGN §9: UI hints
    ui: UIConfig | None = None
    
    # Per DESIGN §6: Row filters at profile level
    row_filters: list[dict[str, Any]] = field(default_factory=list)
    
    # Per DESIGN §7: Advanced validation rules
    schema_rules: dict[str, Any] = field(default_factory=dict)
    row_rules: list[dict[str, Any]] = field(default_factory=list)
    aggregate_rules: list[dict[str, Any]] = field(default_factory=list)
    on_validation_fail: str = "continue"  # continue, stop, quarantine
    quarantine_table: str = "validation_failures"
    
    # Per DESIGN §8: File naming configuration
    file_naming_template: str = "{profile_id}_{lot_id}_{timestamp}"
    file_naming_timestamp_format: str = "%Y%m%d_%H%M%S"
    file_naming_sanitize: bool = True
    
    # Per DESIGN §10: Governance
    governance: GovernanceConfig | None = None
    
    # Per DESIGN §1: Extended metadata
    owner: str = ""
    classification: str = "internal"  # public, internal, confidential
    domain: str = ""
    tags: list[str] = field(default_factory=list)

    def get_level(self, name: str) -> LevelConfig | None:
        """Get level configuration by name."""
        for level in self.levels:
            if level.name == name:
                return level
        return None

    def get_table(self, level_name: str, table_id: str) -> TableConfig | None:
        """Get table configuration by level and table ID."""
        level = self.get_level(level_name)
        if not level:
            return None
        for table in level.tables:
            if table.id == table_id:
                return table
        return None

    def get_all_tables(self) -> list[tuple[str, TableConfig]]:
        """Get all tables across all levels as (level_name, table) tuples."""
        result = []
        for level in self.levels:
            for table in level.tables:
                result.append((level.name, table))
        return result

    def extract_context_from_filename(self, filename: str) -> dict[str, str]:
        """Extract context values from filename using regex patterns."""
        if not self.context_defaults:
            return {}

        context = {}
        for pattern in self.context_defaults.regex_patterns:
            if pattern.scope != "filename":
                continue
            try:
                match = re.search(pattern.pattern, filename)
                if match:
                    # Get named group matching the field
                    groups = match.groupdict()
                    if pattern.field in groups:
                        context[pattern.field] = groups[pattern.field]
            except re.error:
                continue

        return context


def load_profile(path: Path | str) -> DATProfile:
    """Load a DAT profile from YAML file.
    
    Args:
        path: Path to YAML profile file
        
    Returns:
        Parsed DATProfile object
    """
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return _parse_profile(data)


def load_profile_from_string(yaml_content: str) -> DATProfile:
    """Load a DAT profile from YAML string."""
    data = yaml.safe_load(yaml_content)
    return _parse_profile(data)


def _parse_profile(data: dict) -> DATProfile:
    """Parse profile data dictionary into DATProfile object."""
    meta = data.get("meta", {})
    datasource = data.get("datasource", {})
    population = data.get("population", {})
    normalization = data.get("normalization", {})
    outputs = data.get("outputs", {})

    # Parse context defaults
    context_defaults = None
    if "context_defaults" in data:
        cd = data["context_defaults"]
        patterns = []
        for p in cd.get("regex_patterns", []):
            patterns.append(RegexPattern(
                field=p.get("field", ""),
                pattern=p.get("pattern", ""),
                scope=p.get("scope", "filename"),
                required=p.get("required", False),
                description=p.get("description", ""),
                example=p.get("example", ""),
            ))
        context_defaults = ContextDefaults(
            defaults=cd.get("defaults", {}),
            regex_patterns=patterns,
        )

    # Parse contexts
    contexts = []
    for ctx in data.get("contexts", []):
        contexts.append(ContextConfig(
            name=ctx.get("name", ""),
            level=ctx.get("level", ""),
            paths=ctx.get("paths", []),
            key_map=ctx.get("key_map", {}),
            primary_keys=ctx.get("primary_keys", []),
            time_fields=ctx.get("time_fields"),
        ))

    # Parse levels and tables
    levels = []
    for level_data in data.get("levels", []):
        tables = []
        for table_data in level_data.get("tables", []):
            select_data = table_data.get("select", {})
            select = TableSelect(
                strategy=select_data.get("strategy", "flat_object"),
                path=select_data.get("path", "$"),
                headers_key=select_data.get("headers_key"),
                data_key=select_data.get("data_key"),
                repeat_over=select_data.get("repeat_over"),
            )
            tables.append(TableConfig(
                id=table_data.get("id", ""),
                label=table_data.get("label", ""),
                description=table_data.get("description", ""),
                select=select,
                stable_columns=table_data.get("stable_columns", []),
                stable_columns_mode=table_data.get("stable_columns_mode", "warn"),
                stable_columns_subset=table_data.get("stable_columns_subset", True),
            ))

        levels.append(LevelConfig(
            name=level_data.get("name", ""),
            apply_context=level_data.get("apply_context", ""),
            tables=tables,
        ))

    # Parse outputs
    default_outputs = []
    for out in outputs.get("defaults", []):
        default_outputs.append(OutputConfig(
            id=out.get("id", ""),
            from_level=out.get("from_level", ""),
            from_tables=out.get("from_tables", []),
            include_context=out.get("include_context", True),
        ))

    optional_outputs = []
    for out in outputs.get("long_form_optional", []):
        optional_outputs.append(OutputConfig(
            id=out.get("id", ""),
            from_level=out.get("from_level", ""),
            from_tables=out.get("from_tables", []),
            include_context=out.get("include_context", True),
        ))

    return DATProfile(
        schema_version=data.get("schema_version", "1.0.0"),
        version=data.get("version", 1),
        profile_id=meta.get("profile_id", ""),
        title=meta.get("title", ""),
        description=meta.get("description", ""),
        created_by=meta.get("created_by", ""),
        created_at=_parse_datetime(meta.get("created_at")),
        modified_at=_parse_datetime(meta.get("modified_at")),
        revision=meta.get("revision", 1),
        hash=meta.get("hash", ""),
        datasource_id=datasource.get("id", ""),
        datasource_label=datasource.get("label", ""),
        datasource_format=datasource.get("format", "json"),
        datasource_filters=datasource.get("filters", {}),
        datasource_options=datasource.get("options", {}),
        default_strategy=population.get("default_strategy", "all"),
        include_populations=population.get("include_populations", []),
        context_defaults=context_defaults,
        contexts=contexts,
        levels=levels,
        nan_values=normalization.get("nan_values", []),
        units_policy=normalization.get("units_policy", "preserve"),
        numeric_coercion=normalization.get("numeric_coercion", True),
        default_outputs=default_outputs,
        optional_outputs=optional_outputs,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse datetime string to datetime object."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def get_builtin_profiles() -> dict[str, Path]:
    """Get dictionary of built-in profile IDs to file paths."""
    profiles_dir = Path(__file__).parent
    profiles = {}

    for yaml_file in profiles_dir.glob("*.yaml"):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            profile_id = data.get("meta", {}).get("profile_id")
            if profile_id:
                profiles[profile_id] = yaml_file
        except Exception:
            continue

    return profiles


def get_profile_by_id(profile_id: str) -> DATProfile | None:
    """Load a built-in profile by its ID."""
    profiles = get_builtin_profiles()
    if profile_id in profiles:
        return load_profile(profiles[profile_id])
    return None


def validate_profile(
    profile: DATProfile,
    source_columns: list[str] | None = None,
    source_files: list[Path] | None = None,
) -> ProfileValidationResult:
    """Validate a profile against schema and optionally source data.

    Per ADR-0011: Profiles are validated before use to ensure consistency.

    Args:
        profile: DATProfile to validate.
        source_columns: Optional list of actual source column names for matching.
        source_files: Optional list of source files to match against patterns.

    Returns:
        ProfileValidationResult with validation status and details.
    """
    errors: list[str] = []
    warnings: list[str] = []
    matched_files = 0
    matched_columns = 0
    unmapped_columns: list[str] = []

    # Validate required profile fields
    if not profile.profile_id:
        errors.append("Profile must have a profile_id")

    if not profile.title:
        errors.append("Profile must have a title")

    # Validate levels and tables
    if not profile.levels:
        warnings.append("Profile has no levels defined")
    else:
        for level in profile.levels:
            if not level.tables:
                warnings.append(f"Level '{level.name}' has no tables defined")
            for table in level.tables:
                if not table.id:
                    errors.append(f"Table in level '{level.name}' has no id")
                if table.select and not table.select.path:
                    errors.append(
                        f"Table '{table.id}' in level '{level.name}' has no select path"
                    )

    # Validate context defaults
    if profile.context_defaults:
        for pattern in profile.context_defaults.regex_patterns:
            if pattern.required and not pattern.pattern:
                errors.append(
                    f"Required regex pattern '{pattern.field}' has no pattern defined"
                )
            # Validate regex compiles
            if pattern.pattern:
                try:
                    re.compile(pattern.pattern)
                except re.error as e:
                    errors.append(
                        f"Invalid regex pattern for '{pattern.field}': {e}"
                    )

    # Validate contexts
    for ctx in profile.contexts:
        if not ctx.name:
            errors.append("Context configuration has no name")
        if not ctx.level:
            warnings.append(f"Context '{ctx.name}' has no level specified")

    # Validate outputs
    if not profile.default_outputs and not profile.optional_outputs:
        warnings.append("Profile has no outputs defined")

    for output in profile.default_outputs:
        if not output.from_level:
            errors.append(f"Output '{output.id}' has no from_level specified")
        # Check that from_level exists
        level_names = [level.name for level in profile.levels]
        if output.from_level and output.from_level not in level_names:
            errors.append(
                f"Output '{output.id}' references unknown level '{output.from_level}'"
            )

    # Validate against source files if provided
    if source_files:
        for file_path in source_files:
            # Check if filename matches any context extraction pattern
            extracted = profile.extract_context_from_filename(file_path.name)
            if extracted:
                matched_files += 1

    # Validate against source columns if provided
    if source_columns:
        # Check for columns that might not be mapped
        # This is a basic check - full mapping validation would need column mappings
        for col in source_columns:
            # Check if column appears in any context key_map
            is_mapped = False
            for ctx in profile.contexts:
                if col in ctx.key_map.values():
                    is_mapped = True
                    matched_columns += 1
                    break
            if not is_mapped:
                unmapped_columns.append(col)

    return ProfileValidationResult(
        profile_id=profile.profile_id,
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        matched_files=matched_files,
        matched_columns=matched_columns,
        unmapped_columns=unmapped_columns,
    )
