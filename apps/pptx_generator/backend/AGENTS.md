# PPTX Backend - AI Coding Guide

> **Scope**: Python/FastAPI backend for PowerPoint Generator tool.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| PPTX Library | python-pptx |
| Validation | Pydantic (from shared.contracts) |
| Charts | python-pptx + custom renderers |

---

## Directory Structure

```text
backend/
├── api/
│   ├── routes.py          # FastAPI route definitions
│   ├── errors.py          # ErrorResponse helpers
│   └── dependencies.py    # Dependency injection
├── services/
│   ├── template_service.py   # Template management
│   ├── shape_service.py      # Shape discovery
│   └── generation_service.py # PPTX generation
└── src/pptx_generator/
    ├── renderers/         # Shape renderers
    ├── discovery/         # Shape discovery engine
    └── templates/         # Template processing
```

---

## Shape Discovery

```python
from pptx import Presentation
from shared.contracts.pptx.shape import ShapeDiscoveryResult

def discover_shapes(template_path: Path) -> ShapeDiscoveryResult:
    """Discover named shapes in template.
    
    Shape names follow pattern: {category}_{identifier}
    Categories: text, table, chart, image
    """
    prs = Presentation(template_path)
    shapes = []
    for slide in prs.slides:
        for shape in slide.shapes:
            if shape.name and "_" in shape.name:
                # Parse category_identifier pattern
                ...
    return ShapeDiscoveryResult(shapes=shapes)
```

---

## Renderer Pattern

```python
from abc import ABC, abstractmethod
from pptx.shapes.base import BaseShape

class BaseRenderer(ABC):
    """Base class for all shape renderers."""

    @abstractmethod
    def render(self, shape: BaseShape, data: Any, config: RenderConfig) -> None:
        """Render data into shape."""
        ...

    @abstractmethod
    def supports(self, shape_type: str) -> bool:
        """Check if renderer supports shape type."""
        ...


class TextRenderer(BaseRenderer):
    """Renders text into text placeholders."""
    
    def supports(self, shape_type: str) -> bool:
        return shape_type == "text"
```

---

## Domain Configuration

Domain config loaded at startup:

```python
# config/domain.yaml
metrics:
  yield:
    unit: "%"
    precision: 2
    aliases: ["Yield", "YIELD", "yield_pct"]
  
  thickness:
    unit: "nm"
    precision: 1
```

---

## Testing

```bash
pytest tests/pptx/ -v
pytest tests/pptx/test_renderers/ -v
pytest tests/pptx/test_shape_discovery/ -v
```
