# Contributing Guide

> **How to contribute to the Engineering Tools Platform**

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- Git

### Setup

```bash
# Clone repository
git clone <repository-url>
cd engineering-tools

# Run setup script (Windows)
.\setup.ps1

# Or Linux/macOS
./setup.sh

# Start development server
.\start.ps1 --with-frontend
```

---

## Code Standards

### Python (Backend)

We use **Ruff** for linting and formatting.

```bash
# Format code
ruff format .

# Run linter
ruff check .

# Auto-fix issues
ruff check --fix .
```

#### Type Hints

All functions must have type hints:

```python
def process_data(data: pd.DataFrame, columns: list[str]) -> dict[str, Any]:
    """Process data and return results."""
    ...
```

#### Docstrings

Use Google-style docstrings:

```python
def create_dataset(name: str, data: pl.DataFrame) -> DataSetManifest:
    """Create a new DataSet.

    Args:
        name: Display name for the DataSet.
        data: DataFrame to store.

    Returns:
        DataSetManifest with the new dataset information.

    Raises:
        ValidationError: If data is empty or invalid.
    """
```

### TypeScript (Frontend)

```bash
cd apps/homepage/frontend
npm run lint
```

All components must have typed props:

```tsx
interface MyComponentProps {
  title: string
  onSubmit: () => void
}

export function MyComponent({ title, onSubmit }: MyComponentProps) {
  // ...
}
```

---

## Commit Conventions

We follow **Conventional Commits**:

```text
<type>(<scope>): <description>
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation |
| `style` | Formatting |
| `refactor` | Code restructuring |
| `test` | Tests |
| `chore` | Maintenance |

### Scopes

| Scope | Description |
|-------|-------------|
| `gateway` | API Gateway |
| `shared` | Shared infrastructure |
| `dat` | Data Aggregator |
| `sov` | SOV Analyzer |
| `pptx` | PPTX Generator |
| `homepage` | Homepage |
| `docs` | Documentation |

### Examples

```bash
git commit -m "feat(pptx): add dataset input support"
git commit -m "fix(gateway): handle missing dataset gracefully"
git commit -m "docs: update architecture diagram"
```

---

## Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=shared --cov=gateway tests/

# Specific test file
pytest tests/unit/test_artifact_store.py
```

### Test Structure

```text
tests/
├── unit/                    # Unit tests
│   ├── test_artifact_store.py
│   └── test_contracts.py
├── integration/             # Integration tests
│   └── test_gateway_api.py
└── conftest.py              # Shared fixtures
```

---

## Documentation

### Adding Documentation

1. Create/edit Markdown files in `docs/`
2. Update `mkdocs.yml` navigation if needed
3. Preview locally:

```bash
pip install mkdocs mkdocs-material
mkdocs serve
# Open http://localhost:8001
```

### Documentation Style

- Use `##` for main sections
- Use tables for structured data
- Include code examples
- Add diagrams where helpful (ASCII art)

---

## Pull Request Process

1. Create feature branch: `feat/description`
2. Make changes following code standards
3. Add/update tests
4. Update documentation if needed
5. Run linting and tests
6. Submit PR with clear description

---

## Project Structure

```text
engineering-tools/
├── gateway/           # API Gateway
├── shared/            # Shared code
├── apps/              # Tool applications
│   ├── data_aggregator/
│   ├── sov_analyzer/
│   ├── pptx_generator/
│   └── homepage/
├── docs/              # Documentation
├── tests/             # Test suites
└── .adrs/             # Architecture Decision Records
```
