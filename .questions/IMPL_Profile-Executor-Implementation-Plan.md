# Implementation Plan: Profile-Driven ETL Architecture

**Date**: 2025-12-29  
**Status**: APPROVED FOR IMPLEMENTATION  
**Implements**: ADR-0011, SPEC-DAT-0011, SPEC-DAT-0012  
**Goal**: Bridge the gap between beautiful profile YAML and actual code execution

---

## Executive Summary

The profile `cdsem_metrology_profile.yaml` defines 22 tables with rich extraction logic, but **none of it is actually used**. The current `parse.py` reads files directly via adapters without applying profile-driven extraction.

### Gap Analysis

| Profile Feature | YAML Has It | Code Implements It |
|-----------------|-------------|-------------------|
| Meta/versioning | ✅ | ✅ |
| Datasource filters | ✅ | ❌ (not used) |
| Context regex patterns | ✅ | ❌ (not used) |
| Context JSONPath | ✅ | ❌ (not used) |
| Table `flat_object` strategy | ✅ | ❌ (not used) |
| Table `headers_data` strategy | ✅ | ❌ (not used) |
| Table `repeat_over` iteration | ✅ | ❌ (not used) |
| Stable columns policy | ✅ | ❌ (not used) |
| Normalization rules | ✅ | ❌ (not used) |
| Output configuration | ✅ | ❌ (not used) |
| UI hints | ✅ | ❌ (not used) |

### ROI Impact

Once implemented:
- **Power users**: Full YAML control to create domain-specific profiles
- **End users**: Curated experiences with sensible defaults
- **Data quality**: Automatic validation via stable columns
- **Traceability**: Profile ID in every DataSetManifest for lineage

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          parse.py                                    │
│                    (orchestrates extraction)                         │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ delegates to
                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     ProfileExecutor                                  │
│  + execute(profile, files, context) → Dict[table_id, DataFrame]     │
│  + extract_table(table_config, data, context) → DataFrame           │
│  + apply_context(df, context, level) → DataFrame                    │
└───────────────────────────┬─────────────────────────────────────────┘
                            │ uses
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ FlatObjectStrategy │ │HeadersDataStrategy│ │RepeatOverStrategy│
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

---

## Milestone Breakdown

### M1: ProfileExecutor Core (Foundation) ⭐ CRITICAL PATH

**Goal**: Create the ProfileExecutor engine that interprets profiles and executes extraction strategies.

#### Files to Create

| File | Purpose |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/profile_executor.py` | Core executor engine |
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/strategies/__init__.py` | Strategy exports |
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/strategies/base.py` | Base strategy protocol |
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/strategies/flat_object.py` | flat_object implementation |
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/strategies/headers_data.py` | headers_data implementation |
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/strategies/repeat_over.py` | repeat_over implementation |
| `tests/unit/dat/profiles/test_profile_executor.py` | Unit tests |
| `tests/unit/dat/profiles/strategies/test_strategies.py` | Strategy tests |

#### Files to Modify

| File | Changes |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/stages/parse.py` | Replace direct adapter reads with ProfileExecutor |
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/profile_loader.py` | Add `SelectConfig` dataclass with all fields |

#### Implementation Details

**1. Base Strategy Protocol** (`strategies/base.py`):
```python
from typing import Any, Protocol
import polars as pl

class ExtractionStrategy(Protocol):
    """Protocol for extraction strategies per SPEC-DAT-0012."""
    
    def extract(self, data: Any, config: SelectConfig, context: dict) -> pl.DataFrame:
        """Execute extraction and return DataFrame."""
        ...
    
    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate configuration, return list of errors."""
        ...
```

**2. FlatObjectStrategy** (`strategies/flat_object.py`):
```python
class FlatObjectStrategy:
    """Extract flat JSON object as single-row DataFrame.
    
    Per SPEC-DAT-0012: Object keys become column names, values become single row.
    """
    
    def extract(self, data: Any, config: SelectConfig, context: dict) -> pl.DataFrame:
        # 1. Navigate to path using JSONPath
        # 2. Extract object at path
        # 3. Flatten if config.flatten_nested
        # 4. Return single-row DataFrame
```

