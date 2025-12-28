"""Built-in message catalogs for all tools.

Per ADR-0017#message-catalogs: All user-facing messages MUST be defined
in catalogs, never hardcoded in backend logic.

This module provides pre-defined catalogs for each tool with common messages.
"""

from datetime import datetime, timezone

from .catalog import (
    MessageCatalog,
    MessageCategory,
    MessageDefinition,
    MessageSeverity,
)

__version__ = "0.1.0"


def _create_core_catalog() -> MessageCatalog:
    """Create the core platform message catalog."""
    catalog = MessageCatalog(
        catalog_id="core",
        name="Core Platform Messages",
        description="Common messages used across all tools",
        domain="platform",
        created_at=datetime.now(timezone.utc),
    )

    messages = [
        MessageDefinition(
            message_id="CORE_NOT_FOUND",
            message="{resource_type} not found: {resource_id}",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.ERROR,
            placeholders=["resource_type", "resource_id"],
        ),
        MessageDefinition(
            message_id="CORE_VALIDATION_FAILED",
            message="Validation failed: {error_count} error(s)",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.VALIDATION,
            placeholders=["error_count"],
        ),
        MessageDefinition(
            message_id="CORE_OPERATION_CANCELLED",
            message="Operation cancelled by user",
            severity=MessageSeverity.WARNING,
            category=MessageCategory.SYSTEM,
        ),
        MessageDefinition(
            message_id="CORE_INTERNAL_ERROR",
            message="An internal error occurred. Please try again or contact support.",
            severity=MessageSeverity.CRITICAL,
            category=MessageCategory.ERROR,
            error_code="INTERNAL_ERROR",
        ),
        MessageDefinition(
            message_id="CORE_RATE_LIMITED",
            message="Rate limit exceeded. Please wait {wait_seconds} seconds.",
            severity=MessageSeverity.WARNING,
            category=MessageCategory.SYSTEM,
            placeholders=["wait_seconds"],
        ),
    ]

    for msg in messages:
        catalog.add_message(msg)

    return catalog


def _create_dat_catalog() -> MessageCatalog:
    """Create the DAT tool message catalog."""
    catalog = MessageCatalog(
        catalog_id="dat",
        name="Data Aggregator Messages",
        description="Messages for the Data Aggregator tool",
        domain="dat",
        created_at=datetime.now(timezone.utc),
    )

    messages = [
        MessageDefinition(
            message_id="DAT_PARSE_START",
            message="Starting parse of {file_count} file(s)",
            severity=MessageSeverity.INFO,
            category=MessageCategory.PROGRESS,
            placeholders=["file_count"],
        ),
        MessageDefinition(
            message_id="DAT_PARSE_PROGRESS",
            message="Processing {current_file} ({progress_pct:.0f}%)",
            severity=MessageSeverity.INFO,
            category=MessageCategory.PROGRESS,
            placeholders=["current_file", "progress_pct"],
        ),
        MessageDefinition(
            message_id="DAT_PARSE_COMPLETE",
            message="Parse complete: {row_count} rows from {file_count} file(s)",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.RESULT,
            placeholders=["row_count", "file_count"],
        ),
        MessageDefinition(
            message_id="DAT_PARSE_CANCELLED",
            message="Parse cancelled. {completed_files} of {total_files} files completed.",
            severity=MessageSeverity.WARNING,
            category=MessageCategory.SYSTEM,
            placeholders=["completed_files", "total_files"],
        ),
        MessageDefinition(
            message_id="DAT_PROFILE_NOT_FOUND",
            message="Extraction profile not found: {profile_id}",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.ERROR,
            error_code="PROFILE_NOT_FOUND",
            placeholders=["profile_id"],
        ),
        MessageDefinition(
            message_id="DAT_CONTEXT_FALLBACK",
            message="Using profile defaults: context.json not found",
            severity=MessageSeverity.INFO,
            category=MessageCategory.SYSTEM,
        ),
        MessageDefinition(
            message_id="DAT_EXPORT_COMPLETE",
            message="Export complete: {output_path}",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.RESULT,
            placeholders=["output_path"],
        ),
    ]

    for msg in messages:
        catalog.add_message(msg)

    return catalog


