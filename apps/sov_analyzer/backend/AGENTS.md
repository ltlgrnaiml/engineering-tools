# SOV Backend - AI Coding Guide

> **Scope**: Python/FastAPI backend for SOV Analyzer tool.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Framework | FastAPI |
| Computation | Polars (NOT pandas) |
| Statistics | scipy.stats, statsmodels |
| Validation | Pydantic (from shared.contracts) |

---

## Directory Structure

```text
backend/
├── api/
│   ├── routes.py          # FastAPI route definitions
│   ├── errors.py          # ErrorResponse helpers
│   └── dependencies.py    # Dependency injection
├── services/
│   ├── analysis_service.py   # ANOVA execution
│   └── visualization_service.py
└── src/sov_analyzer/
    ├── core/
    │   ├── anova.py       # ANOVA computation
    │   └── variance.py    # Variance decomposition
    └── visualization/
        ├── box_plot.py
        └── interaction_plot.py
```

---

## ANOVA Computation (ADR-0022)

```python
import polars as pl
from scipy import stats
from shared.contracts.sov.anova import ANOVAResult, VarianceComponent

def compute_anova(
    df: pl.DataFrame,
    factors: list[str],
    response: str
) -> ANOVAResult:
    """Compute ANOVA with Type III Sum of Squares.
    
    Args:
        df: Input data as Polars DataFrame.
        factors: Categorical factor columns.
        response: Numeric response column.
    
    Returns:
        ANOVAResult with variance components summing to 100%.
    """
    # Use Type III SS (partial)
    # Ensure deterministic computation (ADR-0012)
    ...
```

---

## Variance Components

Must sum to exactly 100%:

```python
def compute_variance_components(
    anova_table: pl.DataFrame
) -> list[VarianceComponent]:
    """Compute variance percentage for each factor.
    
    Returns:
        List of VarianceComponent where sum(pct) == 100.0
    """
    total_ss = anova_table["SS"].sum()
    components = []
    for row in anova_table.iter_rows(named=True):
        pct = (row["SS"] / total_ss) * 100
        components.append(VarianceComponent(
            factor=row["factor"],
            variance_pct=pct,
            f_statistic=row["F"],
            p_value=row["p"]
        ))
    
    # Verify sum is 100%
    assert abs(sum(c.variance_pct for c in components) - 100.0) < 0.01
    return components
```

---

## DataSet Integration

```python
from shared.contracts.core.dataset import DataSetRef, DataSetManifest

# Load input DataSet
def load_input_dataset(ref: DataSetRef) -> pl.DataFrame:
    """Load DataSet from artifact store."""
    manifest_path = f"workspace/datasets/{ref.id}/manifest.json"
    data_path = f"workspace/datasets/{ref.id}/data.parquet"
    return pl.read_parquet(data_path)

# Save output with lineage
def save_result_dataset(
    result: pl.DataFrame,
    parent_ids: list[str]
) -> DataSetManifest:
    """Save result as new DataSet with lineage tracking."""
    manifest = DataSetManifest(
        id=compute_dataset_id(result),
        parent_dataset_ids=parent_ids,  # Lineage!
        ...
    )
    ...
```

---

## Testing

```bash
pytest tests/sov/ -v
pytest tests/sov/test_anova/ -v
```
