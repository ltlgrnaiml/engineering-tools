"""Domain Configuration Models.

Pydantic models representing the full domain_config.yaml structure.
All config sections are typed and validated.
"""

from typing import Any

from pydantic import BaseModel, Field


class JobDescription(BaseModel):
    """Job description metadata."""

    name: str = Field(..., description="Report name")
    version: str = Field(..., description="Config version")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Log level")
    folder: str = Field(default="logs", description="Log folder path")


class JobContext(BaseModel):
    """Job context dimension configuration.

    Represents a categorical dimension used for filtering and slide duplication.
    Examples: Sides (Left/Right), Wafer (W1/W2/W3), CD Target (40nm/45nm).
    """

    name: str = Field(..., description="Display name for UI")
    key: str = Field(..., description="Machine key for data column")
    values: list[str] = Field(..., description="Valid canonical values")
    aliases: dict[str, str] = Field(
        default_factory=dict, description="Aliases mapping to canonical values"
    )

    def resolve_value(self, value: str) -> str | None:
        """Resolve a value through aliases to canonical form.

        Args:
            value: Value to resolve (may be alias or canonical).

        Returns:
            Canonical value if found, None otherwise.
        """
        if value in self.values:
            return value
        return self.aliases.get(value)


class Repository(BaseModel):
    """Data repository configuration."""

    kind: str = Field(..., description="Repository type (fs, adls, sql)")
    root: str = Field(..., description="Root path or connection string")


class FilePattern(BaseModel):
    """File pattern configuration for data discovery."""

    id: str = Field(..., description="Unique file identifier")
    title: str = Field(..., description="Human-readable title")
    repo: str = Field(..., description="Repository reference")
    patterns: list[str] = Field(..., description="Glob patterns for file matching")
    required_columns: list[str] = Field(default_factory=list)
    variants: list[str] = Field(default_factory=list)


class EnvProfileRoots(BaseModel):
    """Environment profile root paths."""

    templates_root: str = Field(..., description="Templates directory")
    output_root: str = Field(..., description="Output directory")
    dataagg_rel: str = Field(
        default="{run_key}/DataAgg/{category}",
        description="Relative data aggregation path pattern",
    )


class EnvProfileConfig(BaseModel):
    """Environment profile configuration."""

    source: str = Field(..., description="Data source type")
    roots: EnvProfileRoots = Field(..., description="Root paths")
    encoding_policy: list[str] = Field(
        default_factory=lambda: ["utf-8", "utf-8-sig", "cp1252"]
    )


class TemplateGeometry(BaseModel):
    """Template geometry configuration."""

    source: str = Field(default="slideset")


class TemplateSlideConfig(BaseModel):
    """Template slide configuration."""

    slide_titles: list[str] = Field(default_factory=list)
    output_layout: dict[str, Any] = Field(default_factory=dict)


class TemplateConfig(BaseModel):
    """Template configuration."""

    file: str = Field(..., description="Template filename")
    keep_geometry_slide: bool = Field(default=False)
    geometry: TemplateGeometry = Field(default_factory=TemplateGeometry)
    job_slides: TemplateSlideConfig = Field(default_factory=TemplateSlideConfig)
    run_slides: TemplateSlideConfig = Field(default_factory=TemplateSlideConfig)


class MetricsConfig(BaseModel):
    """Metrics configuration."""

    canonical: list[str] = Field(default_factory=list, description="Canonical metric names")
    rename_map: dict[str, str] = Field(default_factory=dict, description="Column rename mappings")


class DataConfig(BaseModel):
    """Data processing configuration."""

    global_where: dict[str, Any] = Field(default_factory=dict)
    enforce_singleton: dict[str, Any] = Field(default_factory=dict)


class ShapeNamingConfig(BaseModel):
    """Shape naming configuration (ARL v2)."""

    version: str = Field(default="2", description="ARL version")
    format: str = Field(
        default="<renderer>:<data>[@<filter>][|<options>]",
        description="Shape name format specification",
    )
    allowed_renderers: dict[str, list[str]] = Field(default_factory=dict)
    filter_shorthands: dict[str, str] = Field(default_factory=dict)
    option_keys: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class ContextConfig(BaseModel):
    """Context extraction configuration."""

    image_name_regex: str = Field(default="")
    required_columns: list[str] = Field(default_factory=list)
    rename_map: dict[str, str] = Field(default_factory=dict)