**3. HeadersDataStrategy** (`strategies/headers_data.py`):
```python
class HeadersDataStrategy:
    """Extract headers + data arrays as DataFrame.
    
    Per SPEC-DAT-0012: headers_key contains column names, data_key contains rows.
    """
    
    def extract(self, data: Any, config: SelectConfig, context: dict) -> pl.DataFrame:
        # 1. Navigate to path
        # 2. Get headers from config.headers_key
        # 3. Get data rows from config.data_key
        # 4. Build DataFrame with headers as columns
```

**4. RepeatOverStrategy** (`strategies/repeat_over.py`):
```python
class RepeatOverStrategy:
    """Extract with iteration over array elements.
    
    Per SPEC-DAT-0012: Iterate over array, apply base strategy at each element,
    inject context fields from parent, concatenate results.
    """
    
    def __init__(self, base_strategy: ExtractionStrategy):
        self.base_strategy = base_strategy
    
    def extract(self, data: Any, config: SelectConfig, context: dict) -> pl.DataFrame:
        # 1. Get array at repeat_over.path
        # 2. For each element:
        #    a. Substitute {index_var} in config.path
        #    b. Extract inject_fields from element
        #    c. Call base_strategy.extract()
        #    d. Add injected columns
        # 3. Concatenate all DataFrames
```

**5. ProfileExecutor** (`profile_executor.py`):
```python
class ProfileExecutor:
    """Interprets profiles and executes extraction per ADR-0011."""
    
    def __init__(self):
        self.strategies = {
            "flat_object": FlatObjectStrategy(),
            "headers_data": HeadersDataStrategy(),
            "array_of_objects": ArrayOfObjectsStrategy(),
        }
        self.jsonpath_engine = "jsonpath-ng"  # default, profile can override
    
    async def execute(
        self,
        profile: DATProfile,
        files: list[Path],
        context: dict,
        selected_tables: list[str] | None = None,
    ) -> dict[str, pl.DataFrame]:
        """Execute full profile extraction.
        
        Args:
            profile: Loaded DATProfile
            files: List of files to process
            context: Context dictionary (from context stage)
            selected_tables: Optional filter for specific tables
            
        Returns:
            Dict mapping table_id to extracted DataFrame
        """
        results = {}
        
        for file_path in files:
            # Load file content via adapter
            data = await self._load_file(file_path, profile)
            
            # Extract each selected table
            for level_name, table_config in profile.get_all_tables():
                if selected_tables and table_config.id not in selected_tables:
                    continue
                
                df = await self.extract_table(table_config, data, context)
                
                # Apply context columns
                df = self._apply_context(df, context, level_name)
                
                # Accumulate results
                if table_config.id in results:
                    results[table_config.id] = pl.concat([
                        results[table_config.id], df
                    ], how="diagonal")
                else:
                    results[table_config.id] = df
        
        return results
    
    async def extract_table(
        self,
        table_config: TableConfig,
        data: Any,
        context: dict,
    ) -> pl.DataFrame:
        """Extract single table using configured strategy."""
        if not table_config.select:
            return pl.DataFrame()
        
        strategy_name = table_config.select.strategy
        
        # Handle repeat_over wrapper
        if table_config.select.repeat_over:
            base_strategy = self.strategies.get(strategy_name)
            strategy = RepeatOverStrategy(base_strategy)
        else:
            strategy = self.strategies.get(strategy_name)
        
        if not strategy:
            raise ValueError(f"Unknown strategy: {strategy_name}")
        
        return strategy.extract(data, table_config.select, context)
```

**6. Integration in parse.py**:
```python
# In execute_parse():

# NEW: If profile specified, use ProfileExecutor
if profile:
    executor = ProfileExecutor()
    results = await executor.execute(
        profile=profile,
        files=config.selected_files,
        context=context,
        selected_tables=config.selected_tables.get("__all__"),
    )
    
    # Combine all tables into single DataFrame for backward compat
    # OR return dict for new multi-table export
    all_dfs = list(results.values())
    combined = pl.concat(all_dfs, how="diagonal") if all_dfs else pl.DataFrame()
else:
    # Legacy path: direct adapter reads
    # ... existing code ...
```

