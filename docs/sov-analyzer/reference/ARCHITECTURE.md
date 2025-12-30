# SOV Analyzer - Architecture Overview

> **System design for the SOV (Source of Variation) Analyzer tool**

---

## Overview

The SOV Analyzer performs **ANOVA-based variance decomposition** to identify sources of variation in engineering data.

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                         SOV Frontend (React)                             │
│                         http://localhost:5174                            │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │  Analysis Dashboard                                                │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐              │  │
│  │  │Data      │ │Factor    │ │Results   │ │Charts    │              │  │
│  │  │Selection │ │Config    │ │Table     │ │Panel     │              │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘              │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                         API Gateway (FastAPI)                            │
│                         http://localhost:8000/api/sov/*                  │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────────┐
│                         SOV Backend (FastAPI)                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│  │ ANOVA Engine    │  │ Visualization   │  │ DataSet I/O     │         │
│  │ (Polars+scipy)  │  │ (contracts)     │  │ (lineage)       │         │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Analysis Pipeline (ADR-0023)

### 5-Stage Flow

```text
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Load      │──▶│  Configure  │──▶│   Compute   │
│  DataSet    │   │   Factors   │   │   ANOVA     │
└─────────────┘   └─────────────┘   └──────┬──────┘
                                           │
                  ┌─────────────┐   ┌──────▼──────┐
                  │   Export    │◀──│  Visualize  │
                  │   Results   │   │   Charts    │
                  └─────────────┘   └─────────────┘
```

### Stage Descriptions

| Stage | Purpose | Key Actions |
|-------|---------|-------------|
| **1. Load** | Input data | Load DataSet via DataSetRef |
| **2. Configure** | Define analysis | Select factors (categorical) + response (numeric) |
| **3. Compute** | Run ANOVA | Type III SS, variance decomposition |
| **4. Visualize** | Generate charts | Box plots, interaction plots, Pareto |
| **5. Export** | Save results | New DataSet with lineage tracking |

---

## ANOVA Computation (ADR-0023)

### Requirements

| Requirement | Implementation |
|-------------|----------------|
| Sum of Squares | **Type III** (partial SS) |
| Computation Engine | **Polars** (NOT pandas) |
| Statistics | scipy.stats, statsmodels |
| Variance Sum | Must equal exactly 100% |
| Determinism | All computations reproducible |

### Variance Decomposition

```text
Total Variance (100%)
        │
        ├──▶ Factor A: 45%
        │
        ├──▶ Factor B: 30%
        │
        ├──▶ Factor C: 15%
        │
        └──▶ Residual: 10%
             ─────────────
             Total: 100%
```

### ANOVA Result Structure

```python
@dataclass
class ANOVAResult:
    factors: list[str]
    response: str
    components: list[VarianceComponent]
    f_statistics: dict[str, float]
    p_values: dict[str, float]
    total_observations: int

@dataclass
class VarianceComponent:
    factor: str
    variance_pct: float  # Must sum to 100%
    sum_of_squares: float
    degrees_of_freedom: int
    mean_square: float
    f_statistic: float
    p_value: float
```

---

## Backend Architecture

### Directory Structure

```text
apps/sov_analyzer/backend/
├── api/
│   ├── routes.py              # FastAPI route definitions
│   ├── errors.py              # ErrorResponse helpers
│   └── dependencies.py        # Dependency injection
├── services/
│   ├── analysis_service.py    # ANOVA execution
│   └── visualization_service.py
└── src/sov_analyzer/
    ├── core/
    │   ├── anova.py           # ANOVA computation
    │   ├── variance.py        # Variance decomposition
    │   └── post_hoc.py        # Post-hoc tests
    └── visualization/
        ├── box_plot.py
        ├── interaction_plot.py
        └── pareto_chart.py
```

### Core Computation

```python
import polars as pl
from scipy import stats

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
    # Type III SS computation
    # Ensure deterministic results (ADR-0013)
    ...
```

---

## DataSet Integration (ADR-0024)

### Input: Load Existing DataSet

```text
┌──────────────────┐
│ Gateway API      │
│ /api/v1/datasets │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ DataSetRef       │──▶ Resolve ID to manifest
│ {id: "abc123"}   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ ArtifactStore    │──▶ Load Parquet + manifest
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Polars DataFrame │──▶ Ready for analysis
└──────────────────┘
```