def _create_sov_catalog() -> MessageCatalog:
    """Create the SOV tool message catalog."""
    catalog = MessageCatalog(
        catalog_id="sov",
        name="SOV Analyzer Messages",
        description="Messages for the SOV Analyzer tool",
        domain="sov",
        created_at=datetime.now(timezone.utc),
    )

    messages = [
        MessageDefinition(
            message_id="SOV_ANALYSIS_START",
            message="Starting ANOVA analysis with {factor_count} factor(s)",
            severity=MessageSeverity.INFO,
            category=MessageCategory.PROGRESS,
            placeholders=["factor_count"],
        ),
        MessageDefinition(
            message_id="SOV_ANALYSIS_COMPLETE",
            message="ANOVA complete: R² = {r_squared:.2%}",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.RESULT,
            placeholders=["r_squared"],
        ),
        MessageDefinition(
            message_id="SOV_VARIANCE_VALIDATION_FAILED",
            message="Variance percentages sum to {variance_sum:.2f}%, expected 100%",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.VALIDATION,
            error_code="VARIANCE_VALIDATION_FAILED",
            placeholders=["variance_sum"],
        ),
        MessageDefinition(
            message_id="SOV_FACTOR_SIGNIFICANT",
            message="Factor '{factor}' is significant (p={p_value:.4f})",
            severity=MessageSeverity.INFO,
            category=MessageCategory.RESULT,
            placeholders=["factor", "p_value"],
        ),
        MessageDefinition(
            message_id="SOV_DATASET_LOADED",
            message="Loaded dataset: {row_count} rows, {column_count} columns",
            severity=MessageSeverity.INFO,
            category=MessageCategory.PROGRESS,
            placeholders=["row_count", "column_count"],
        ),
    ]

    for msg in messages:
        catalog.add_message(msg)

    return catalog


def _create_pptx_catalog() -> MessageCatalog:
    """Create the PPTX tool message catalog."""
    catalog = MessageCatalog(
        catalog_id="pptx",
        name="PowerPoint Generator Messages",
        description="Messages for the PowerPoint Generator tool",
        domain="pptx",
        created_at=datetime.now(timezone.utc),
    )

    messages = [
        MessageDefinition(
            message_id="PPTX_TEMPLATE_PARSED",
            message="Template parsed: {slide_count} slides, {shape_count} shapes discovered",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.RESULT,
            placeholders=["slide_count", "shape_count"],
        ),
        MessageDefinition(
            message_id="PPTX_SHAPE_INVALID",
            message="Invalid shape name on slide {slide_index}: '{shape_name}'",
            severity=MessageSeverity.WARNING,
            category=MessageCategory.VALIDATION,
            placeholders=["slide_index", "shape_name"],
        ),
        MessageDefinition(
            message_id="PPTX_VALIDATION_PASSED",
            message="Validation passed: all requirements met ('Four Green Bars')",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.VALIDATION,
        ),
        MessageDefinition(
            message_id="PPTX_VALIDATION_BLOCKED",
            message="Cannot validate: {blocking_steps} step(s) incomplete",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.VALIDATION,
            placeholders=["blocking_steps"],
        ),
        MessageDefinition(
            message_id="PPTX_GENERATE_BLOCKED",
            message="Generation blocked: validation required per ADR-0019",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.ERROR,
            error_code="GENERATE_BLOCKED",
        ),
        MessageDefinition(
            message_id="PPTX_GENERATE_START",
            message="Starting presentation generation",
            severity=MessageSeverity.INFO,
            category=MessageCategory.PROGRESS,
        ),
        MessageDefinition(
            message_id="PPTX_GENERATE_COMPLETE",
            message="Presentation generated: {output_filename}",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.RESULT,
            placeholders=["output_filename"],
        ),
        MessageDefinition(
            message_id="PPTX_SHAPE_RENDER_FAILED",
            message="Failed to render shape '{shape_name}': {error}",
            severity=MessageSeverity.WARNING,
            category=MessageCategory.ERROR,
            placeholders=["shape_name", "error"],
        ),
    ]

    for msg in messages:
        catalog.add_message(msg)

    return catalog


