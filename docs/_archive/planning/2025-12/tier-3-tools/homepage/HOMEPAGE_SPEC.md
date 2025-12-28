# Tier 3: Homepage Tool Specification

**Document Type:** Tool Specification  
**Audience:** Engineers  
**Last Updated:** 2025-01-26

---

## Overview

The Homepage is the central hub for the Engineering Tools Platform. It provides tool launching, DataSet browsing, pipeline management, and health monitoring.

---

## Responsibilities

1. **Tool Launcher** - Display and launch available tools
2. **DataSet Browser** - Browse, preview, and manage DataSets
3. **Pipeline Manager** - Create, monitor, and manage pipelines
4. **Health Dashboard** - Monitor platform and tool health
5. **Navigation** - Route to tools with context (piped DataSets)

---

## Acceptance Criteria (Homepage)

### AC-HOME1: Tool Grid

- [ ] Display all tools as cards in grid layout
- [ ] Show tool status (available, coming_soon, error)
- [ ] Click to navigate to tool
- [ ] Show recent activity per tool

### AC-HOME2: DataSet Browser

- [ ] List recent DataSets on homepage (limit 5)
- [ ] Full browser at /datasets
- [ ] Filter by source tool
- [ ] Search by name
- [ ] Preview DataSet contents
- [ ] Actions: Pipe to tool, view lineage, delete

### AC-HOME3: Pipeline Manager

- [ ] List pipelines at /pipelines
- [ ] Show pipeline state and progress
- [ ] Create new pipeline at /pipelines/new
- [ ] Visual step builder
- [ ] Execute/cancel pipelines

### AC-HOME4: Health Dashboard

- [ ] Health indicator in header
- [ ] Aggregate tool status from /api/health
- [ ] Storage statistics

### AC-HOME5: Navigation

- [ ] Clean URL structure
- [ ] Query params for piping context
- [ ] Back navigation preserves state

---

## Code Map

### Frontend Structure

```text
apps/homepage/frontend/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── MainLayout.tsx
│   │   ├── tools/
│   │   │   ├── ToolCard.tsx
│   │   │   └── ToolGrid.tsx
│   │   ├── datasets/
│   │   │   ├── DataSetList.tsx
│   │   │   ├── DataSetCard.tsx
│   │   │   ├── DataSetPreview.tsx
│   │   │   └── DataSetLineage.tsx
│   │   ├── pipelines/
│   │   │   ├── PipelineList.tsx
│   │   │   ├── PipelineCard.tsx
│   │   │   ├── PipelineBuilder.tsx
│   │   │   └── StepConfigurator.tsx
│   │   └── health/
│   │       ├── HealthIndicator.tsx
│   │       └── HealthDashboard.tsx
│   ├── hooks/
│   │   ├── useHealth.ts
│   │   ├── useDataSets.ts
│   │   └── usePipelines.ts
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── DataSetsPage.tsx
│   │   ├── DataSetDetailsPage.tsx
│   │   ├── PipelinesPage.tsx
│   │   ├── PipelineDetailsPage.tsx
│   │   └── PipelineBuilderPage.tsx
│   ├── routes.tsx
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

### Key Components

#### `ToolCard.tsx`

```typescript
interface ToolCardProps {
  id: "dat" | "sov" | "pptx";
  name: string;
  description: string;
  status: "available" | "coming_soon" | "maintenance" | "error";
  icon: ReactNode;
  path: string;
  recentActivity?: {
    type: "dataset" | "run";
    name: string;
    timestamp: Date;
  };
}