#### Acceptance Criteria

- [ ] **AC-M1-001**: `ProfileExecutor.execute()` returns `Dict[table_id, DataFrame]`
- [ ] **AC-M1-002**: `FlatObjectStrategy` extracts flat JSON objects to single-row DataFrames
- [ ] **AC-M1-003**: `HeadersDataStrategy` extracts headers+data to multi-row DataFrames
- [ ] **AC-M1-004**: `RepeatOverStrategy` iterates and concatenates results
- [ ] **AC-M1-005**: Context columns are injected into each extracted DataFrame
- [ ] **AC-M1-006**: Unit tests pass for all strategies with fixture data
- [ ] **AC-M1-007**: `parse.py` uses `ProfileExecutor` when profile is specified

#### Test Fixtures

Create `tests/fixtures/cdsem_sample.json`:
```json
{
  "metadata": {
    "lot_id": "LOTABC12345",
    "wafer_id": "W01"
  },
  "summary": {
    "total_images": 50,
    "valid_images": 48,
    "mean_cd": 45.2,
    "sigma_cd": 1.3
  },
  "statistics": {
    "columns": ["parameter", "mean", "std_dev", "min", "max"],
    "values": [
      ["cd_left", 45.1, 1.2, 42.0, 48.0],
      ["cd_right", 45.3, 1.1, 43.0, 47.5]
    ]
  },
  "sites": [
    {
      "site_id": "S01",
      "name": "Center",
      "cd_data": {
        "headers": ["x", "y", "cd_value"],
        "rows": [[0, 0, 45.1], [1, 0, 45.2]]
      }
    },
    {
      "site_id": "S02", 
      "name": "Edge",
      "cd_data": {
        "headers": ["x", "y", "cd_value"],
        "rows": [[10, 0, 45.5], [11, 0, 45.6]]
      }
    }
  ]
}
```

#### Verification Commands

```bash
# Run unit tests
pytest tests/unit/dat/profiles/test_profile_executor.py -v

# Run strategy tests
pytest tests/unit/dat/profiles/strategies/ -v

# Integration test with real profile
python -c "
from pathlib import Path
from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import load_profile
from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_executor import ProfileExecutor

profile = load_profile('apps/data_aggregator/backend/src/dat_aggregation/profiles/cdsem_metrology_profile.yaml')
print(f'Loaded profile: {profile.title}')
print(f'Tables defined: {len(profile.get_all_tables())}')
"
```

---

### M2: Context Auto-Extraction

**Goal**: Implement the 4-level context extraction priority system.

#### Priority Levels (per ADR-0011)

1. **User Override** (highest): Explicit values from UI
2. **Content Patterns**: JSONPath extraction from file content
3. **Regex Patterns**: Regex extraction from filename/path
4. **Defaults** (lowest): Static values from profile

#### Files to Create

| File | Purpose |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/context_extractor.py` | Context extraction engine |
| `tests/unit/dat/profiles/test_context_extractor.py` | Unit tests |

#### Files to Modify

| File | Changes |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/profile_loader.py` | Add `ContentPattern` dataclass |
| `apps/data_aggregator/backend/src/dat_aggregation/stages/context.py` | Use ContextExtractor |

#### Implementation Details

