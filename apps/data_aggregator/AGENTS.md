# Data Aggregator Tool (DAT) - AI Coding Guide

> **Scope**: This AGENTS.md applies when working with files in `apps/data_aggregator/`.

---

## Architecture Overview

DAT is a **profile-driven data extraction tool** with an 8-stage pipeline:

```
Upload → Context → Preview → Select → Aggregate → Parse → Export → Complete
```

### Three-Layer Architecture (ADR-0012)

```
┌─────────────────────────────────────────┐
│  Profile Layer (SSoT)                   │  YAML profiles define WHAT to extract
│  - 10-section YAML schema               │
│  - Builtin + custom profiles            │
├─────────────────────────────────────────┤
│  Adapter Layer (HOW)                    │  File handlers execute extraction
│  - CSV, Excel, JSON, XML adapters       │
│  - AdapterFactory pattern               │
├─────────────────────────────────────────┤
│  Dataset Layer (OUTPUT)                 │  Parquet + manifest output
│  - DataSetManifest contract             │
│  - Lineage tracking                     │
└─────────────────────────────────────────┘
```

---

## Key ADRs

| ADR | Topic | Key Points |
|-----|-------|------------|
| **ADR-0004** | Stage Graph | 8-stage pipeline, unlock cascades downstream |
| **ADR-0012** | Profile-Driven Extraction | YAML profiles, 6 extraction strategies |
| **ADR-0041** | Large File Streaming | >10MB uses streaming mode |
| **ADR-0043** | Horizontal Wizard UI | Stepper pattern, collapsible panels |
| **ADR-0014** | Cancellation | Preserve completed artifacts, no partial data |

---

## Contracts Location

**Tier-0 contracts** (SSOT): `shared/contracts/dat/`

```python
# ✅ CORRECT
from shared.contracts.dat.profile import DATProfile, TableConfig
from shared.contracts.dat.stage import DATStageState

# ❌ WRONG - never define locally
class DATProfile(BaseModel): ...  # NO!
```

---

## Profile Structure (SPEC-0033)

Profiles have 10 sections:

1. `metadata` - name, version, description
2. `source` - file patterns, adapters
3. `context` - extraction settings
4. `tables` - table definitions
5. `columns` - column mappings
6. `aggregation` - grouping rules
7. `validation` - data quality rules
8. `output` - export format settings
9. `ui` - UI hints and labels
10. `advanced` - streaming, caching options

---

## Extraction Strategies (SPEC-0009)

| Strategy | Use Case |
|----------|----------|
| `flat_object` | Single-level key-value data |
| `headers_data` | Header row + data rows |
| `array_of_objects` | JSON array of records |
| `repeat_over` | Repeated structures |
| `unpivot` | Wide to long transformation |
| `join` | Multi-table joins |

---

## Stage State Model (ADR-0001)

```
UNLOCKED ──lock()──► LOCKED ──complete()──► COMPLETED
    ▲                   │
    └───unlock()────────┘  (cascades to downstream stages)
```

**Rules**:

- Unlock cascades to all downstream stages
- Never delete artifacts on unlock (ADR-0002)
- Context and Preview stages are optional (ADR-0004)

---

## Large File Handling (ADR-0041)

| File Size | Mode | Behavior |
|-----------|------|----------|
| < 10MB | Eager | Load entire file into memory |
| ≥ 10MB | Streaming | Process in chunks |

**Thresholds**:

- Schema probe: < 5 seconds
- Preview load: < 2 seconds (sampling)
- Memory: Must not exceed `max_memory_mb` config

---

## Testing

Tests located in `tests/dat/`:

- `test_adapters/` - Adapter unit tests
- `test_stages/` - Stage execution tests
- `test_profiles/` - Profile validation tests
- `test_api/` - API integration tests
