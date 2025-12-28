# Tier 2: Homepage Control & Navigation

**Document Type:** Integration Specification  
**Audience:** Senior Engineers  
**Last Updated:** 2025-01-26

---

## Overview

The Homepage serves as the central control point for the Engineering Tools Platform. It provides tool launching, DataSet browsing, and pipeline management.

---

## Homepage Responsibilities

1. **Tool Launcher** - Display available tools with status indicators
2. **DataSet Browser** - Show recent DataSets across all tools
3. **Pipeline Manager** - Create and monitor multi-tool pipelines
4. **Health Dashboard** - Display platform and tool health status

---

## Navigation Architecture

### URL Structure

```text
/                           # Homepage
/tools/dat                  # Data Aggregator
/tools/dat/runs/{run_id}    # DAT run details
/tools/sov                  # SOV Analyzer
/tools/sov/analysis/{id}    # SOV analysis details
/tools/pptx                 # PowerPoint Generator
/tools/pptx/runs/{run_id}   # PPTX run details
/datasets                   # DataSet browser
/datasets/{id}              # DataSet details
/pipelines                  # Pipeline manager
/pipelines/{id}             # Pipeline details
```

### Query Parameters for Cross-Tool Navigation

When piping data between tools:

```text
/tools/pptx?input_datasets=ds_abc123
/tools/pptx?input_datasets=ds_abc123,ds_def456
/tools/sov?input_datasets=ds_abc123
```

The receiving tool reads `input_datasets` and pre-populates the DataSet selection.

---

## Homepage Layout

```text
┌─────────────────────────────────────────────────────────────┐
│  Engineering Tools Platform                    [Health: ✓]  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │     DAT     │  │     SOV     │  │    PPTX     │         │
│  │ Aggregator  │  │  Analyzer   │  │  Generator  │         │
│  │    [✓]      │  │  [Coming]   │  │    [✓]      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Recent DataSets                              [View All →]  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ ds_abc123  │ DAT │ 1,234 rows │ 2 min ago           │  │
│  │ ds_def456  │ SOV │   456 rows │ 1 hour ago          │  │
│  │ ds_ghi789  │ DAT │ 5,678 rows │ Yesterday           │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Active Pipelines                             [View All →]  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Full Analysis Report │ Step 2/3 │ Running... [███░░] │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Tool Card Component

### States

| State | Visual | Behavior |
|-------|--------|----------|
| `available` | Green checkmark | Clickable, navigates to tool |
| `coming_soon` | Gray badge | Disabled, shows "Coming Soon" |
| `maintenance` | Yellow warning | Disabled, shows maintenance message |
| `error` | Red X | Shows error, retry option |

### Tool Card Props

```typescript
interface ToolCardProps {
  id: "dat" | "sov" | "pptx";
  name: string;
  description: string;
  status: "available" | "coming_soon" | "maintenance" | "error";
  icon: ReactNode;
  recentActivity?: {
    type: "dataset" | "run";
    name: string;
    timestamp: Date;
  };
}
```

---

## DataSet Browser

### Features

1. **List View** - Table of all DataSets with sorting/filtering
2. **Filter by Tool** - Show only DAT, SOV, or PPTX DataSets
3. **Search** - Filter by name or ID
4. **Preview** - Quick view of first 100 rows
5. **Lineage View** - Visualize parent/child relationships
6. **Actions** - Pipe to tool, delete, view details

### DataSet Browser Props

```typescript
interface DataSetBrowserProps {
  filterByTool?: "dat" | "sov" | "pptx";
  onSelect?: (datasetId: string) => void;
  showActions?: boolean;
}
```

---

## Pipeline Manager

### Features

1. **Pipeline List** - All pipelines with state indicators
2. **Create Pipeline** - Visual step builder
3. **Execute** - Start/stop pipeline execution
4. **Progress Tracking** - Real-time step status
5. **Error Details** - View failed step errors

### Pipeline Builder

```text
┌─────────────────────────────────────────────────────────────┐
│  Create Pipeline                                            │
├─────────────────────────────────────────────────────────────┤
│  Name: [Full Analysis Report________________]               │
│                                                             │
│  Steps:                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 1. [DAT: Aggregate ▼]  [Configure...]  [×]          │   │
│  │ 2. [SOV: ANOVA     ▼]  [Configure...]  [×]          │   │
│  │ 3. [PPTX: Generate ▼]  [Configure...]  [×]          │   │
│  │    [+ Add Step]                                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Cancel]                              [Save] [Execute →]   │
└─────────────────────────────────────────────────────────────┘
```

---

## Health Dashboard

### Health Check API

```text
GET /api/health

Response:
{
  "status": "healthy",
  "version": "0.1.0",
  "tools": {
    "dat": "available",
    "sov": "coming_soon",
    "pptx": "available"
  },
  "storage": {
    "datasets": 15,
    "pipelines": 3,
    "total_size_mb": 125.4
  }
}
```

### Health Indicator

- **Green** - All tools available
- **Yellow** - Some tools unavailable or in maintenance
- **Red** - Critical error (storage failure, gateway down)

---

## Acceptance Criteria (Homepage)

### AC-H1: Tool Launcher

- [ ] Homepage displays all tools as cards
- [ ] Tool status is fetched from health API
- [ ] Available tools are clickable and navigate correctly
- [ ] Coming soon tools show badge and are disabled

### AC-H2: DataSet Browser

- [ ] Recent DataSets shown on homepage (limit 5)
- [ ] Full DataSet browser at `/datasets`
- [ ] Filter by tool works
- [ ] Preview loads in < 2 seconds
- [ ] "Pipe To" action navigates correctly

### AC-H3: Pipeline Manager

- [ ] Pipeline list shows all pipelines
- [ ] Pipeline builder allows step configuration
- [ ] Execute starts pipeline in background
- [ ] Progress updates in real-time
- [ ] Cancel preserves completed work

### AC-H4: Health Dashboard

- [ ] Health indicator on homepage header
- [ ] Tool status reflects actual availability
- [ ] Storage stats displayed

---

## Frontend Routes

```typescript
// apps/homepage/frontend/src/routes.tsx

const routes = [
  { path: "/", element: <HomePage /> },
  { path: "/datasets", element: <DataSetBrowser /> },
  { path: "/datasets/:id", element: <DataSetDetails /> },
  { path: "/pipelines", element: <PipelineManager /> },
  { path: "/pipelines/:id", element: <PipelineDetails /> },
  { path: "/pipelines/new", element: <PipelineBuilder /> },
];
```

---

## API Integration

### Homepage Data Fetching

```typescript
// On homepage load
const { data: health } = useQuery("health", () => fetch("/api/health"));
const { data: datasets } = useQuery("recentDatasets", () => 
  fetch("/api/datasets/v1/?limit=5")
);
const { data: pipelines } = useQuery("activePipelines", () =>
  fetch("/api/pipelines/v1/?state=running")
);
```

---

## Next Steps

Proceed to Tier 3 for detailed Homepage specification:

- `tier-3-tools/homepage/HOMEPAGE_SPEC.md`
