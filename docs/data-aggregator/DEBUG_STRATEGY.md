# DAT Tool - Comprehensive Debug Strategy

## Root Cause Analysis: "Create New Run" Button Not Working

### Issue Identified
**API Path Mismatch** between frontend and backend:
- **Frontend** was calling: `/api/dat/runs`
- **Backend** was expecting: `/api/v1/runs`

### Files Fixed
All API endpoint paths have been corrected from `/api/dat/` to `/api/v1/`:
- `useRun.ts` - Run creation and fetching
- `SelectionPanel.tsx` - File selection endpoints
- `ContextPanel.tsx` - Profile and context endpoints
- `TableAvailabilityPanel.tsx` - Table scanning endpoints
- `TableSelectionPanel.tsx` - Table selection endpoints
- `PreviewPanel.tsx` - Preview data endpoints
- `ParsePanel.tsx` - Parse progress and control endpoints
- `ExportPanel.tsx` - Export summary and execution endpoints

---

## Deterministic Debug Strategy

### Phase 1: Backend Health Check

#### 1.1 Verify Backend is Running
```bash
# Check if backend is accessible
curl http://localhost:8001/health

# Expected response:
# {"status":"healthy","tool":"dat","version":"0.1.0"}
```

#### 1.2 Verify API Routes
```bash
# Check OpenAPI docs are accessible
curl http://localhost:8001/docs
# Should return HTML for Swagger UI

# Test run creation endpoint directly
curl -X POST http://localhost:8001/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{}'

# Expected: JSON response with run_id, name, created_at
```

#### 1.3 Backend Logs
```bash
# Start backend with visible logs
cd apps/data_aggregator/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Watch for:
# - Import errors
# - Route registration
# - Request/response logs
```

---

### Phase 2: Frontend Health Check

#### 2.1 Verify Frontend is Running
```bash
cd apps/data_aggregator/frontend
npm run dev

# Check console output for:
# - Vite server starting on http://localhost:5173
# - No compilation errors
```

#### 2.2 Browser Developer Tools
Open browser DevTools (F12) and check:

**Console Tab:**
- No JavaScript errors
- React Query initialization messages
- No CORS errors

**Network Tab:**
- When clicking "Create New Run", look for:
  - POST request to `/api/v1/runs`
  - Status code 200 (success)
  - Response body with run_id

**React DevTools (if installed):**
- Check component state
- Verify `runId` state updates after button click

---

### Phase 3: End-to-End Workflow Testing

#### 3.1 Create New Run
**Test:**
1. Open DAT tool in browser
2. Click "Create New Run" button
3. Verify loading spinner appears
4. Verify stage panel appears with "File Selection" active

**Debug if fails:**
- Check Network tab for failed requests
- Check Console for React Query errors
- Verify `handleCreateRun` function in App.tsx is called
- Check if `setRunId` is executed with valid ID

#### 3.2 File Selection Stage
**Test:**
1. Enter a valid folder path
2. Click "Scan" button
3. Verify files are discovered and listed
4. Select files and click "Continue"

**Debug if fails:**
- Check API endpoint: `POST /api/v1/runs/{runId}/stages/selection/lock`
- Verify backend has filesystem access permissions
- Check if selection stage can read file extensions

**Backend verification:**
```bash
# Test file discovery directly
python -c "
from apps.data_aggregator.backend.src.dat_aggregation.stages import discover_files
from pathlib import Path
files = discover_files([Path('/path/to/test/data')], recursive=True)
print(f'Found {len(files)} files')
for f in files[:5]:
    print(f'  {f.name}: {f.tables}')
"
```

#### 3.3 Context Stage
**Test:**
1. Verify profiles are loaded
2. Select a profile
3. Select aggregation levels
4. Click "Continue"

**Debug if fails:**
- Check API: `GET /api/v1/profiles`
- Verify profile YAML files exist
- Check profile loader imports

**Backend verification:**
```python
# Test profile loading
from apps.data_aggregator.backend.src.dat_aggregation.profiles import load_profile
profile = load_profile('path/to/profile.yaml')
print(f'Loaded profile: {profile.title}')
```

#### 3.4 Table Availability Stage
**Test:**
1. Verify tables are scanned automatically
2. Check available/unavailable status
3. Click "Continue"

**Debug if fails:**
- Check API: `GET /api/v1/runs/{runId}/stages/table_availability/scan`
- Verify adapter can read file formats
- Check for table parsing errors in logs

