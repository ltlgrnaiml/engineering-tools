# Tier 4: Phase 2 Homepage + PPTX Migration - Implementation Instructions

**Document Type:** Step-by-Step Implementation Guide  
**Audience:** AI Coding Assistants, Junior Developers  
**Status:** ⚠️ MOSTLY COMPLETE (some pages pending)  
**Last Updated:** 2025-01-26

---

## Phase Overview

Phase 2 creates the Homepage frontend and migrates the existing PowerPointGenerator to the monorepo structure, updating it to use shared contracts and DataSet inputs.

**Duration:** Week 2-3  
**Dependencies:** Phase 1 complete

---

## Step 2.1: Create Homepage Frontend Structure ✅

**Goal:** Set up React + Vite project for Homepage

**Location:** `apps/homepage/frontend/`

> **Implementation Status:** Complete. Frontend structure exists with Vite, React, TailwindCSS, and react-query.

**Commands:**
```bash
cd /Users/kalepook_ai/Coding/engineering-tools/apps/homepage/frontend

# Initialize Vite project
npm create vite@latest . -- --template react-ts

# Install dependencies
npm install react-router-dom @tanstack/react-query
npm install -D tailwindcss postcss autoprefixer
npm install @radix-ui/react-dialog @radix-ui/react-dropdown-menu

# Initialize Tailwind
npx tailwindcss init -p
```

**Files to create:**

1. `tailwind.config.js` - Tailwind configuration
2. `src/main.tsx` - Entry point
3. `src/App.tsx` - Root component
4. `src/routes.tsx` - Route definitions

**tailwind.config.js:**
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

**src/routes.tsx:**
```typescript
import { createBrowserRouter } from "react-router-dom";
import { MainLayout } from "./components/layout/MainLayout";
import { HomePage } from "./pages/HomePage";
import { DataSetsPage } from "./pages/DataSetsPage";
import { PipelinesPage } from "./pages/PipelinesPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "datasets", element: <DataSetsPage /> },
      { path: "datasets/:id", element: <DataSetDetailsPage /> },
      { path: "pipelines", element: <PipelinesPage /> },
      { path: "pipelines/new", element: <PipelineBuilderPage /> },
      { path: "pipelines/:id", element: <PipelineDetailsPage /> },
    ],
  },
]);
```

---

## Step 2.2: Create Homepage Components ✅

**Goal:** Implement core UI components

> **Implementation Status:** Complete. Components exist in `src/components/` with a flatter structure than originally planned (Layout.tsx, HealthIndicator.tsx instead of nested folders).

### 2.2.1: MainLayout Component

**File:** `src/components/layout/MainLayout.tsx`

```typescript
import { Outlet } from "react-router-dom";
import { Header } from "./Header";

export function MainLayout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}
```

### 2.2.2: Header Component

**File:** `src/components/layout/Header.tsx`

```typescript
import { Link } from "react-router-dom";
import { useHealth } from "../../hooks/useHealth";
import { HealthIndicator } from "../health/HealthIndicator";

export function Header() {
  const { data: health } = useHealth();
  
  return (
    <header className="bg-white shadow">
      <div className="container mx-auto px-4 py-4 flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">
          Engineering Tools Platform
        </Link>
        <nav className="flex gap-4 items-center">
          <Link to="/datasets" className="hover:text-blue-600">DataSets</Link>
          <Link to="/pipelines" className="hover:text-blue-600">Pipelines</Link>
          <HealthIndicator status={health?.status} />
        </nav>
      </div>
    </header>
  );
}
```

### 2.2.3: ToolCard Component

**File:** `src/components/tools/ToolCard.tsx`

