# Troubleshooting Guide

> **Common issues and solutions for PowerPoint Generator**

---

## Table of Contents

1. [Backend Issues](#backend-issues)
2. [Frontend Issues](#frontend-issues)
3. [Template Parsing Issues](#template-parsing-issues)
4. [Data Upload Issues](#data-upload-issues)
5. [Mapping Issues](#mapping-issues)
6. [Validation Issues](#validation-issues)
7. [Generation Issues](#generation-issues)

---

## Backend Issues

### Server Won't Start

**Symptom:** Gateway or PPTX backend fails to start.

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: No module named 'apps'` | Not in project root | `cd` to engineering-tools root directory |
| `ModuleNotFoundError: No module named 'fastapi'` | Dependencies not installed | `pip install -r requirements.txt` or run `setup.ps1` |
| `Address already in use` | Port 8000 in use | Stop other process or use different port |

**Debug Steps:**

```bash
# 1. Verify virtual environment is active
which python  # Should show .venv path

# 2. Reinstall dependencies
pip install -e .

# 3. Check Python version (requires 3.11+)
python --version

# 4. Start gateway
python -m gateway.main
```

### API Returns 500 Error

**Symptom:** Endpoints return "Internal server error".

**Debug Steps:**

```bash
# 1. Check server logs (run with debug)
python -m gateway.main

# 2. Test health endpoint
curl http://localhost:8000/api/health

# 3. Test PPTX endpoint
curl http://localhost:8000/api/pptx/api/v1/health
```

### CORS Errors

**Symptom:** Frontend gets "Access-Control-Allow-Origin" errors.

**Solution:** The gateway configures CORS for localhost:3000 and localhost:5173. If using different ports, update `gateway/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5175",  # PPTX frontend
    ],
    ...
)
```

---

## Frontend Issues

### Build Fails

**Symptom:** `npm run build` shows TypeScript errors.

**Debug Steps:**

```bash
# 1. Navigate to PPTX frontend
cd apps/pptx_generator/frontend

# 2. Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# 3. Install types
npm install -D @types/node

# 4. Check for type errors
npx tsc --noEmit
```

### API Connection Failed

**Symptom:** Frontend shows network errors.

**Debug Steps:**

1. Verify gateway is running at http://localhost:8000
2. Check browser DevTools Network tab for failed requests
3. Verify the API proxy in `vite.config.ts` is configured correctly

### PPTX App Not Loading in Homepage

**Symptom:** Blank iframe when navigating to PPTX Generator from homepage.

**Solution:** Ensure the PPTX frontend is running on port 5175:

```bash
cd apps/pptx_generator/frontend
npm run dev
# Should start on http://localhost:5175
```

---

## Template Parsing Issues

### "Parse Failed" Error

**Symptom:** Template upload succeeds but parsing fails.

| Cause | Solution |
|-------|----------|
| No named shapes | Add shape names in PowerPoint (Selection Pane) |
| Invalid shape names | Follow naming convention |
| Corrupted PPTX | Re-save template in PowerPoint |
| Password protected | Remove password protection |

**Debug Steps:**

1. Open template in PowerPoint
2. View → Selection Pane
3. Verify shapes have descriptive names
4. Save and re-upload

### "No Shapes Found"

**Symptom:** Parser finds 0 shapes.

**Cause:** Shapes aren't named or use default names like "Rectangle 1".

**Solution:**

1. Open PowerPoint template
2. Select each data-bound shape
3. In Selection Pane, rename to follow convention

---

## Data Upload Issues

### "Invalid File Format"

**Symptom:** Data file rejected on upload.

| File Type | Allowed Extensions | Notes |
|-----------|-------------------|-------|
| CSV | `.csv` | UTF-8 encoding recommended |
| Excel | `.xlsx`, `.xls` | First sheet used |

### "No Columns Found"

**Symptom:** Data file uploads but shows 0 columns.

| Cause | Solution |
|-------|----------|
| Empty first row | Add headers to first row |
| Wrong delimiter | Use comma (,) for CSV |
| BOM character | Save as UTF-8 without BOM |

### Loading from DataSet Fails

**Symptom:** "Load from DataSet" shows error.

**Debug Steps:**

1. Verify the DataSet exists in the artifact store
2. Check gateway logs for detailed error
3. Ensure the DataSet has valid parquet data

---

## Mapping Issues

### No Suggestions Generated

**Symptom:** Mapping step shows no auto-suggestions.

| Cause | Solution |
|-------|----------|
| Column names don't match | Rename columns to match template requirements |
| Low similarity score | Use more descriptive column names |
| DRM not extracted | Re-upload template to regenerate DRM |

### "Can't Save Mappings"

**Symptom:** Save button disabled or returns error.

| Cause | Solution |
|-------|----------|
| No mappings configured | Configure at least one mapping |
| Required field empty | Fill in all required fields |
| Session expired | Refresh page and retry |

---

## Validation Issues

### Red Bar: Required Context

**Symptom:** Context bar shows red/incomplete.

| Issue | Solution |
|-------|----------|
| Unmapped context | Add mapping in Context Mapping step |
| Missing data column | Add column to data file or use Default source |
| Regex not matching | Test regex pattern against data |

### Red Bar: Required Metrics

**Symptom:** Metrics bar shows red/incomplete.

| Issue | Solution |
|-------|----------|
| Unmapped metric | Add mapping in Metrics Mapping step |
| Non-numeric column | Select different column or clean data |
| Wrong aggregation | Change aggregation type |

---

## Generation Issues

### "Generation Failed"

**Symptom:** Build Plan succeeds but generation fails.

**Debug Steps:**

1. Check server logs for stack trace
2. Verify all four bars were green
3. Check output directory permissions

### Output File Empty or Corrupted

**Symptom:** Generated PPTX can't be opened.

| Cause | Solution |
|-------|----------|
| Template corruption | Re-upload original template |
| Renderer error | Check logs for specific shape errors |
| Disk full | Free disk space |

---

## Getting More Help

### Log Locations

| Component | Log Location |
|-----------|--------------|
| Gateway | Terminal running `python -m gateway.main` |
| PPTX Backend | Gateway logs (mounted at /api/pptx) |
| Frontend | Browser DevTools Console |

### Diagnostic Commands

```bash
# Gateway health
curl http://localhost:8000/api/health

# PPTX health
curl http://localhost:8000/api/pptx/api/v1/health

# Check Python environment
python --version
pip list | grep -E "fastapi|pydantic|uvicorn"

# Check Node environment
node --version
npm list
```