#### 3.5 Table Selection Stage
**Test:**
1. Verify available tables are listed
2. Select tables to include
3. Click "Continue"

**Debug if fails:**
- Check forward gating (requires table_availability locked)
- Verify table metadata is present

#### 3.6 Preview Stage
**Test:**
1. Verify preview data loads
2. Check column names and sample rows
3. Click "Continue to Parse"

**Debug if fails:**
- Check API: `GET /api/v1/runs/{runId}/stages/preview/data`
- Verify parse stage has not been locked yet
- Check if preview sampling works

#### 3.7 Parse Stage
**Test:**
1. Click "Start Parsing"
2. Verify progress bar updates
3. Wait for completion
4. Click "Continue to Export"

**Debug if fails:**
- Check API: `POST /api/v1/runs/{runId}/stages/parse/start`
- Monitor progress endpoint polling
- Check workspace directory for parquet files
- Verify cancellation token works

**Backend verification:**
```bash
# Check workspace structure
ls -la workspace/tools/dat/runs/
# Should show run directories with parquet files
```

#### 3.8 Export Stage
**Test:**
1. Verify summary statistics display
2. Enter dataset name
3. Click "Export DataSet"
4. Verify success message and dataset ID

**Debug if fails:**
- Check API: `POST /api/v1/runs/{runId}/stages/export/execute`
- Verify ArtifactStore has write permissions
- Check dataset manifest creation

---

### Phase 4: State Machine Testing

#### 4.1 Forward Gating Rules
Test that stages enforce dependencies:
- Context requires Selection locked
- Parse requires Table Selection locked
- Export requires Parse locked and completed

**Test:**
Try to lock stages out of order via API:
```bash
# Should fail - parse without table selection
curl -X POST http://localhost:8001/api/v1/runs/{runId}/stages/parse/lock

# Expected: 400 error with reason
```

#### 4.2 Cascade Unlocking
Test that unlocking cascades correctly:
- Unlock Selection → should unlock all downstream stages
- Unlock Parse → should unlock Export
- Context and Preview should NOT cascade

**Test via UI:**
1. Complete workflow to Parse stage
2. Click unlock on Selection stage
3. Verify Parse and Export reset to unlocked

#### 4.3 Idempotent Stage Locking
Test deterministic stage IDs (ADR-0004):
```bash
# Lock selection twice with same inputs
curl -X POST http://localhost:8001/api/v1/runs/{runId}/stages/selection/lock \
  -H "Content-Type: application/json" \
  -d '{"source_paths":["/same/path"]}'

# Save stage_id from response

curl -X POST http://localhost:8001/api/v1/runs/{runId}/stages/selection/lock \
  -H "Content-Type: application/json" \
  -d '{"source_paths":["/same/path"]}'

# Verify stage_id is identical (deterministic)
```

---

### Phase 5: Integration Testing

#### 5.1 Full Workflow with Example Data
```bash
# Run complete workflow test
cd tests/dat
pytest test_stages.py::TestParseWithExampleData -v

# Verify all stages work with CD-SEM example data
```

#### 5.2 Profile-Driven Extraction
Test that profiles correctly define extraction:
1. Load CD-SEM profile
2. Process example JSON files
3. Verify tables match profile definitions
4. Check context extraction from filenames

#### 5.3 Error Handling
Test graceful degradation:
- Invalid file paths
- Corrupted data files
- Network interruptions
- Cancellation during parse
- Insufficient permissions

---

### Phase 6: Performance Testing

#### 6.1 Large File Handling
Test with:
- Files > 100MB
- 1000+ rows
- 50+ columns
- Multiple files simultaneously

#### 6.2 Progress Reporting
Verify progress updates correctly:
- Callback frequency
- Percentage accuracy
- File-by-file tracking

#### 6.3 Memory Usage
Monitor during large parse operations:
```bash
# Monitor backend process
top -p $(pgrep -f "uvicorn main:app")

# Check for memory leaks during repeated operations
```

---

### Phase 7: Cross-Browser Testing

Test in multiple browsers:
- Chrome/Edge (Chromium)
- Firefox
- Safari (if on macOS)

Verify:
- Fetch API compatibility
- React Query behavior
- CSS rendering
- File input handling

---

## Common Issues & Solutions