```typescript
import { useNavigate } from "react-router-dom";

interface ToolCardProps {
  id: "dat" | "sov" | "pptx";
  name: string;
  description: string;
  status: "available" | "coming_soon" | "maintenance" | "error";
  path: string;
}

export function ToolCard({ id, name, description, status, path }: ToolCardProps) {
  const navigate = useNavigate();
  const isDisabled = status !== "available";
  
  const statusColors = {
    available: "bg-green-100 text-green-800",
    coming_soon: "bg-gray-100 text-gray-600",
    maintenance: "bg-yellow-100 text-yellow-800",
    error: "bg-red-100 text-red-800",
  };
  
  return (
    <div
      onClick={() => !isDisabled && navigate(path)}
      className={`
        p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow
        ${isDisabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
      `}
    >
      <div className="flex justify-between items-start mb-4">
        <h3 className="text-lg font-semibold">{name}</h3>
        <span className={`px-2 py-1 text-xs rounded ${statusColors[status]}`}>
          {status.replace("_", " ")}
        </span>
      </div>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}
```

### 2.2.4: HomePage Component

**File:** `src/pages/HomePage.tsx`

```typescript
import { ToolCard } from "../components/tools/ToolCard";
import { DataSetList } from "../components/datasets/DataSetList";
import { useHealth } from "../hooks/useHealth";

const TOOLS = [
  {
    id: "dat" as const,
    name: "Data Aggregator",
    description: "Extract and aggregate data from multiple sources",
    path: "/tools/dat",
  },
  {
    id: "sov" as const,
    name: "SOV Analyzer",
    description: "Source of Variation analysis (ANOVA)",
    path: "/tools/sov",
  },
  {
    id: "pptx" as const,
    name: "PowerPoint Generator",
    description: "Generate reports from templates",
    path: "/tools/pptx",
  },
];

export function HomePage() {
  const { data: health } = useHealth();
  
  return (
    <div className="space-y-8">
      <section>
        <h2 className="text-2xl font-bold mb-4">Tools</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {TOOLS.map(tool => (
            <ToolCard
              key={tool.id}
              {...tool}
              status={health?.tools?.[tool.id] || "coming_soon"}
            />
          ))}
        </div>
      </section>
      
      <section>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">Recent DataSets</h2>
          <a href="/datasets" className="text-blue-600 hover:underline">
            View All →
          </a>
        </div>
        <DataSetList limit={5} />
      </section>
    </div>
  );
}
```

---

## Step 2.3: Create Homepage Hooks ✅

**Goal:** Implement data fetching hooks

> **Implementation Status:** Complete. Hooks exist in `src/hooks/` (useHealth.ts, useDataSets.ts, usePipelines.ts).

### 2.3.1: useHealth Hook

**File:** `src/hooks/useHealth.ts`

```typescript
import { useQuery } from "@tanstack/react-query";

interface HealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  version: string;
  tools: {
    dat: "available" | "coming_soon" | "maintenance" | "error";
    sov: "available" | "coming_soon" | "maintenance" | "error";
    pptx: "available" | "coming_soon" | "maintenance" | "error";
  };
}

export function useHealth() {
  return useQuery<HealthResponse>({
    queryKey: ["health"],
    queryFn: async () => {
      const res = await fetch("/api/health");
      if (!res.ok) throw new Error("Health check failed");
      return res.json();
    },
    refetchInterval: 30000,
  });
}
```

### 2.3.2: useDataSets Hook

**File:** `src/hooks/useDataSets.ts`

```typescript
import { useQuery } from "@tanstack/react-query";

interface DataSetRef {
  dataset_id: string;
  name: string;
  created_at: string;
  created_by_tool: "dat" | "sov" | "pptx" | "manual";
  row_count: number;
  column_count: number;
  parent_count: number;
}

interface UseDataSetsOptions {
  tool?: string;
  limit?: number;
}

export function useDataSets(options?: UseDataSetsOptions) {
  return useQuery<DataSetRef[]>({
    queryKey: ["datasets", options],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (options?.tool) params.set("tool", options.tool);
      if (options?.limit) params.set("limit", String(options.limit));
      
      const res = await fetch(`/api/datasets/v1/?${params}`);
      if (!res.ok) throw new Error("Failed to fetch datasets");
      return res.json();
    },
  });
}
```

---

## Step 2.4: Migrate PowerPointGenerator ✅

**Goal:** Copy existing PPTX code to monorepo and update imports

> **Implementation Status:** Complete. PPTX backend exists at `apps/pptx_generator/backend/`.

### 2.4.1: Copy Backend

**Commands:**
```bash
# Copy backend
cp -r /Users/kalepook_ai/Coding/PowerPointGenerator/backend/* \
  /Users/kalepook_ai/Coding/engineering-tools/apps/pptx-generator/backend/

# Copy frontend
cp -r /Users/kalepook_ai/Coding/PowerPointGenerator/frontend/* \
  /Users/kalepook_ai/Coding/engineering-tools/apps/pptx-generator/frontend/

# Copy templates
cp -r /Users/kalepook_ai/Coding/PowerPointGenerator/templates/* \
  /Users/kalepook_ai/Coding/engineering-tools/apps/pptx-generator/templates/
```

### 2.4.2: Update Imports

**Files to modify:**

Search and replace in all Python files:

| Old Import | New Import |
|------------|------------|
| `from backend.models` | `from pptx_generator.models` |
| `from backend.services` | `from pptx_generator.services` |
| `from backend.api` | `from pptx_generator.api` |

### 2.4.3: Add DataSet Support

**File to create:** `apps/pptx-generator/backend/services/data_loader.py`

```python
"""DataSet loader for PPTX Generator.

Loads DataSets from shared artifact store for report generation.
"""
from typing import Any

import polars as pl

from shared.contracts.core.dataset import DataSetManifest
from shared.storage.artifact_store import ArtifactStore


async def load_datasets_for_report(
    dataset_ids: list[str],
) -> dict[str, tuple[pl.DataFrame, DataSetManifest]]:
    """Load multiple DataSets for report generation.
    
    Args:
        dataset_ids: List of DataSet IDs to load
        
    Returns:
        Dict mapping source tool (or ID) to (DataFrame, Manifest) tuple
    """
    store = ArtifactStore()
    result: dict[str, tuple[pl.DataFrame, DataSetManifest]] = {}
    
    for ds_id in dataset_ids:
        manifest = await store.get_manifest(ds_id)
        df = await store.read_dataset(ds_id)
        
        # Key by source tool for easy template access
        key = manifest.created_by_tool
        if key in result:
            key = f"{key}_{ds_id[:8]}"
        
        result[key] = (df, manifest)
    
    return result
```

### 2.4.4: Update API to Accept DataSets

**File to modify:** `apps/pptx-generator/backend/api/routes.py`

Add to run creation endpoint:

```python
from pptx_generator.services.data_loader import load_datasets_for_report

@router.post("/v1/runs")
async def create_run(
    input_datasets: list[str] | None = None,
    config_id: str | None = None,
    # ... existing params
):
    """Create a new PPTX generation run.
    
    Args:
        input_datasets: Optional list of DataSet IDs to use as input
        config_id: Optional config ID to load
    """
    run = await run_manager.create_run()
    
    if input_datasets:
        # Load DataSets from shared store
        datasets = await load_datasets_for_report(input_datasets)
        await run_manager.set_datasets(run.id, datasets)
    
    return run
```

---

## Step 2.5: Configure Vite Proxy

**Goal:** Proxy API requests to gateway during development

**File:** `apps/homepage/frontend/vite.config.ts`

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

---

## Step 2.6: Update Gateway to Mount PPTX

**File to modify:** `gateway/main.py`

Uncomment PPTX mounting:

```python
# Uncomment when PPTX is migrated
from apps.pptx_generator.backend.main import app as pptx_app
app.mount("/api/pptx", pptx_app)
```

---

## Validation Checklist

### Homepage

- [x] `npm run dev` starts without errors
- [x] Homepage displays tool cards
- [x] Health indicator shows status
- [x] DataSet list loads (empty is OK)
- [x] Navigation works
- [ ] DataSetDetailsPage implemented
- [ ] PipelineDetailsPage implemented

### PPTX Migration

- [x] PPTX backend starts standalone
- [x] Gateway mounts PPTX at `/api/pptx`
- [ ] PPTX frontend builds
- [ ] Existing PPTX tests pass
- [ ] DataSet input works (when datasets exist)

---

## Next Phase

Proceed to **Phase 3: Data Aggregator**

See: `phase-3-data-aggregator/PHASE3_INSTRUCTIONS.md`
