# EXP-001: Enhanced L1 Model Scoring (V2 Rubric)

## Scoring Rubric V2 Weights

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Correctness | 25% | Code works as intended |
| Completeness | 20% | All required tasks finished |
| Architectural Consistency | 20% | Follows existing project patterns |
| Schema Adherence | 15% | Follows L1 context guidance precisely |
| Code Quality | 10% | Clean, maintainable code |
| Efficiency | 10% | Speed and token efficiency |

---

## Model Scores

### Claude Opus 4.5 Thinking (5x cost)

| Criterion | Max | Score | Notes |
|-----------|-----|-------|-------|
| **Correctness (25%)** | | | |
| C1: Imports work | 5 | 5 | ✓ All imports resolve |
| C2: Endpoints exist | 5 | 5 | ✓ In devtools_service.py |
| C3: Schema valid | 5 | 5 | ✓ Pydantic models work |
| C4: Tests pass | 10 | 10 | ✓ Tests in correct location |
| **Subtotal** | 25 | **25** | |
| **Completeness (20%)** | | | |
| CP1-6: All tasks | 20 | 20 | ✓ All 6 tasks complete |
| **Subtotal** | 20 | **20** | |
| **Architectural Consistency (20%)** | | | |
| AC1: Style match | 5 | 5 | ✓ Functional style matches existing |
| AC2: File location | 5 | 5 | ✓ Correct directories |
| AC3: Naming | 5 | 4 | `ARTIFACT_DIRECTORIES` vs existing patterns |
| AC4: No extras | 5 | 3 | ⚠️ Created `Test-Discussion.md` |
| **Subtotal** | 20 | **17** | |
| **Schema Adherence (15%)** | | | |
| SA1: Version format | 4 | 4 | ✓ `2025.12.01` correct |
| SA2: Enum values | 4 | 3 | Only 5 statuses (minimal) |
| SA3: Field names | 4 | 4 | ✓ `search` param |
| SA4: Import style | 3 | 3 | ✓ Correct |
| **Subtotal** | 15 | **14** | |
| **Code Quality (10%)** | | | |
| Q1: Linting | 3 | 3 | ✓ Clean |
| Q2: Type hints | 3 | 3 | ✓ Full coverage |
| Q3: Docstrings | 2 | 2 | ✓ Google-style |
| Q4: No dead code | 2 | 2 | ✓ Clean |
| **Subtotal** | 10 | **10** | |
| **Efficiency (10%)** | | | |
| E1: Time (<5min=5) | 5 | 5 | ~4 minutes |
| E2: Messages | 5 | 4 | Est. 10-15 messages |
| **Subtotal** | 10 | **9** | |
| **TOTAL** | 100 | **95** | |

---

### Claude Sonnet 4.5 Thinking (3x cost)

| Criterion | Max | Score | Notes |
|-----------|-----|-------|-------|
| **Correctness (25%)** | | | |
| C1: Imports work | 5 | 5 | ✓ All imports resolve |
| C2: Endpoints exist | 5 | 5 | ✓ In devtools_service.py |
| C3: Schema valid | 5 | 5 | ✓ Pydantic models work |
| C4: Tests pass | 10 | 8 | ⚠️ Tests in wrong dir (tests/ not tests/gateway/) |
| **Subtotal** | 25 | **23** | |
| **Completeness (20%)** | | | |
| CP1-6: All tasks | 20 | 20 | ✓ All 6 tasks complete |
| **Subtotal** | 20 | **20** | |
| **Architectural Consistency (20%)** | | | |
| AC1: Style match | 5 | 5 | ✓ Functional style matches existing |
| AC2: File location | 5 | 3 | ⚠️ Tests in wrong directory |
| AC3: Naming | 5 | 3 | `search_query` vs `search` |
| AC4: No extras | 5 | 5 | ✓ No extra files |
| **Subtotal** | 20 | **16** | |
| **Schema Adherence (15%)** | | | |
| SA1: Version format | 4 | 3 | `2025.12.1` (missing leading zero) |
| SA2: Enum values | 4 | 4 | 9 statuses (comprehensive) |
| SA3: Field names | 4 | 2 | ⚠️ `search_query` not `search` |
| SA4: Import style | 3 | 3 | ✓ Correct |
| **Subtotal** | 15 | **12** | |
| **Code Quality (10%)** | | | |
| Q1: Linting | 3 | 3 | ✓ Clean |
| Q2: Type hints | 3 | 3 | ✓ Full coverage |
| Q3: Docstrings | 2 | 2 | ✓ Google-style |
| Q4: No dead code | 2 | 2 | ✓ Clean |
| **Subtotal** | 10 | **10** | |
| **Efficiency (10%)** | | | |
| E1: Time (<5min=5) | 5 | 5 | ~4 minutes |
| E2: Messages | 5 | 4 | Est. 10-15 messages |
| **Subtotal** | 10 | **9** | |
| **TOTAL** | 100 | **90** | |