### Issue: Button Click Does Nothing
**Symptoms:** No network request, no error
**Causes:**
1. API path mismatch ✓ FIXED
2. CORS configuration issue
3. React event handler not attached
4. Button disabled state logic error

**Debug:**
```javascript
// Add console.log in App.tsx handleCreateRun
const handleCreateRun = async () => {
  console.log('Create run clicked') // Should appear
  const newRun = await createRun()
  console.log('Run created:', newRun) // Should show run data
  setRunId(newRun.run_id)
}
```

### Issue: CORS Errors
**Symptoms:** Network request fails with CORS error
**Solution:**
```python
# In backend main.py, verify:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Or specific frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: 404 Not Found
**Symptoms:** API returns 404
**Causes:**
1. Wrong API path (fixed)
2. Router not registered
3. Backend not running

**Verify router:**
```python
# In main.py, check:
app.include_router(router, prefix="/api", tags=["dat"])
```

### Issue: Stage Won't Lock
**Symptoms:** Lock request returns 400
**Causes:**
1. Forward gating rules not satisfied
2. Required stage not completed
3. Invalid inputs

**Check state machine:**
```bash
# Get all stage statuses
curl http://localhost:8001/api/v1/runs/{runId}

# Check specific stage
curl http://localhost:8001/api/v1/runs/{runId}/stages/selection
```

### Issue: Data Not Parsing
**Symptoms:** Parse fails or returns empty
**Causes:**
1. Adapter not handling file format
2. Profile extraction path incorrect
3. Column mapping issues

**Test adapter directly:**
```python
from apps.data_aggregator.backend.src.dat_aggregation.adapters import AdapterFactory
from pathlib import Path

file_path = Path('/path/to/test.json')
adapter = AdapterFactory.get_adapter(file_path)
print(f'Using adapter: {adapter.__class__.__name__}')

tables = adapter.get_tables(file_path)
print(f'Found tables: {tables}')

df = adapter.read(file_path, json_path='$.data')
print(df)
```

---

## Automated Testing Commands

```bash
# Backend tests (108 tests)
python -m pytest tests/dat/ -v

# Test specific components
python -m pytest tests/dat/test_profiles.py -v     # Profile loading
python -m pytest tests/dat/test_adapters.py -v     # File adapters
python -m pytest tests/dat/test_stages.py -v       # Stage operations
python -m pytest tests/dat/test_state_machine.py -v # FSM logic
python -m pytest tests/dat/test_api.py -v          # API endpoints

# Frontend tests (once dependencies installed)
cd apps/data_aggregator/frontend
npm test

# Coverage report
python -m pytest tests/dat/ --cov --cov-report=html
```

---

## Monitoring & Logging

### Backend Logging
```python
# Enable debug logging in main.py
logging.basicConfig(
    level=logging.DEBUG,  # Change from INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

### Frontend Logging
```typescript
// Add React Query DevTools
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

function App() {
  return (
    <>
      {/* ... app content ... */}
      <ReactQueryDevtools initialIsOpen={false} />
    </>
  )
}
```

### Network Monitoring
Use browser DevTools Network tab with:
- Preserve log enabled
- Filter: Fetch/XHR
- Headers shown
- Response preview

---

## Success Criteria

### ✓ Create New Run Works
- Button click triggers network request
- Backend returns 200 with valid run_id
- UI transitions to File Selection stage

### ✓ All Stages Function
- Each stage can be locked
- Forward gating enforced
- Cascade unlocking works
- Stage IDs are deterministic

### ✓ Data Processing Works
- Files discovered correctly
- Tables extracted per profile
- Parse completes successfully
- Export creates valid DataSet

### ✓ Error Handling Works
- Invalid inputs rejected gracefully
- Network errors shown to user
- Cancellation works correctly
- Logs provide debugging info

---

## Next Steps After Verification

1. **Install frontend dependencies:**
   ```bash
   cd apps/data_aggregator/frontend
   npm install
   ```

2. **Start both services:**
   ```bash
   # Terminal 1 - Backend
   cd apps/data_aggregator/backend
   python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload

   # Terminal 2 - Frontend
   cd apps/data_aggregator/frontend
   npm run dev
   ```

3. **Test the fix:**
   - Open http://localhost:5173
   - Click "Create New Run"
   - Verify it works!

4. **Run test suite:**
   ```bash
   python -m pytest tests/dat/ -v
   ```
