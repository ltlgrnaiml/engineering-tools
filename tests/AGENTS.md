# Tests Directory - AI Coding Guide

> **Scope**: Testing patterns and conventions for the platform.

---

## Test Organization

```text
tests/
├── conftest.py           # Shared pytest fixtures
├── fixtures/             # Test data files
├── unit/                 # Unit tests (fast, isolated)
│   ├── test_contracts.py
│   └── test_stage_id.py
├── integration/          # Integration tests (API, services)
│   ├── test_gateway.py
│   └── test_artifact_preservation.py
├── dat/                  # DAT-specific tests
│   ├── test_adapters/
│   ├── test_api/
│   └── test_stages/
├── pptx/                 # PPTX-specific tests
│   ├── test_renderers/
│   └── test_shape_discovery/
└── sov/                  # SOV-specific tests
    └── test_anova/
```

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/unit/test_contracts.py -v

# Run tests with coverage
pytest tests/ --cov=shared --cov=gateway --cov-report=html

# Run only fast unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v

# Run tool-specific tests
pytest tests/dat/ -v
pytest tests/pptx/ -v
pytest tests/sov/ -v
```

---

## Test Naming Convention

| Pattern | Example | Purpose |
|---------|---------|---------|
| `test_{function}__{scenario}` | `test_compute_stage_id__empty_inputs` | Unit tests |
| `test_{endpoint}__{method}` | `test_stages_lock__success` | API tests |
| `test_{behavior}` | `test_unlock_preserves_artifacts` | Behavior tests |

---

## Fixture Patterns

### Shared Fixtures (conftest.py)

```python
import pytest
from shared.contracts.core.dataset import DataSetManifest

@pytest.fixture
def sample_manifest() -> DataSetManifest:
    """Create a sample DataSet manifest for testing."""
    return DataSetManifest(
        id="test_dataset_001",
        name="Test Dataset",
        # ...
    )

@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace directory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace
```

---

## Contract Tests (ADR-0036)

Test that contracts serialize/deserialize correctly:

```python
from shared.contracts.dat.profile import DATProfile

def test_profile_roundtrip():
    """Profile should survive JSON roundtrip."""
    profile = DATProfile(name="test", version="1.0")
    json_str = profile.model_dump_json()
    restored = DATProfile.model_validate_json(json_str)
    assert restored == profile
```

---

## Determinism Tests (ADR-0005)

Test that computations are reproducible:

```python
from shared.utils.stage_id import compute_stage_id

def test_stage_id_deterministic():
    """Same inputs must produce same ID."""
    inputs = {"file": "data.csv", "profile": "default"}
    id1 = compute_stage_id(inputs)
    id2 = compute_stage_id(inputs)
    assert id1 == id2
```

---

## API Integration Tests

```python
from fastapi.testclient import TestClient
from gateway.main import app

client = TestClient(app)

def test_health_endpoint():
    """Health endpoint should return 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

---

## Test Data in fixtures/

Place test data files in `tests/fixtures/`:

```text
tests/fixtures/
├── sample_data.csv
├── sample_profile.yaml
├── sample_template.pptx
└── expected_outputs/
    └── parsed_data.parquet
```

Access via fixture:

```python
@pytest.fixture
def sample_csv(request):
    """Path to sample CSV file."""
    return Path(request.fspath).parent / "fixtures" / "sample_data.csv"
```

---

## What to Test

| Category | What to Test | Priority |
|----------|--------------|----------|
| Contracts | Serialization roundtrip | P0 |
| Stage IDs | Determinism | P0 |
| API endpoints | Request/response | P0 |
| Error handling | Error responses | P1 |
| Edge cases | Empty inputs, large files | P1 |
| Cancellation | Artifact preservation | P1 |
