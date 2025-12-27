# Tier 4: Phase 4 SOV Analyzer - Implementation Instructions

**Document Type:** Step-by-Step Implementation Guide  
**Audience:** AI Coding Assistants, Junior Developers  
**Status:** ⚠️ BACKEND COMPLETE (frontend pending)  
**Last Updated:** 2025-01-26

---

## Phase Overview

Phase 4 implements the SOV (Source of Variation) Analyzer with ANOVA functionality.

**Duration:** Week 5-6  
**Dependencies:** Phase 1-3 complete

---

## Step 4.1: Create SOV Backend Structure ✅

**Location:** `apps/sov_analyzer/backend/`

> **Implementation Status:** Complete. Backend structure exists with ANOVA implementation and API routes.

**Structure:**
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
│   │   ├── anova.py
│   │   └── variance_components.py
│   └── core/
│       ├── __init__.py
│       └── analysis_manager.py
└── main.py
```

---

## Step 4.2: Implement ANOVA Core ✅

**File:** `src/sov_analyzer/analysis/anova.py`

> **Implementation Status:** Complete. ANOVA implementation exists (7125 bytes).

Key function signature:

```python
async def run_anova_analysis(
    data: pl.DataFrame,
    factors: list[str],
    response_columns: list[str],
    config: ANOVAConfig,
) -> ANOVAResult:
    """Run ANOVA analysis using scipy.stats."""
```

**Dependencies:** `scipy>=1.11.0`, `statsmodels>=0.14.0`

---

## Step 4.3: Create API Routes ✅

> **Implementation Status:** Complete. Routes implemented and mounted in gateway.

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/v1/analysis` | Create analysis |
| GET | `/v1/analysis/{id}` | Get analysis |
| POST | `/v1/analysis/{id}/run` | Execute |
| POST | `/v1/analysis/{id}/export` | Export as DataSet |

---

## Step 4.4: Implement DataSet Export

SOV outputs analysis results as a DataSet with columns:
- `source` (factor name)
- `sum_squares`, `df`, `mean_square`
- `f_statistic`, `p_value`
- `variance_pct`, `significant`

---

## Step 4.5: Frontend (Basic)

Create minimal UI with:
1. DataSet input selector
2. Factor/response column pickers
3. Results table display
4. "Pipe To PPTX" button

---

## Validation Checklist

### Backend Implementation

- [x] ANOVA computation implemented
- [x] API routes implemented
- [x] Gateway mount configured

### Pending Items

- [ ] DataSet input loading integration
- [ ] Results export as DataSet
- [ ] Piping to PPTX works
- [ ] SOV frontend with configuration
- [ ] Unit tests for ANOVA correctness

---

## References

- Tier 3 Spec: `tier-3-tools/sov-analyzer/SOV_SPEC.md`
- ADR-0004: Deterministic IDs
- ADR-0013: Cancellation semantics
