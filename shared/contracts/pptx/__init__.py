"""PPTX (PowerPoint Generator) contracts.

This package contains Pydantic models for PPTX-specific data structures:
- Template contracts for slide deck templates and configuration
- Shape contracts for shape discovery and placeholder mapping
- Workflow contracts for guided workflow FSM (ADR-0019)
- Domain contracts for domain-specific configuration (ADR-0020)
- Renderer contracts for the rendering pipeline (ADR-0021)

All contracts are domain-agnostic; user-specific knowledge (template paths,
placeholder names, data bindings) is injected via configs.
"""

from shared.contracts.pptx.template import (
    PPTXTemplate,
    PPTXTemplateRef,
    SlideTemplate,
    SlideLayout,
    TemplateValidationResult,
    RenderConfig,
    RenderRequest,
    RenderResult,
)
from shared.contracts.pptx.shape import (
    ShapeType,
    ShapeDiscoveryResult,
    ShapePlaceholder,
    ShapeBinding,
    DataBindingType,
    ChartConfig,
    TableConfig,
    TextConfig,
    ImageConfig,
)
from shared.contracts.pptx.workflow import (
    PPTXStageId,
    PPTXStageState,
    ValidationBarStatus,
    PPTXStageConfig,
    PPTXStageGraphConfig,
    PPTXStageStatus,
    ValidationResult,
    PPTXWorkflowState,
    PPTXProject,
    PPTXProjectRef,
    CreateProjectRequest,
    UpdateProjectRequest,
    StageTransitionRequest,
    StageTransitionResult,
)
from shared.contracts.pptx.domain import (
    MetricCategory,
    MetricAggregation,
    MetricFormat,
    CanonicalMetric,
    MetricRegistry,
    ContextDimensionType,
    ContextDimension,
    JobContext,
    ChartType,
    RenderingRule,
    DomainConfig,
    DomainConfigRef,
    DomainConfigValidationResult,
)
from shared.contracts.pptx.renderer import (
    RendererCategory,
    RenderStatus,
    TextRenderConfig,
    ChartRenderConfig,
    TableRenderConfig,
    ImageRenderConfig,
    MetricRenderConfig,
    ShapeRenderContext,
    RenderInput,
    ShapeRenderResult,
    RendererResult,
    RendererMetadata,
    RendererRegistryEntry,
    RendererRegistryState,
    BaseRenderer,
)

__all__ = [
    # Template contracts
    "PPTXTemplate",
    "PPTXTemplateRef",
    "SlideTemplate",
    "SlideLayout",
    "TemplateValidationResult",
    "RenderConfig",
    "RenderRequest",
    "RenderResult",
    # Shape contracts
    "ShapeType",
    "ShapeDiscoveryResult",
    "ShapePlaceholder",
    "ShapeBinding",
    "DataBindingType",
    "ChartConfig",
    "TableConfig",
    "TextConfig",
    "ImageConfig",
    # Workflow contracts (ADR-0019)
    "PPTXStageId",
    "PPTXStageState",
    "ValidationBarStatus",
    "PPTXStageConfig",
    "PPTXStageGraphConfig",
    "PPTXStageStatus",
    "ValidationResult",
    "PPTXWorkflowState",
    "PPTXProject",
    "PPTXProjectRef",
    "CreateProjectRequest",
    "UpdateProjectRequest",
    "StageTransitionRequest",
    "StageTransitionResult",
    # Domain contracts (ADR-0020)
    "MetricCategory",
    "MetricAggregation",
    "MetricFormat",
    "CanonicalMetric",
    "MetricRegistry",
    "ContextDimensionType",
    "ContextDimension",
    "JobContext",
    "ChartType",
    "RenderingRule",
    "DomainConfig",
    "DomainConfigRef",
    "DomainConfigValidationResult",
    # Renderer contracts (ADR-0021)
    "RendererCategory",
    "RenderStatus",
    "TextRenderConfig",
    "ChartRenderConfig",
    "TableRenderConfig",
    "ImageRenderConfig",
    "MetricRenderConfig",
    "ShapeRenderContext",
    "RenderInput",
    "ShapeRenderResult",
    "RendererResult",
    "RendererMetadata",
    "RendererRegistryEntry",
    "RendererRegistryState",
    "BaseRenderer",
]
