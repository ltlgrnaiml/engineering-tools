# SOV Analyzer Tool - AI Coding Guide

> **Scope**: This AGENTS.md applies when working with files in `apps/sov_analyzer/`.

---

## Architecture Overview

SOV (Source of Variation) Analyzer performs **ANOVA-based variance decomposition**:

```
Load DataSet → Configure Factors → Run Analysis → Visualize → Export Results
```

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Factor** | Categorical variable (e.g., lot, wafer, step) |
| **Response** | Numeric variable to analyze (e.g., yield, thickness) |
| **Variance Component** | Percentage of total variance explained by each factor |
| **Post-Hoc Test** | Pairwise comparisons after ANOVA |

---

## Key ADRs

| ADR | Topic | Key Points |
|-----|-------|------------|
| **ADR-0022** | Analysis Pipeline | Type III SS, 5-stage pipeline, Polars |
| **ADR-0023** | DataSet Integration | Input via DataSetRef, output with lineage |
| **ADR-0024** | Visualization Contracts | Typed Pydantic models, extends RenderSpec |

---

## Contracts Location

**Tier-0 contracts** (SSOT): `shared/contracts/sov/`

```python
# ✅ CORRECT
from shared.contracts.sov.anova import ANOVAConfig, ANOVAResult, VarianceComponent
from shared.contracts.sov.visualization import VisualizationSpec, BoxPlotConfig

# ❌ WRONG
class ANOVAResult(BaseModel): ...  # NO!
```

---

## ANOVA Requirements (ADR-0022)

| Requirement | Implementation |
|-------------|----------------|
| Sum of Squares | **Type III** (partial SS) |
| Computation Engine | **Polars** (NOT pandas) |
| Variance Sum | Must equal 100% |
| Determinism | All computations reproducible (ADR-0012) |

---

## Pipeline Stages

```
1. Load      → Load DataSet via DataSetRef
2. Configure → Select factors and response variable
3. Compute   → Run ANOVA, calculate variance components
4. Visualize → Generate charts (box plots, interaction plots)
5. Export    → Save results as new DataSet with lineage
```

---

## DataSet Integration (ADR-0023)

### Input

```python
from shared.contracts.core.dataset import DataSetRef

# Load existing DataSet (e.g., from DAT export)
input_ref = DataSetRef(id="dat_export_abc123")
```

### Output

Results saved as new DataSet with lineage:

```python
from shared.contracts.core.dataset import DataSetManifest

result_manifest = DataSetManifest(
    id="sov_result_xyz789",
    parent_dataset_ids=["dat_export_abc123"],  # Lineage!
    # ... other fields
)
```

---

## Visualization Contracts (ADR-0024)

All visualizations extend `RenderSpec` hierarchy (ADR-0028):

| Visualization | Contract | Use Case |
|---------------|----------|----------|
| Box Plot | `BoxPlotConfig` | Distribution by factor |
| Interaction Plot | `InteractionPlotConfig` | Factor interactions |
| Pareto Chart | `ParetoChartConfig` | Variance ranking |
| Residual Plot | `ResidualPlotConfig` | Model diagnostics |

---

## Computation Notes

```python
# Use Polars, NOT pandas
import polars as pl

# ✅ CORRECT
df = pl.read_parquet("data.parquet")
result = df.group_by("factor").agg(pl.col("response").mean())

# ❌ WRONG - no pandas
import pandas as pd  # NO!
```

---

## Testing

Tests located in `tests/sov/`:

- `test_anova/` - ANOVA computation tests
- `test_variance/` - Variance component tests
- `test_visualization/` - Chart generation tests