**ContextExtractor** (`context_extractor.py`):
```python
class ContextExtractor:
    """4-level priority context extraction per ADR-0011."""
    
    def extract(
        self,
        profile: DATProfile,
        file_path: Path,
        file_content: dict | None = None,
        user_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract context using 4-level priority."""
        context = {}
        
        # Priority 4: Defaults (lowest)
        if profile.context_defaults and profile.context_defaults.defaults:
            context.update(profile.context_defaults.defaults)
        
        # Priority 3: Regex from filename
        if profile.context_defaults:
            regex_values = self._extract_regex(
                profile.context_defaults.regex_patterns,
                file_path,
            )
            context.update(regex_values)
        
        # Priority 2: JSONPath from content
        if file_content and profile.context_defaults:
            content_values = self._extract_jsonpath(
                profile.context_defaults.content_patterns,
                file_content,
            )
            context.update(content_values)
        
        # Priority 1: User overrides (highest)
        if user_overrides:
            # Only allow overrides for fields in allow_user_override
            allowed = profile.context_defaults.allow_user_override if profile.context_defaults else []
            for key, value in user_overrides.items():
                if not allowed or key in allowed:
                    context[key] = value
        
        return context
    
    def _extract_regex(
        self,
        patterns: list[RegexPattern],
        file_path: Path,
    ) -> dict[str, str]:
        """Extract values using regex patterns."""
        results = {}
        for pattern in patterns:
            scope_value = self._get_scope_value(pattern.scope, file_path)
            try:
                match = re.search(pattern.pattern, scope_value)
                if match:
                    groups = match.groupdict()
                    if pattern.field in groups:
                        value = groups[pattern.field]
                        # Apply transform if specified
                        if pattern.transform:
                            value = self._apply_transform(
                                value, pattern.transform, pattern.transform_args
                            )
                        results[pattern.field] = value
                elif pattern.required:
                    logger.warning(
                        f"Required pattern '{pattern.field}' not matched in {scope_value}"
                    )
            except re.error as e:
                logger.error(f"Invalid regex for {pattern.field}: {e}")
        return results
    
    def _extract_jsonpath(
        self,
        patterns: list[ContentPattern],
        content: dict,
    ) -> dict[str, Any]:
        """Extract values using JSONPath."""
        from jsonpath_ng import parse as jsonpath_parse
        
        results = {}
        for pattern in patterns:
            try:
                expr = jsonpath_parse(pattern.path)
                matches = expr.find(content)
                if matches:
                    results[pattern.field] = matches[0].value
                elif pattern.default is not None:
                    results[pattern.field] = pattern.default
                elif pattern.required:
                    logger.warning(f"Required JSONPath '{pattern.field}' not found")
            except Exception as e:
                logger.error(f"JSONPath error for {pattern.field}: {e}")
        return results
```

#### Acceptance Criteria

- [ ] **AC-M2-001**: Defaults from profile are applied (priority 4)
- [ ] **AC-M2-002**: Regex patterns extract from filename (priority 3)
- [ ] **AC-M2-003**: JSONPath patterns extract from content (priority 2)
- [ ] **AC-M2-004**: User overrides have highest priority (priority 1)
- [ ] **AC-M2-005**: Only `allow_user_override` fields can be overridden
- [ ] **AC-M2-006**: `on_fail` behavior (warn/error/skip_file) is honored
- [ ] **AC-M2-007**: Transforms (e.g., `parse_date`) are applied

#### Test Cases

```python
def test_priority_4_defaults():
    """Defaults apply when no other source provides value."""
    
def test_priority_3_regex_overrides_defaults():
    """Regex extraction overrides defaults."""
    
def test_priority_2_jsonpath_overrides_regex():
    """JSONPath extraction overrides regex."""
    
def test_priority_1_user_overrides_all():
    """User override has highest priority."""
    
def test_user_override_restricted_to_allowed_fields():
    """User cannot override fields not in allow_user_override."""
```

---

### M3: Validation Engine

**Goal**: Implement stable columns validation and schema enforcement.

#### Files to Create

| File | Purpose |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/validation_engine.py` | Validation engine |
| `tests/unit/dat/profiles/test_validation_engine.py` | Unit tests |

#### Implementation Details

**ValidationEngine** (`validation_engine.py`):
```python
@dataclass
class ValidationResult:
    """Result of table validation."""
    table_id: str
    valid: bool
    errors: list[str]
    warnings: list[str]
    missing_columns: list[str]
    extra_columns: list[str]