const ToolCard: React.FC<ToolCardProps> = ({ ... }) => {
  const navigate = useNavigate();
  const isDisabled = status !== "available";
  
  return (
    <Card 
      onClick={() => !isDisabled && navigate(path)}
      className={isDisabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
    >
      <CardHeader>
        {icon}
        <h3>{name}</h3>
        <StatusBadge status={status} />
      </CardHeader>
      <CardContent>
        <p>{description}</p>
        {recentActivity && <RecentActivityBadge {...recentActivity} />}
      </CardContent>
    </Card>
  );
};
```

#### `PipelineBuilder.tsx`

```typescript
interface PipelineBuilderProps {
  onSave: (pipeline: CreatePipelineRequest) => void;
  onExecute: (pipeline: CreatePipelineRequest) => void;
}

const PipelineBuilder: React.FC<PipelineBuilderProps> = ({ ... }) => {
  const [name, setName] = useState("");
  const [steps, setSteps] = useState<PipelineStep[]>([]);
  
  const addStep = (type: PipelineStepType) => {
    setSteps([...steps, { step_index: steps.length, step_type: type, ... }]);
  };
  
  return (
    <div className="pipeline-builder">
      <Input label="Pipeline Name" value={name} onChange={setName} />
      <StepList steps={steps} onRemove={removeStep} onConfigure={configureStep} />
      <StepPalette onAdd={addStep} />
      <ButtonGroup>
        <Button onClick={() => onSave(buildRequest())}>Save</Button>
        <Button variant="primary" onClick={() => onExecute(buildRequest())}>
          Execute
        </Button>
      </ButtonGroup>
    </div>
  );
};
```

---

## Routes

```typescript
// apps/homepage/frontend/src/routes.tsx
import { createBrowserRouter } from "react-router-dom";

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
  // Tool routes (served by gateway, redirect to tool apps)
  { path: "tools/dat/*", element: <ToolRedirect tool="dat" /> },
  { path: "tools/sov/*", element: <ToolRedirect tool="sov" /> },
  { path: "tools/pptx/*", element: <ToolRedirect tool="pptx" /> },
]);
```

---

## API Integration

### Hooks

```typescript
// hooks/useHealth.ts
export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => fetch("/api/health").then(r => r.json()),
    refetchInterval: 30000, // Refresh every 30s
  });
}

// hooks/useDataSets.ts
export function useDataSets(options?: { tool?: string; limit?: number }) {
  return useQuery({
    queryKey: ["datasets", options],
    queryFn: () => {
      const params = new URLSearchParams();
      if (options?.tool) params.set("tool", options.tool);
      if (options?.limit) params.set("limit", String(options.limit));
      return fetch(`/api/datasets/v1/?${params}`).then(r => r.json());
    },
  });
}

// hooks/usePipelines.ts
export function usePipelines() {
  return useQuery({
    queryKey: ["pipelines"],
    queryFn: () => fetch("/api/pipelines/v1/").then(r => r.json()),
  });
}

export function useCreatePipeline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreatePipelineRequest) =>
      fetch("/api/pipelines/v1/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
      }).then(r => r.json()),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["pipelines"] }),
  });
}
```

---

## Change Order

### Phase 2A: Homepage Setup (Week 2)

1. Create `apps/homepage/frontend/` with Vite + React
2. Install dependencies (TailwindCSS, shadcn/ui, react-query)
3. Create MainLayout with Header
4. Create HomePage with ToolGrid

### Phase 2B: Tool Cards (Week 2)

1. Implement ToolCard component
2. Fetch health from /api/health
3. Display tools with status
4. Navigation to tools

### Phase 2C: DataSet Browser (Week 2-3)

1. Implement DataSetList and DataSetCard
2. Fetch from /api/datasets/v1/
3. Preview modal with first 100 rows
4. Filter and search

### Phase 2D: Pipeline Manager (Week 3)

1. Implement PipelineList
2. Implement PipelineBuilder
3. Execute pipelines
4. Progress tracking

---

## Validation Plan

### Unit Tests

- [ ] ToolCard renders correctly for each status
- [ ] DataSetList filters work
- [ ] PipelineBuilder creates valid request

### Integration Tests

- [ ] Health fetch and display
- [ ] DataSet list and preview
- [ ] Pipeline create and execute

### E2E Tests

- [ ] Navigate from homepage to each tool
- [ ] Browse datasets, preview, pipe to tool
- [ ] Create and execute pipeline
