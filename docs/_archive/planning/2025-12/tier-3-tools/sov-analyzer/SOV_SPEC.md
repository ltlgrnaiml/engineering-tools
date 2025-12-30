# Tier 3: SOV Analyzer Tool Specification

**Document Type:** Tool Specification  
**Audience:** Engineers  
**Status:** TODO - Phase 4  
**Last Updated:** 2025-01-26

---

## Overview

The SOV (Source of Variation) Analyzer performs statistical analysis on manufacturing data, primarily ANOVA (Analysis of Variance) to identify sources of variation in process metrics.

---

## Responsibilities

1. **DataSet Input** - Accept DataSet from DAT or manual upload
2. **Factor Selection** - Select categorical factors for analysis
3. **Response Selection** - Select numeric response columns
4. **Analysis Configuration** - Configure ANOVA parameters
5. **Analysis Execution** - Run ANOVA with progress tracking
6. **Results Display** - Show variance components, F-tests
7. **Export** - Output results as DataSet for PPTX

---

## Acceptance Criteria (SOV)

### AC-SOV1: DataSet Input

- [ ] Accept DataSet ID via query parameter
- [ ] Accept DataSet ID via API request body
- [ ] Validate DataSet has required columns
- [ ] Show DataSet preview with column types

### AC-SOV2: Factor Selection

- [ ] List categorical columns from DataSet
- [ ] User selects 1+ factors
- [ ] Validate factors have multiple levels
- [ ] Support nested factors (future)

### AC-SOV3: Response Selection

- [ ] List numeric columns from DataSet
- [ ] User selects 1+ response columns
- [ ] Validate responses are numeric
- [ ] Handle missing values (drop or impute)

### AC-SOV4: Analysis Configuration

- [ ] Analysis type: One-way, Two-way, Nested (future)
- [ ] Confidence level (default 95%)
- [ ] Post-hoc tests (Tukey, Bonferroni - future)

### AC-SOV5: Analysis Execution

- [ ] Run ANOVA via scipy/statsmodels
- [ ] Progress tracking for large datasets
- [ ] Cancellation support
- [ ] Deterministic results (fixed seed)

### AC-SOV6: Results Display

- [ ] ANOVA table (SS, DF, MS, F, p-value)
- [ ] Variance components (% contribution)
- [ ] Visualization (bar chart of variance %)
- [ ] Significance indicators

### AC-SOV7: Export

- [ ] Output as DataSet with SOV results
- [ ] Include analysis metadata in manifest
- [ ] Lineage tracks input DataSet
- [ ] "Pipe To" button for PPTX

---

## Code Map

### Backend Structure

```text
apps/sov-analyzer/backend/
├── src/sov_analyzer/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   └── schemas.py
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── anova.py            # Core ANOVA implementation
│   │   ├── variance_components.py
│   │   └── validators.py       # Input validation
│   ├── core/
│   │   ├── __init__.py
│   │   └── analysis_manager.py
│   └── models/
│       ├── __init__.py
│       ├── config.py
│       └── results.py
└── main.py
```

### Key Functions

#### `analysis/anova.py`

```python
async def run_anova_analysis(
    data: pl.DataFrame,
    factors: list[str],
    response_columns: list[str],
    config: ANOVAConfig,
    progress_callback: Callable[[float], None],
    cancel_token: CancelToken,
) -> ANOVAResult:
    """Run ANOVA analysis on input data.
    
    Returns:
        ANOVAResult with:
        - anova_table: DataFrame with SS, DF, MS, F, p-value
        - variance_components: Dict of factor -> variance %
        - summary: Overall statistics
    """
```

#### `analysis/variance_components.py`

```python
def compute_variance_components(
    anova_result: ANOVAResult,
    method: str = "type_iii",
) -> dict[str, float]:
    """Compute variance component percentages.
    
    Returns dict mapping factor names to % of total variance.
    """
```

---

## API Endpoints

### Analysis

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/analysis` | POST | Create new analysis |
| `/v1/analysis` | GET | List analyses |
| `/v1/analysis/{id}` | GET | Get analysis details |
| `/v1/analysis/{id}` | DELETE | Delete analysis |
| `/v1/analysis/{id}/run` | POST | Execute analysis |
| `/v1/analysis/{id}/status` | GET | Get execution status |
| `/v1/analysis/{id}/results` | GET | Get results |
| `/v1/analysis/{id}/export` | POST | Export as DataSet |

---

## Output DataSet Schema

SOV produces a DataSet with analysis results:

```python
# Output columns for ANOVA table
columns = [
    ColumnMeta(name="source", dtype="string"),        # Factor name
    ColumnMeta(name="sum_squares", dtype="float64"),  # SS
    ColumnMeta(name="df", dtype="int64"),             # Degrees of freedom
    ColumnMeta(name="mean_square", dtype="float64"),  # MS
    ColumnMeta(name="f_statistic", dtype="float64"),  # F value
    ColumnMeta(name="p_value", dtype="float64"),      # p-value
    ColumnMeta(name="variance_pct", dtype="float64"), # % of variance
    ColumnMeta(name="significant", dtype="bool"),     # p < alpha
]

# Manifest metadata
manifest = DataSetManifest(
    created_by_tool="sov",
    analysis_type="anova",
    factors=["lot", "wafer", "tool"],
    response_columns=["cd_mean", "cd_sigma"],
    parent_dataset_ids=["ds_raw_input"],
)
```

---

## Change Order

### Phase 4A: Backend Core (Week 5)

1. Create `apps/sov-analyzer/backend/` structure
2. Implement ANOVA core (`analysis/anova.py`)
3. Implement variance components
4. Create API routes
5. Write unit tests

### Phase 4B: DataSet Integration (Week 5-6)

1. Add DataSet input handling
2. Implement result export as DataSet
3. Register in artifact store
4. Add lineage tracking

### Phase 4C: Frontend (Week 6)

1. Create frontend structure
2. Factor/response selection UI
3. Results display (table + chart)
4. "Pipe To" integration

---

## Dependencies

- `scipy>=1.11.0` - ANOVA computations
- `statsmodels>=0.14.0` - Advanced statistics (future)
- `polars>=0.20.0` - Data manipulation

---

## Validation Plan

### Unit Tests

- [ ] ANOVA computation correctness
- [ ] Variance component calculation
- [ ] Input validation

### Integration Tests

- [ ] Full analysis with DataSet input
- [ ] Export as DataSet
- [ ] Piping to PPTX

### E2E Tests

- [ ] Receive piped DataSet from DAT
- [ ] Run ANOVA, view results
- [ ] Pipe results to PPTX

---

## ADR References

| ADR | Application in SOV |
|-----|-------------------|
| ADR-0005 | Deterministic analysis IDs |
| ADR-0009 | Timestamps in results |
| ADR-0013 | Windows-first (scipy compatibility) |
| ADR-0014 | Analysis cancellation |