class ValidationEngine:
    """Validates extracted DataFrames against profile rules."""
    
    def validate_stable_columns(
        self,
        df: pl.DataFrame,
        table_config: TableConfig,
    ) -> ValidationResult:
        """Validate DataFrame has expected columns per stable_columns policy."""
        errors = []
        warnings = []
        missing = []
        extra = []
        
        actual_cols = set(df.columns)
        expected_cols = set(table_config.stable_columns)
        
        # Check for missing columns
        missing = list(expected_cols - actual_cols)
        
        # Check for extra columns (if not subset mode)
        if not table_config.stable_columns_subset:
            extra = list(actual_cols - expected_cols)
        
        # Apply mode
        mode = table_config.stable_columns_mode
        if missing:
            msg = f"Missing columns: {missing}"
            if mode == "error":
                errors.append(msg)
            elif mode == "warn":
                warnings.append(msg)
            # else ignore
        
        if extra and not table_config.stable_columns_subset:
            msg = f"Unexpected columns: {extra}"
            if mode == "error":
                errors.append(msg)
            elif mode == "warn":
                warnings.append(msg)
        
        return ValidationResult(
            table_id=table_config.id,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_columns=missing,
            extra_columns=extra,
        )
```

#### Acceptance Criteria

- [ ] **AC-M3-001**: Missing stable columns detected
- [ ] **AC-M3-002**: `stable_columns_mode: warn` logs warning but continues
- [ ] **AC-M3-003**: `stable_columns_mode: error` raises exception
- [ ] **AC-M3-004**: `stable_columns_subset: true` allows extra columns
- [ ] **AC-M3-005**: `stable_columns_subset: false` rejects extra columns
- [ ] **AC-M3-006**: Validation results aggregated per table

---

### M4: Transform Pipeline

**Goal**: Implement normalization and column transformations.

#### Files to Create

| File | Purpose |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/transform_pipeline.py` | Transform pipeline |
| `tests/unit/dat/profiles/test_transform_pipeline.py` | Unit tests |

#### Implementation Details

**TransformPipeline** (`transform_pipeline.py`):
```python
class TransformPipeline:
    """Applies normalization and column transformations."""
    
    def apply_normalization(
        self,
        df: pl.DataFrame,
        profile: DATProfile,
    ) -> pl.DataFrame:
        """Apply normalization rules from profile."""
        # 1. Replace NaN values
        if profile.nan_values:
            for col in df.columns:
                if df[col].dtype == pl.Utf8:
                    df = df.with_columns(
                        pl.when(pl.col(col).is_in(profile.nan_values))
                        .then(None)
                        .otherwise(pl.col(col))
                        .alias(col)
                    )
        
        # 2. Numeric coercion
        if profile.numeric_coercion:
            for col in df.columns:
                if df[col].dtype == pl.Utf8:
                    # Try to convert to numeric
                    try:
                        df = df.with_columns(
                            pl.col(col).cast(pl.Float64, strict=False).alias(col)
                        )
                    except:
                        pass  # Keep as string
        
        return df
    
    def apply_column_transforms(
        self,
        df: pl.DataFrame,
        transforms: list[ColumnTransform],
    ) -> pl.DataFrame:
        """Apply column-level transformations."""
        for transform in transforms:
            if transform.transform == "rename":
                df = df.rename({transform.source: transform.target})
            elif transform.transform == "unit_convert":
                factor = transform.args.get("factor", 1)
                df = df.with_columns(
                    (pl.col(transform.source) * factor).alias(transform.target)
                )
            elif transform.transform == "calculated":
                # Use polars expression evaluation
                expr = transform.args.get("expression", "")
                # Parse and evaluate expression...
        return df
```

#### Acceptance Criteria

- [ ] **AC-M4-001**: NaN values from profile are replaced with null
- [ ] **AC-M4-002**: Numeric coercion attempts string → float conversion
- [ ] **AC-M4-003**: Column renames are applied
- [ ] **AC-M4-004**: Unit conversions are applied with correct factors
- [ ] **AC-M4-005**: Calculated columns are added

