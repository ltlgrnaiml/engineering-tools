"""PPTX (PowerPoint Generator) contracts.

This package contains Pydantic models for PPTX-specific data structures:
- Template contracts for slide deck templates and configuration
- Shape contracts for shape discovery and placeholder mapping
- Workflow contracts for guided workflow FSM (ADR-0020)
- Domain contracts for domain-specific configuration (ADR-0021)
- Renderer contracts for the rendering pipeline (ADR-0022)

All contracts are domain-agnostic; user-specific knowledge (template paths,
placeholder names, data bindings) is injected via configs.
"""

from shared.contracts.pptx.domain import (
    CanonicalMetric,
    ChartType,
    ContextDimension,
    ContextDimensionType,
    DomainConfig,
    DomainConfigRef,
    DomainConfigValidationResult,
    JobContext,
    MetricAggregation,
    MetricCategory,
    MetricFormat,
    MetricRegistry,
    RenderingRule,
)
from shared.contracts.pptx.renderer import (
    BaseRenderer,
    ChartRenderConfig,
    ImageRenderConfig,
    MetricRenderConfig,
    RendererCategory,
    RendererMetadata,
    RendererRegistryEntry,
    RendererRegistryState,
    RendererResult,
    RenderInput,
    RenderStatus,
    ShapeRenderContext,
    ShapeRenderResult,
    TableRenderConfig,
    TextRenderConfig,
)
from shared.contracts.pptx.shape import (
    ChartConfig,
    DataBindingType,
    ImageConfig,
    ShapeBinding,
    ShapeDiscoveryResult,
    ShapePlaceholder,
    ShapeType,
    TableConfig,
    TextConfig,
)
from shared.contracts.pptx.template import (
    PPTXTemplate,
    PPTXTemplateRef,
    RenderConfig,
    RenderRequest,
    RenderResult,
    SlideLayout,
    SlideTemplate,
    TemplateValidationResult,
)
from shared.contracts.pptx.workflow import (
    CreateProjectRequest,
    PPTXProject,
    PPTXProjectRef,
    PPTXStageConfig,
    PPTXStageGraphConfig,
    PPTXStageId,
    PPTXStageState,
    PPTXStageStatus,
    PPTXWorkflowState,
    StageTransitionRequest,
    StageTransitionResult,
    UpdateProjectRequest,
    ValidationBarStatus,
    ValidationResult,
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
    # Workflow contracts (ADR-0020)
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
    # Domain contracts (ADR-0021)
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
    # Renderer contracts (ADR-0022)
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