class OutputsConfig(BaseModel):
    """Output file configuration."""

    folder: str = Field(default="artifacts")
    ppt_output_template: str = Field(default="{run_key}_{job_name}_{timestamp}.pptx")
    boxplot_png_template: str = Field(default="{run_key}_boxplot_{metric}.png")
    boxplot_html_template: str = Field(default="{run_key}_boxplot_{metric}.html")


class DeterminismConfig(BaseModel):
    """Determinism and reproducibility configuration."""

    enable: bool = Field(default=True)
    rng_seed: int = Field(default=42)
    spec_sort_keys: list[str] = Field(
        default_factory=lambda: ["slideIndex", "top", "left", "name"]
    )
    filename_canonicalization: bool = Field(default=True)
    record_hashes: bool = Field(default=True)
    record_code_version: bool = Field(default=True)


class PlottingConfig(BaseModel):
    """Plotting configuration."""

    job_context_colors: dict[str, str] = Field(default_factory=dict)
    use_fixed_y_ranges: bool = Field(default=False)
    fixed_y_ranges: dict[str, list[float]] = Field(default_factory=dict)
    reverse_left_axis: bool = Field(default=True)
    left_contour_lines: bool = Field(default=True)
    reverse_right_axis: bool = Field(default=False)
    right_contour_lines: bool = Field(default=True)
    colormap: str = Field(default="viridis")
    figure_dpi: int = Field(default=150)


class TableGridConfig(BaseModel):
    """Table grid line configuration."""

    header_line_pt: float = Field(default=1.5)
    body_line_pt: float = Field(default=0.5)


class TableDefaults(BaseModel):
    """Table renderer defaults."""

    font_size: int = Field(default=8)
    width_in: float = Field(default=9.4)
    height_in: float = Field(default=2.6)
    top_in: float = Field(default=0.6)
    first_col_w_in: float = Field(default=1.2)
    second_col_w_in: float = Field(default=1.4)
    header_fill_rgb: list[int] = Field(default_factory=lambda: [230, 230, 230])
    header_font_rgb: list[int] = Field(default_factory=lambda: [0, 0, 0])
    subheader_fill_rgb: list[int] = Field(default_factory=lambda: [242, 242, 242])
    body_font_rgb: list[int] = Field(default_factory=lambda: [0, 0, 0])
    metric_band_rgb: list[int] = Field(default_factory=lambda: [191, 191, 191])
    row_stripe_rgb: list[int] = Field(default_factory=lambda: [242, 242, 242])
    grid: TableGridConfig = Field(default_factory=TableGridConfig)
    link_rgb: list[int] = Field(default_factory=lambda: [0, 144, 218])


class KPIDefaults(BaseModel):
    """KPI renderer defaults."""

    font_size: int = Field(default=24)
    decimal_places: int = Field(default=2)
    show_unit: bool = Field(default=True)


class TextDefaults(BaseModel):
    """Text renderer defaults."""

    font_size: int = Field(default=12)
    font_family: str = Field(default="Arial")


class DefaultsConfig(BaseModel):
    """Renderer defaults configuration."""

    tables: TableDefaults = Field(default_factory=TableDefaults)
    kpi: KPIDefaults = Field(default_factory=KPIDefaults)
    text: TextDefaults = Field(default_factory=TextDefaults)


class UIGatesConfig(BaseModel):
    """UI validation gates configuration."""

    preflight_pass_rate_threshold: float = Field(default=0.95)
    require_all_metrics_mapped: bool = Field(default=True)
    require_all_contexts_mapped: bool = Field(default=True)


class LookupArchiveConfig(BaseModel):
    """Lookup archive configuration."""

    dir: str = Field(default="archives")
    naming: str = Field(default="lookup_{job_name}_{yyyymmdd}_{template_hash}.json")