---

### Gemini 3 Pro High (3x cost)

| Criterion | Max | Score | Notes |
|-----------|-----|-------|-------|
| **Correctness (25%)** | | | |
| C1: Imports work | 5 | 5 | ✓ All imports resolve |
| C2: Endpoints exist | 5 | 5 | ✓ In devtools_service.py |
| C3: Schema valid | 5 | 5 | ✓ Pydantic models work |
| C4: Tests pass | 10 | 10 | ✓ Tests in correct location |
| **Subtotal** | 25 | **25** | |
| **Completeness (20%)** | | | |
| CP1-6: All tasks | 20 | 20 | ✓ All 6 tasks complete |
| **Subtotal** | 20 | **20** | |
| **Architectural Consistency (20%)** | | | |
| AC1: Style match | 5 | 2 | ❌ Class-based, not functional |
| AC2: File location | 5 | 5 | ✓ Correct directories |
| AC3: Naming | 5 | 3 | `ARTIFACT_DIRS` (abbreviated) |
| AC4: No extras | 5 | 5 | ✓ No extra files |
| **Subtotal** | 20 | **15** | |
| **Schema Adherence (15%)** | | | |
| SA1: Version format | 4 | 1 | ❌ `0.1.0` wrong format |
| SA2: Enum values | 4 | 3 | 11 statuses (over-engineered, `DONE` vs `COMPLETED`) |
| SA3: Field names | 4 | 4 | ✓ `search` param |
| SA4: Import style | 3 | 3 | ✓ Correct |
| **Subtotal** | 15 | **11** | |
| **Code Quality (10%)** | | | |
| Q1: Linting | 3 | 3 | ✓ Clean |
| Q2: Type hints | 3 | 3 | ✓ Full coverage |
| Q3: Docstrings | 2 | 2 | ✓ Present |
| Q4: No dead code | 2 | 2 | ✓ Most concise |
| **Subtotal** | 10 | **10** | |
| **Efficiency (10%)** | | | |
| E1: Time (5-10min=4) | 5 | 3 | ~6-8 minutes |
| E2: Messages | 5 | 4 | Est. 10-15 messages |
| **Subtotal** | 10 | **7** | |
| **TOTAL** | 100 | **88** | |

---

## Summary Ranking

| Rank | Model | Score | Cost | Efficiency | Key Deductions |
|------|-------|-------|------|------------|----------------|
| 1 | **Opus 4.5** | 95/100 | 5x | 19.0 | Extra file (-2), naming (-1) |
| 2 | **Sonnet 4.5** | 90/100 | 3x | 30.0 | Wrong test dir (-4), param name (-2) |
| 3 | **Gemini Pro** | 88/100 | 3x | 29.3 | OOP style (-3), wrong version (-3) |

---

## L1 Schema Improvement Recommendations

Based on the stochastic variation observed, the L1 `context` field should include:

### 1. Architecture Style (Critical)

```json
"context": [
  "ARCHITECTURE: Use functional style (no classes) matching existing services"
]
```

### 2. Version Format (Critical)

```json
"context": [
  "VERSION: Use __version__ = 'YYYY.MM.PATCH' format (e.g., 2025.12.01)"
]
```

### 3. File Locations (Important)

```json
"context": [
  "FILE: Place tests in tests/gateway/test_devtools_workflow.py"
]
```

### 4. Enum Value Guidance (Important)

```json
"context": [
  "ENUM: ArtifactStatus should include: DRAFT, ACTIVE, DEPRECATED, SUPERSEDED, COMPLETED"
]
```

### 5. Parameter Naming (Nice-to-have)

```json
"context": [
  "PARAMS: Use 'search' not 'search_query' for consistency"
]
```

### 6. Variable Naming (Nice-to-have)

```json
"context": [
  "NAMING: Use ARTIFACT_DIRECTORIES (not ARTIFACT_DIRS) for clarity"
]
```

---

## Best Model Recommendation

**For L1 execution**: **Claude Opus 4.5 Thinking**

- Highest score (95/100)
- Best architectural consistency
- Only deductions: minor naming and one extra file

**For cost-effectiveness**: **Claude Sonnet 4.5 Thinking**

- Score 90/100 at 3x cost (efficiency 30.0)
- Issues are easily correctable with better L1 context

---

## Next Steps

1. Update L1 schema with recommended context additions
2. Re-run experiment to measure variation reduction
3. Compare with L3 results to quantify granularity benefit