### Output: Save with Lineage

```text
┌──────────────────┐
│ Analysis Results │
│ (Polars DataFrame)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ DataSetBuilder   │──▶ Create new DataSet
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────┐
│ DataSetManifest                          │
│ {                                        │
│   id: "sov_result_xyz789",               │
│   parent_dataset_ids: ["dat_abc123"],  ◀── Lineage!
│   created_at: "2025-12-30T...",          │
│   columns: [...],                        │
│   row_count: 1000                        │
│ }                                        │
└──────────────────────────────────────────┘
```

---

## Visualization Contracts (ADR-0025)

All visualizations extend the `RenderSpec` hierarchy (ADR-0029):

### Chart Types

| Chart | Contract | Use Case |
|-------|----------|----------|
| Box Plot | `BoxPlotConfig` | Distribution by factor level |
| Interaction Plot | `InteractionPlotConfig` | Factor interactions |
| Pareto Chart | `ParetoChartConfig` | Variance ranking (80/20) |
| Residual Plot | `ResidualPlotConfig` | Model diagnostics |

### Box Plot Structure

```text
┌─────────────────────────────────────────────────────────────┐
│  Response Variable by Factor                                 │
│                                                              │
│      ┬           ┬           ┬                              │
│      │           │           │                              │
│   ┌──┴──┐     ┌──┴──┐     ┌──┴──┐                          │
│   │     │     │     │     │     │                          │
│   │  ─  │     │  ─  │     │  ─  │  ← Median                │
│   │     │     │     │     │     │                          │
│   └──┬──┘     └──┬──┘     └──┬──┘                          │
│      │           │           │                              │
│      ┴           ┴           ┴                              │
│                                                              │
│   Level A     Level B     Level C                           │
└─────────────────────────────────────────────────────────────┘
```

### Pareto Chart Structure

```text
┌─────────────────────────────────────────────────────────────┐
│  Variance Contribution by Factor                             │
│                                                              │
│  100% ─────────────────────────────────────────── ●         │
│                                           ●                  │
│   80% ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ●─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─   │
│                         ●                                    │
│   60%           ●                                            │
│                                                              │
│   40%   ████                                                 │
│         ████   ████                                          │
│   20%   ████   ████   ████                                   │
│         ████   ████   ████   ████                            │
│    0%   ████   ████   ████   ████                            │
│        Factor Factor Factor Residual                         │
│           A      B      C                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### Component Structure

```text
apps/sov_analyzer/frontend/src/
├── components/
│   ├── data/
│   │   ├── DatasetSelector.tsx    # Select input DataSet
│   │   └── ColumnSelector.tsx     # Select factors/response
│   ├── analysis/
│   │   ├── FactorConfig.tsx       # Configure factors
│   │   └── VarianceTable.tsx      # Results display
│   └── charts/
│       ├── BoxPlot.tsx            # D3 box plot
│       ├── InteractionPlot.tsx    # D3 interaction
│       └── ParetoChart.tsx        # D3 Pareto
├── hooks/
│   ├── useDataset.ts
│   └── useAnalysis.ts
└── api/
    └── sov-api.ts
```

### Variance Table Display

```text
┌────────────┬────────────┬────────────┬────────────┐
│ Factor     │ Variance % │ F-statistic│ p-value    │
├────────────┼────────────┼────────────┼────────────┤
│ Factor A   │ 45.2%      │ 23.5       │ < 0.001 ** │
│ Factor B   │ 30.1%      │ 15.2       │ < 0.001 ** │
│ Factor C   │ 14.8%      │  7.1       │   0.012 *  │
│ Residual   │  9.9%      │    -       │     -      │
├────────────┼────────────┼────────────┼────────────┤
│ Total      │ 100.0%     │            │            │
└────────────┴────────────┴────────────┴────────────┘

** p < 0.01   * p < 0.05
```

---

## Key ADRs

| ADR | Topic |
|-----|-------|
| ADR-0023 | SOV Analysis Pipeline |
| ADR-0024 | DataSet Integration |
| ADR-0025 | Visualization Contracts |

---

## Related Documentation

- **AGENTS.md**: `apps/sov_analyzer/AGENTS.md` - AI assistant rules
- **SPECs**: `docs/specs/sov/` - Technical specifications
- **Contracts**: `shared/contracts/sov/` - Pydantic models
