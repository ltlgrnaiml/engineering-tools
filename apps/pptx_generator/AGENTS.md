# PowerPoint Generator Tool (PPTX) - AI Coding Guide

> **Scope**: This AGENTS.md applies when working with files in `apps/pptx_generator/`.

---

## Architecture Overview

PPTX is a **template-driven report generator** with a 7-step workflow:

```
Upload Template → Upload Data → Map Context → Map Metrics → Validate → Generate → Download
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Template** | PPTX file with named shapes as placeholders |
| **Shape Discovery** | Scans template for `{category}_{identifier}` named shapes |
| **Renderer** | Pluggable components that fill shapes with data |
| **Domain Config** | YAML defining metrics, units, and canonicalization |

---

## Key ADRs

| ADR | Topic | Key Points |
|-----|-------|------------|
| **ADR-0019** | Template Processing | Named shape discovery, `{category}_{identifier}` |
| **ADR-0020** | Guided Workflow | 7-step FSM, "Four Green Bars" validation |
| **ADR-0021** | Domain Configuration | YAML config, metric canonicalization |
| **ADR-0022** | Renderer Architecture | Pluggable renderers, BaseRenderer interface |

---

## Contracts Location

**Tier-0 contracts** (SSOT): `shared/contracts/pptx/`

```python
# ✅ CORRECT
from shared.contracts.pptx.template import PPTXTemplate, SlideTemplate
from shared.contracts.pptx.shape import ShapeDiscoveryResult, ShapePlaceholder

# ❌ WRONG
class PPTXTemplate(BaseModel): ...  # NO!
```

---

## Template Shape Naming Convention

Shapes in templates use the pattern: `{category}_{identifier}`

| Category | Example | Renders As |
|----------|---------|------------|
| `text` | `text_title`, `text_summary` | Text content |
| `table` | `table_data`, `table_summary` | Data table |
| `chart` | `chart_trend`, `chart_bar` | Chart/graph |
| `image` | `image_logo`, `image_diagram` | Image |

---

## Workflow Stages (ADR-0020)

```
Step 1: Upload Template    → Template validated, shapes discovered
Step 2: Upload Data        → CSV/Excel/DataSet loaded
Step 3: Map Context        → Context columns mapped to template
Step 4: Map Metrics        → Metric columns mapped to charts/tables
Step 5: Validate           → "Four Green Bars" - all mappings valid
Step 6: Generate           → PPTX rendered with data
Step 7: Download           → User downloads result
```

**Validation Gate**: Generate button disabled until Step 5 passes.

---

## Renderer Interface (ADR-0022)

All renderers implement `BaseRenderer`:

```python
class BaseRenderer(ABC):
    @abstractmethod
    def render(self, shape: Shape, data: Any, config: RenderConfig) -> None:
        """Render data into the shape."""
        ...

    @abstractmethod
    def supports(self, shape_type: str) -> bool:
        """Check if renderer supports this shape type."""
        ...
```

Built-in renderers:

- `TextRenderer` - Text placeholders
- `TableRenderer` - Data tables
- `ChartRenderer` - Charts (bar, line, pie)
- `ImageRenderer` - Images

---

## DataSet Integration

PPTX can load data from:

1. **File Upload** - CSV, Excel direct upload
2. **DataSet API** - Load from `workspace/datasets/` via gateway

```python
# Loading from DataSet
from shared.contracts.core.dataset import DataSetRef

dataset_ref = DataSetRef(id="dataset_abc123")
# Gateway resolves to workspace/datasets/dataset_abc123/
```

---

## Testing

Tests located in `tests/pptx/`:

- `test_renderers/` - Renderer unit tests
- `test_shape_discovery/` - Shape detection tests
- `test_workflow_fsm/` - Workflow state machine tests