---

### M5: UI Integration

**Goal**: Connect profile to frontend for table selection and preview.

#### Files to Modify

| File | Changes |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/api/routes.py` | Add profile-based endpoints |
| `apps/data_aggregator/frontend/src/components/stages/TableSelectionPanel.tsx` | Use profile tables |
| `apps/data_aggregator/frontend/src/components/stages/PreviewPanel.tsx` | Show profile-extracted preview |

#### API Endpoints to Add

```python
# GET /api/dat/profiles/{profile_id}/tables
# Returns list of available tables from profile

# GET /api/dat/runs/{run_id}/profile-preview
# Returns preview of profile-extracted data

# POST /api/dat/runs/{run_id}/stages/parse/lock
# Body: { selected_tables: ["run_summary", "cd_by_site"] }
# Returns extracted data using ProfileExecutor
```

#### Frontend Changes

**TableSelectionPanel.tsx**:
```typescript
// Fetch tables from profile instead of hardcoded list
const { data: profileTables } = useQuery({
  queryKey: ['profile-tables', profileId],
  queryFn: () => fetch(`/api/dat/profiles/${profileId}/tables`).then(r => r.json())
});

// Group tables by level (run, image) per ui.table_selection.group_by_level
// Apply default selections per ui.table_selection.default_selected
```

#### Acceptance Criteria

- [ ] **AC-M5-001**: Table selection UI shows tables from profile
- [ ] **AC-M5-002**: Tables grouped by level (run, image)
- [ ] **AC-M5-003**: Default selections applied from `ui.table_selection.default_selected`
- [ ] **AC-M5-004**: Preview shows profile-extracted data (not raw)
- [ ] **AC-M5-005**: Preview respects `ui.preview.max_rows` limit

---

### M6: Aggregation & Join Outputs

**Goal**: Implement output aggregations and joins from profile.

#### Files to Create

| File | Purpose |
|------|---------|
| `apps/data_aggregator/backend/src/dat_aggregation/profiles/output_builder.py` | Output aggregation/joins |
| `tests/unit/dat/profiles/test_output_builder.py` | Unit tests |

#### Implementation Details

**OutputBuilder** (`output_builder.py`):
```python
class OutputBuilder:
    """Builds final outputs from extracted tables per profile config."""
    
    def build_outputs(
        self,
        extracted_tables: dict[str, pl.DataFrame],
        profile: DATProfile,
        selected_outputs: list[str] | None = None,
    ) -> dict[str, pl.DataFrame]:
        """Build final output DataFrames."""
        outputs = {}
        
        # Process default outputs
        for output_config in profile.default_outputs:
            if selected_outputs and output_config.id not in selected_outputs:
                continue
            df = self._build_output(output_config, extracted_tables)
            outputs[output_config.id] = df
        
        # Process optional outputs
        for output_config in profile.optional_outputs:
            if selected_outputs and output_config.id not in selected_outputs:
                continue
            df = self._build_output(output_config, extracted_tables)
            outputs[output_config.id] = df
        
        return outputs
    
    def _build_output(
        self,
        config: OutputConfig,
        tables: dict[str, pl.DataFrame],
    ) -> pl.DataFrame:
        """Build single output by combining specified tables."""
        dfs = []
        for table_id in config.from_tables:
            if table_id in tables:
                dfs.append(tables[table_id])
        
        if not dfs:
            return pl.DataFrame()
        
        # Concatenate tables
        return pl.concat(dfs, how="diagonal")
    
    def apply_aggregation(
        self,
        df: pl.DataFrame,
        agg_config: AggregationConfig,
    ) -> pl.DataFrame:
        """Apply aggregation to DataFrame."""
        return df.group_by(agg_config.group_by).agg([
            getattr(pl.col(col), agg_func)()
            for col, agg_func in agg_config.aggregations.items()
        ])
