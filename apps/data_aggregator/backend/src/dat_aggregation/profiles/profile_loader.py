"""Profile loader for DAT extraction profiles.

Per ADR-0011: Profiles are the single source of truth for extraction logic.
Loads YAML profiles and returns Tier-0 Pydantic contracts directly.

This module is the YAML→Pydantic bridge. It parses YAML and constructs
DATProfile (and nested) Pydantic models from shared.contracts.dat.profile.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from shared.contracts.dat.profile import (
    AggregationConfig,
    ContentPattern,
    ContextConfig,
    ContextDefaults,
    DATProfile,
    GovernanceAccessConfig,
    GovernanceAuditConfig,
    GovernanceComplianceConfig,
    GovernanceConfig,
    GovernanceLimitsConfig,
    JoinConfig,
    JoinOutputConfig,
    LevelConfig,
    OnFailBehavior,
    OutputConfig,
    ProfileValidationResult,
    RegexPattern,
    RegexScope,
    RepeatOverConfig,
    SelectConfig,
    StrategyType,
    TableConfig,
    UIConfig,
    UIPreviewConfig,
    UITableSelectionConfig,
)

__version__ = "1.0.0"


def load_profile(path: Path | str) -> DATProfile:
    """Load a DAT profile from YAML file.

    Args:
        path: Path to YAML profile file.

    Returns:
        Parsed DATProfile Pydantic model.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If YAML parsing fails.
        pydantic.ValidationError: If profile data is invalid.
    """
    path = Path(path)
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return _parse_profile(data)


def load_profile_from_string(yaml_content: str) -> DATProfile:
    """Load a DAT profile from YAML string.

    Args:
        yaml_content: YAML content as a string.

    Returns:
        Parsed DATProfile Pydantic model.
    """
    data = yaml.safe_load(yaml_content)
    return _parse_profile(data)


def _parse_profile(data: dict[str, Any]) -> DATProfile:
    """Parse profile data dictionary into DATProfile Pydantic model.

    This function transforms raw YAML dict into strongly-typed Pydantic models.
    All nested structures are converted to their corresponding contract types.

    Args:
        data: Raw profile data from YAML.

    Returns:
        DATProfile instance.
    """
    meta = data.get("meta", {})
    datasource = data.get("datasource", {})
    population = data.get("population", {})
    normalization = data.get("normalization", {})
    outputs = data.get("outputs", {})

    # Parse context defaults
    context_defaults = _parse_context_defaults(data.get("context_defaults"))

    # Parse contexts
    contexts = [_parse_context_config(ctx) for ctx in data.get("contexts", [])]

    # Parse levels and tables
    levels = [_parse_level_config(level_data) for level_data in data.get("levels", [])]

    # Parse outputs
    default_outputs = [
        _parse_output_config(out) for out in outputs.get("defaults", [])
    ]
    optional_outputs = [
        _parse_output_config(out)
        for out in outputs.get("optional_outputs", outputs.get("long_form_optional", []))
    ]

    # Parse aggregations and joins
    aggregations = [
        _parse_aggregation_config(agg) for agg in outputs.get("aggregations", [])
    ]
    joins = [_parse_join_output_config(j) for j in outputs.get("joins", [])]

    # Parse UI config
    ui = _parse_ui_config(data.get("ui"))

    # Parse governance
    governance = _parse_governance_config(data.get("governance"))

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
        owner=meta.get("owner", ""),
        classification=meta.get("classification", "internal"),
        domain=meta.get("domain", ""),
        tags=meta.get("tags", []),
        datasource_id=datasource.get("id", ""),
        datasource_label=datasource.get("label", ""),
        datasource_format=datasource.get("format", "json"),
        datasource_filters=datasource.get("filters", {}),
        datasource_options=datasource.get("options", {}),
        default_strategy=population.get("default_strategy", "all"),
        include_populations=population.get("include_populations", []),
        population_strategies=population.get("strategies", {}),
        context_defaults=context_defaults,
        contexts=contexts,
        levels=levels,
        nan_values=normalization.get("nan_values", []),
        units_policy=normalization.get("units_policy", "preserve"),
        unit_mappings=normalization.get("unit_mappings", {}),
        numeric_coercion=normalization.get("numeric_coercion", True),
        nan_replacement=normalization.get("nan_replacement"),
        numeric_errors=normalization.get("numeric_errors"),
        string_strip=normalization.get("string_strip"),
        string_case=normalization.get("string_case"),
        column_renames=data.get("column_renames", {}),
        calculated_columns=data.get("calculated_columns", []),
        type_coercion=data.get("type_coercion", []),
        row_filters=data.get("row_filters", []),
        default_outputs=default_outputs,
        optional_outputs=optional_outputs,
        aggregations=aggregations,
        joins=joins,
        ui=ui,
        schema_rules=data.get("schema_rules", {}),
        row_rules=data.get("row_rules", []),
        aggregate_rules=data.get("aggregate_rules", []),
        on_validation_fail=data.get("on_validation_fail", "continue"),
        quarantine_table=data.get("quarantine_table", "validation_failures"),
        governance=governance,
        overrides_allow=data.get("overrides", {}).get("allow", {}),
        overrides_deny=data.get("overrides", {}).get("deny", {}),
        overrides_discovery=data.get("overrides", {}).get("discovery", {}),
    )


def _parse_context_defaults(data: dict[str, Any] | None) -> ContextDefaults | None:
    """Parse context_defaults section into Pydantic model."""
    if not data:
        return None

    regex_patterns = []
    for p in data.get("regex_patterns", []):
        scope_str = p.get("scope", "filename")
        scope = (
            RegexScope(scope_str)
            if scope_str in RegexScope._value2member_map_
            else RegexScope.FILENAME
        )
        on_fail_str = p.get("on_fail", "warn")
        on_fail = (
            OnFailBehavior(on_fail_str)
            if on_fail_str in OnFailBehavior._value2member_map_
            else OnFailBehavior.WARN
        )
        regex_patterns.append(
            RegexPattern(
                field=p.get("field", ""),
                pattern=p.get("pattern", ""),
                scope=scope,
                required=p.get("required", False),
                description=p.get("description", ""),
                example=p.get("example", ""),
                transform=p.get("transform"),
                transform_args=p.get("transform_args", {}),
                on_fail=on_fail,
            )
        )

    content_patterns = []
    for p in data.get("content_patterns", []):
        on_fail_str = p.get("on_fail", "warn")
        on_fail = (
            OnFailBehavior(on_fail_str)
            if on_fail_str in OnFailBehavior._value2member_map_
            else OnFailBehavior.WARN
        )
        content_patterns.append(
            ContentPattern(
                field=p.get("field", ""),
                path=p.get("path", ""),
                required=p.get("required", False),
                default=p.get("default"),
                description=p.get("description", ""),
                example=p.get("example", ""),
                on_fail=on_fail,
            )
        )

    return ContextDefaults(
        defaults=data.get("defaults", {}),
        regex_patterns=regex_patterns,
        content_patterns=content_patterns,
        allow_user_override=data.get("allow_user_override", []),
    )


def _parse_context_config(data: dict[str, Any]) -> ContextConfig:
    """Parse a single context configuration."""
    return ContextConfig(
        name=data.get("name", ""),
        level=data.get("level", ""),
        paths=data.get("paths", []),
        key_map=data.get("key_map", {}),
        primary_keys=data.get("primary_keys", []),
        time_fields=data.get("time_fields"),
    )


def _parse_level_config(data: dict[str, Any]) -> LevelConfig:
    """Parse a level configuration with its tables."""
    tables = [_parse_table_config(t) for t in data.get("tables", [])]
    return LevelConfig(
        name=data.get("name", ""),
        apply_context=data.get("apply_context", ""),
        tables=tables,
    )


def _parse_table_config(data: dict[str, Any]) -> TableConfig:
    """Parse a table configuration with its select strategy."""
    select_data = data.get("select", {})
    select = _parse_select_config(select_data)
    return TableConfig(
        id=data.get("id", ""),
        label=data.get("label", ""),
        description=data.get("description", ""),
        select=select,
        stable_columns=data.get("stable_columns", []),
        stable_columns_mode=data.get("stable_columns_mode", "warn"),
        stable_columns_subset=data.get("stable_columns_subset", True),
        validation_constraints=data.get("validation_constraints", []),
        column_transforms=data.get("column_transforms", []),
    )


def _parse_select_config(data: dict[str, Any]) -> SelectConfig:
    """Parse extraction strategy configuration."""
    strategy_str = data.get("strategy", "flat_object")
    strategy = (
        StrategyType(strategy_str)
        if strategy_str in StrategyType._value2member_map_
        else StrategyType.FLAT_OBJECT
    )

    repeat_over = None
    if data.get("repeat_over"):
        ro = data["repeat_over"]
        repeat_over = RepeatOverConfig(
            path=ro.get("path", ""),
            as_var=ro.get("as", ro.get("as_var", "")),
            inject_fields=ro.get("inject_fields", {}),
        )

    left = None
    if data.get("left"):
        left = JoinConfig(path=data["left"].get("path", ""), key=data["left"].get("key", ""))

    right = None
    if data.get("right"):
        right = JoinConfig(path=data["right"].get("path", ""), key=data["right"].get("key", ""))

    from shared.contracts.dat.profile import JoinHow
    how_str = data.get("how", "left")
    how = JoinHow(how_str) if how_str in JoinHow._value2member_map_ else JoinHow.LEFT

    return SelectConfig(
        strategy=strategy,
        path=data.get("path", "$"),
        headers_key=data.get("headers_key"),
        data_key=data.get("data_key"),
        repeat_over=repeat_over,
        fields=data.get("fields"),
        flatten_nested=data.get("flatten_nested", False),
        flatten_separator=data.get("flatten_separator", "_"),
        infer_headers=data.get("infer_headers", False),
        default_headers=data.get("default_headers"),
        id_vars=data.get("id_vars"),
        value_vars=data.get("value_vars"),
        var_name=data.get("var_name", "variable"),
        value_name=data.get("value_name", "value"),
        left=left,
        right=right,
        how=how,
    )


def _parse_output_config(data: dict[str, Any]) -> OutputConfig:
    """Parse output configuration."""
    return OutputConfig(
        id=data.get("id", ""),
        from_level=data.get("from_level", ""),
        from_tables=data.get("from_tables", []),
        include_context=data.get("include_context", True),
        format=data.get("format", "parquet"),
    )


def _parse_aggregation_config(data: dict[str, Any]) -> AggregationConfig:
    """Parse aggregation configuration."""
    return AggregationConfig(
        id=data.get("id", ""),
        from_table=data.get("from_table", ""),
        group_by=data.get("group_by", []),
        aggregations=data.get("aggregations", {}),
        output_table=data.get("output_table", ""),
    )


def _parse_join_output_config(data: dict[str, Any]) -> JoinOutputConfig:
    """Parse join output configuration."""
    from shared.contracts.dat.profile import JoinHow
    how_str = data.get("how", "left")
    how = JoinHow(how_str) if how_str in JoinHow._value2member_map_ else JoinHow.LEFT
    return JoinOutputConfig(
        id=data.get("id", ""),
        left_table=data.get("left_table", ""),
        right_table=data.get("right_table", ""),
        on=data.get("on", []),
        how=how,
    )


def _parse_ui_config(data: dict[str, Any] | None) -> UIConfig | None:
    """Parse UI configuration hints."""
    if not data:
        return None

    table_selection = None
    if data.get("table_selection"):
        ts = data["table_selection"]
        table_selection = UITableSelectionConfig(
            group_by_level=ts.get("group_by_level", True),
            default_selected=ts.get("default_selected", {}),
            collapsed_by_default=ts.get("collapsed_by_default", []),
        )

    preview = None
    if data.get("preview"):
        pv = data["preview"]
        preview = UIPreviewConfig(
            max_rows=pv.get("max_rows", 100),
            max_columns=pv.get("max_columns", 50),
            column_width=pv.get("column_width", "auto"),
            number_format=pv.get("number_format", "0.0000"),
            date_format=pv.get("date_format", "YYYY-MM-DD HH:mm:ss"),
            null_display=pv.get("null_display", "—"),
        )

    return UIConfig(
        show_file_preview=data.get("show_file_preview", True),
        max_preview_files=data.get("max_preview_files", 10),
        highlight_matching=data.get("highlight_matching", True),
        table_selection=table_selection,
        preview=preview,
        show_regex_matches=data.get("show_regex_matches", True),
        editable_fields=data.get("editable_fields", []),
        readonly_fields=data.get("readonly_fields", []),
        default_name_template=data.get("default_name_template", "{profile_title} - {lot_id}"),
        show_row_count=data.get("show_row_count", True),
        show_column_list=data.get("show_column_list", True),
        allow_format_selection=data.get("allow_format_selection", True),
        formats=data.get("formats", ["parquet", "csv", "excel"]),
    )


def _parse_governance_config(data: dict[str, Any] | None) -> GovernanceConfig | None:
    """Parse governance configuration."""
    if not data:
        return None

    access = None
    if data.get("access"):
        a = data["access"]
        access = GovernanceAccessConfig(
            read=a.get("read", ["all"]),
            modify=a.get("modify", ["admin"]),
            delete=a.get("delete", ["admin"]),
        )

    audit = None
    if data.get("audit"):
        au = data["audit"]
        audit = GovernanceAuditConfig(
            log_access=au.get("log_access", True),
            log_modifications=au.get("log_modifications", True),
            retention_days=au.get("retention_days", 365),
        )

    compliance = None
    if data.get("compliance"):
        c = data["compliance"]
        compliance = GovernanceComplianceConfig(
            data_classification=c.get("data_classification", "internal"),
            pii_columns=c.get("pii_columns", []),
            mask_in_preview=c.get("mask_in_preview", []),
        )

    limits = None
    if data.get("limits"):
        lm = data["limits"]
        limits = GovernanceLimitsConfig(
            max_files_per_run=lm.get("max_files_per_run", 1000),
            max_file_size_mb=lm.get("max_file_size_mb", 500),
            max_total_size_gb=lm.get("max_total_size_gb", 10),
            max_rows_output=lm.get("max_rows_output", 10_000_000),
            max_tables_per_level=lm.get("max_tables_per_level", 50),
            max_columns_per_table=lm.get("max_columns_per_table", 500),
            parse_timeout_seconds=lm.get("parse_timeout_seconds", 3600),
            preview_timeout_seconds=lm.get("preview_timeout_seconds", 30),
        )

    return GovernanceConfig(
        access=access,
        audit=audit,
        compliance=compliance,
        limits=limits,
    )


def _parse_datetime(value: str | None) -> datetime | None:
    """Parse ISO-8601 datetime string to datetime object."""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def get_builtin_profiles() -> dict[str, Path]:
    """Get dictionary of built-in profile IDs to file paths.

    Returns:
        Mapping of profile_id to Path for all YAML profiles in this directory.
    """
    profiles_dir = Path(__file__).parent
    profiles: dict[str, Path] = {}

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
    """Load a built-in profile by its ID.

    Args:
        profile_id: The profile_id to look up.

    Returns:
        DATProfile if found, None otherwise.
    """
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
                if not table.select.path:
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
                    errors.append(f"Invalid regex pattern for '{pattern.field}': {e}")

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
        for col in source_columns:
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