class CLIConfig(BaseModel):
    """CLI automation configuration."""

    allow_preflight_lite: bool = Field(default=True)
    fail_on_out_of_policy_job_context: bool = Field(default=True)


class AutomationConfig(BaseModel):
    """Automation configuration."""

    lookup_archive: LookupArchiveConfig = Field(default_factory=LookupArchiveConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)


class PostprocessConfig(BaseModel):
    """Postprocessing configuration."""

    embed_html_as_ole: bool = Field(default=True)
    strip_image_links: bool = Field(default=True)
    ole_visible: bool = Field(default=False)
    replace_text_links: bool = Field(default=True)
    convert_images_too: bool = Field(default=True)
    overlay_pictures_as_transparent_ole: bool = Field(default=True)


class TestDefaultsContextMapping(BaseModel):
    """Test defaults context mapping."""

    context_name: str
    source_type: str
    source_column: str | None = None
    regex_pattern: str | None = None
    default_value: str | None = None
    description: str = ""


class TestDefaultsMetricMapping(BaseModel):
    """Test defaults metric mapping."""

    metric_name: str
    source_column: str
    rename_to: str | None = None
    aggregation_semantics: str
    data_type: str = "float"
    unit: str | None = None
    description: str = ""


class TestDefaultsRunMetadata(BaseModel):
    """Test defaults run metadata."""

    run_key: str = ""
    project_name: str = ""
    date: str = ""
    author: str = ""


class TestDefaultsConfig(BaseModel):
    """Test defaults for quick testing (backward compatibility)."""

    project_name: str = Field(default="Test Project")
    template_file: str | None = Field(None)
    data_file: str | None = Field(None)
    context_mappings: list[TestDefaultsContextMapping] = Field(default_factory=list)
    metrics_mappings: list[TestDefaultsMetricMapping] = Field(default_factory=list)
    run_metadata: TestDefaultsRunMetadata = Field(default_factory=TestDefaultsRunMetadata)


class DomainConfig(BaseModel):
    """Complete domain configuration model.

    Represents the entire config/example_config_production.yaml structure.
    """

    job_description: JobDescription = Field(...)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    job_contexts: list[JobContext] = Field(default_factory=list)
    primary_job_context: str = Field(default="side")
    repositories: dict[str, Repository] = Field(default_factory=dict)
    files: list[FilePattern] = Field(default_factory=list)
    env_profile: EnvProfileConfig | None = Field(None)
    template: TemplateConfig | None = Field(None)
    metrics: MetricsConfig = Field(default_factory=MetricsConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    shape_naming: ShapeNamingConfig = Field(default_factory=ShapeNamingConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)
    determinism: DeterminismConfig = Field(default_factory=DeterminismConfig)
    plotting: PlottingConfig = Field(default_factory=PlottingConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    ui_gates: UIGatesConfig = Field(default_factory=UIGatesConfig)
    automation: AutomationConfig = Field(default_factory=AutomationConfig)
    postprocess: PostprocessConfig = Field(default_factory=PostprocessConfig)
    test_defaults: TestDefaultsConfig = Field(default_factory=TestDefaultsConfig)

    def get_job_context(self, key: str) -> JobContext | None:
        """Get a job context by its key."""
        for ctx in self.job_contexts:
            if ctx.key == key:
                return ctx
        return None

    def get_primary_job_context(self) -> JobContext | None:
        """Get the primary job context."""
        return self.get_job_context(self.primary_job_context)

    def get_filter_shorthands(self) -> dict[str, dict[str, str]]:
        """Get filter shorthands expanded to key-value dicts.

        Returns:
            Dict mapping shorthand to {key: value} dict.
            Example: {"left": {"side": "left"}}
        """
        result = {}
        for shorthand, expansion in self.shape_naming.filter_shorthands.items():
            if "=" in expansion:
                key, value = expansion.split("=", 1)
                result[shorthand] = {key: value}
            else:
                result[shorthand] = {"value": expansion}
        return result

    def get_all_renderers(self) -> list[str]:
        """Get all allowed renderer types."""
        renderers = []
        for category_renderers in self.shape_naming.allowed_renderers.values():
            renderers.extend(category_renderers)
        return renderers