def _create_gateway_catalog() -> MessageCatalog:
    """Create the Gateway message catalog."""
    catalog = MessageCatalog(
        catalog_id="gateway",
        name="Gateway Messages",
        description="Messages for the API Gateway",
        domain="gateway",
        created_at=datetime.now(timezone.utc),
    )

    messages = [
        MessageDefinition(
            message_id="GW_PIPELINE_CREATED",
            message="Pipeline '{name}' created with {step_count} step(s)",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.RESULT,
            placeholders=["name", "step_count"],
        ),
        MessageDefinition(
            message_id="GW_PIPELINE_STARTED",
            message="Pipeline execution started: {pipeline_id}",
            severity=MessageSeverity.INFO,
            category=MessageCategory.PROGRESS,
            placeholders=["pipeline_id"],
        ),
        MessageDefinition(
            message_id="GW_PIPELINE_STEP_COMPLETE",
            message="Step {step_index} complete: {step_name}",
            severity=MessageSeverity.INFO,
            category=MessageCategory.PROGRESS,
            placeholders=["step_index", "step_name"],
        ),
        MessageDefinition(
            message_id="GW_PIPELINE_COMPLETE",
            message="Pipeline execution complete",
            severity=MessageSeverity.SUCCESS,
            category=MessageCategory.RESULT,
        ),
        MessageDefinition(
            message_id="GW_PIPELINE_FAILED",
            message="Pipeline failed at step {step_index}: {error}",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.ERROR,
            error_code="PIPELINE_FAILED",
            placeholders=["step_index", "error"],
        ),
        MessageDefinition(
            message_id="GW_TOOL_UNAVAILABLE",
            message="Tool '{tool}' is currently unavailable",
            severity=MessageSeverity.ERROR,
            category=MessageCategory.ERROR,
            error_code="TOOL_UNAVAILABLE",
            placeholders=["tool"],
        ),
    ]

    for msg in messages:
        catalog.add_message(msg)

    return catalog


# Singleton catalog instances
CORE_CATALOG = _create_core_catalog()
DAT_CATALOG = _create_dat_catalog()
SOV_CATALOG = _create_sov_catalog()
PPTX_CATALOG = _create_pptx_catalog()
GATEWAY_CATALOG = _create_gateway_catalog()

# Registry of all catalogs
CATALOGS: dict[str, MessageCatalog] = {
    "core": CORE_CATALOG,
    "dat": DAT_CATALOG,
    "sov": SOV_CATALOG,
    "pptx": PPTX_CATALOG,
    "gateway": GATEWAY_CATALOG,
}


def get_catalog(catalog_id: str) -> MessageCatalog | None:
    """Get a catalog by ID.

    Args:
        catalog_id: Catalog identifier (core, dat, sov, pptx, gateway).

    Returns:
        MessageCatalog or None if not found.
    """
    return CATALOGS.get(catalog_id)


def get_message(catalog_id: str, message_id: str, **kwargs) -> str | None:
    """Get a formatted message from a catalog.

    Args:
        catalog_id: Catalog identifier.
        message_id: Message identifier within catalog.
        **kwargs: Placeholder values.

    Returns:
        Formatted message string or None if not found.
    """
    catalog = get_catalog(catalog_id)
    if catalog is None:
        return None
    return catalog.format_message(message_id, **kwargs)
