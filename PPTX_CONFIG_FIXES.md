# PPTX Generator Config Path Fixes

## Issue
The Configuration dropdown in the PPTX Generator UI was empty because:
1. Config files were missing (not copied from old repo)
2. Hardcoded relative paths didn't work in the new monorepo structure

## Root Causes

### 1. Missing Config Files
The `config/` directory and its YAML files were not migrated from the old PowerPointGenerator repo.

### 2. Hardcoded Relative Paths
Multiple files used hardcoded relative paths that assumed the old repo structure:
- `domain_config_service.py` - Lines 36-38
- `config_defaults.py` - Lines 36, 40, 286, 308, 354, 386, 446

## Fixes Applied

### 1. Created Config Directory ✅
**Location:** `apps/pptx_generator/config/`

**Files Copied:**
- `example_config_production.yaml` - Production-ready configuration
- `custom_config.yaml` - Custom configuration variant

### 2. Fixed `domain_config_service.py` ✅
**File:** `apps/pptx_generator/backend/core/domain_config_service.py`

**Changes:**
```python
# OLD - Hardcoded relative paths
candidates = [
    Path("config/example_config_production.yaml"),
    Path("../config/example_config_production.yaml"),
    Path(__file__).parent.parent.parent / "config" / "example_config_production.yaml",
]

# NEW - Absolute path resolution
app_root = Path(__file__).parent.parent.parent.resolve()

candidates = [
    app_root / "config" / "example_config_production.yaml",
    app_root / "config" / "custom_config.yaml",
    Path("config/example_config_production.yaml"),
    Path("../config/example_config_production.yaml"),
]
```

### 3. Fixed `config_defaults.py` ✅
**File:** `apps/pptx_generator/backend/api/config_defaults.py`

**Changes:**
- Added `_get_config_dir()` helper function:
```python
def _get_config_dir() -> Path:
    """Get the absolute path to the config directory."""
    app_root = Path(__file__).parent.parent.parent.resolve()
    return app_root / "config"
```

- Updated all functions to use `_get_config_dir()`:
  - `get_config_defaults()` - Line 43
  - `save_config_mappings()` - Line 295
  - `list_config_files()` - Line 363
  - `load_config_file()` - Line 396
  - `save_full_config()` - Line 456

### 4. Fixed Frontend API Base URL ✅
**File:** `apps/pptx_generator/frontend/src/lib/api.ts`

**Change:**
```typescript
// OLD - Absolute URL bypassing proxy
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// NEW - Relative URL using proxy
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'
```

## Files Modified

1. ✅ `apps/pptx_generator/backend/core/domain_config_service.py`
2. ✅ `apps/pptx_generator/backend/api/config_defaults.py`
3. ✅ `apps/pptx_generator/frontend/src/lib/api.ts`

## Files Created

1. ✅ `apps/pptx_generator/config/example_config_production.yaml`
2. ✅ `apps/pptx_generator/config/custom_config.yaml`

## Path Resolution Strategy

All config-related code now uses this pattern:
```python
# Get absolute path to app root
app_root = Path(__file__).parent.parent.parent.resolve()

# Build config path
config_dir = app_root / "config"
config_file = config_dir / "example_config_production.yaml"
```

This ensures paths work correctly regardless of:
- Current working directory
- How the application is launched
- Monorepo vs standalone structure

## API Endpoints Affected

All these endpoints now correctly find config files:

- `GET /api/pptx/api/v1/config/defaults` - Load test defaults
- `GET /api/pptx/api/v1/config/list` - List available configs
- `GET /api/pptx/api/v1/config/load/{filename}` - Load specific config
- `POST /api/pptx/api/v1/config/save` - Save config mappings
- `PUT /api/pptx/api/v1/config/save-full` - Save full config

## Testing

After restarting the services, the Configuration dropdown should now:
1. Display both config files (example_config_production.yaml, custom_config.yaml)
2. Allow selection and loading of configurations
3. Properly apply defaults to projects

## Verification Steps

1. Start services: `.\start.ps1 --with-frontend`
2. Navigate to PPTX Generator
3. Create a new project
4. Check Configuration dropdown - should show 2 files
5. Select a config file - should load successfully
6. Create project - should work without network errors

## Related Fixes

This investigation also revealed and fixed:
- Frontend network error (API base URL issue)
- Gateway health endpoint routing
- Cross-tool dataset/pipeline endpoint paths

All fixes are documented in:
- `FIXES_APPLIED.md` - Endpoint fixes
- `DEBUGGING_CHECKLIST.md` - Test results
- `TOOL_ALIGNMENT.md` - Port alignment