```

#### Acceptance Criteria

- [ ] **AC-M6-001**: Default outputs include specified tables
- [ ] **AC-M6-002**: Optional outputs only included when selected
- [ ] **AC-M6-003**: `include_context: true` adds context columns
- [ ] **AC-M6-004**: Aggregations apply correct functions
- [ ] **AC-M6-005**: Joins combine tables on specified keys

---

## Implementation Schedule

| Milestone | Estimated Effort | Dependencies | Priority |
|-----------|-----------------|--------------|----------|
| **M1**: ProfileExecutor Core | 3-4 days | None | ⭐ CRITICAL |
| **M2**: Context Auto-Extraction | 2 days | M1 | HIGH |
| **M3**: Validation Engine | 1-2 days | M1 | HIGH |
| **M4**: Transform Pipeline | 2 days | M1, M3 | MEDIUM |
| **M5**: UI Integration | 2-3 days | M1, M2 | MEDIUM |
| **M6**: Aggregation & Joins | 1-2 days | M1 | LOW |

**Total Estimated Effort**: 11-15 days

---

## Dependencies

```
M1 (ProfileExecutor) ────┬──── M2 (Context)
                         │
                         ├──── M3 (Validation)
                         │
                         ├──── M4 (Transforms) ← M3
                         │
                         ├──── M5 (UI) ← M2
                         │
                         └──── M6 (Outputs)
```

---

## Testing Strategy

### Unit Tests

Each milestone has dedicated unit tests:
- `tests/unit/dat/profiles/test_profile_executor.py`
- `tests/unit/dat/profiles/strategies/test_*.py`
- `tests/unit/dat/profiles/test_context_extractor.py`
- `tests/unit/dat/profiles/test_validation_engine.py`
- `tests/unit/dat/profiles/test_transform_pipeline.py`
- `tests/unit/dat/profiles/test_output_builder.py`

### Integration Tests

```python
# tests/integration/dat/test_profile_extraction_e2e.py

async def test_full_profile_extraction():
    """End-to-end test: Load profile → Execute → Validate → Export."""
    profile = load_profile("cdsem_metrology_profile.yaml")
    executor = ProfileExecutor()
    
    results = await executor.execute(
        profile=profile,
        files=[Path("tests/fixtures/cdsem_sample.json")],
        context={},
    )
    
    # Verify all expected tables extracted
    assert "run_summary" in results
    assert "run_statistics" in results
    assert "cd_by_site" in results
    
    # Verify flat_object strategy
    assert len(results["run_summary"]) == 1  # Single row
    assert "mean_cd" in results["run_summary"].columns
    
    # Verify headers_data strategy
    assert len(results["run_statistics"]) == 2  # Two parameters
    assert results["run_statistics"]["parameter"].to_list() == ["cd_left", "cd_right"]
    
    # Verify repeat_over strategy
    assert len(results["cd_by_site"]) == 4  # 2 sites × 2 rows each
    assert "site_id" in results["cd_by_site"].columns  # Injected field
```

### Regression Tests

Baseline outputs captured for:
- `cdsem_sample.json` → expected DataFrames per table
- Validates profile changes don't break extraction

---

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| JSONPath complexity | HIGH | Start with simple paths, add complex patterns incrementally |
| Performance on large files | MEDIUM | Use streaming (ADR-0040), chunk processing |
| Backward compatibility | HIGH | Legacy path preserved when no profile specified |
| Profile schema evolution | MEDIUM | Forward-compatible schema (ignore unknown fields) |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Profile feature coverage | 100% of YAML features implemented |
| Test coverage | >80% for profile module |
| Parse stage latency | <2x current (profile overhead acceptable) |
| Context auto-extraction rate | >90% of fields auto-populated |

---

## Next Steps

1. **Approve this plan** - Review milestones and acceptance criteria
2. **Start M1** - ProfileExecutor is critical path
3. **Create test fixtures** - Sample JSON files for testing
4. **Implement in order** - M1 → M2 → M3 → M4 → M5 → M6

---

*Implementation plan prepared for Profile-Driven ETL Architecture*
*Per ADR-0011, SPEC-DAT-0011, SPEC-DAT-0012*
