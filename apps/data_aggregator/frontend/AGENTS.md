# DAT Frontend - AI Coding Guide

> **Scope**: React/TypeScript frontend for Data Aggregator tool.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Framework | React 18+ |
| Language | TypeScript (strict mode) |
| Styling | TailwindCSS |
| State | React Query + Context |
| Icons | Lucide React |

---

## UI Pattern: Horizontal Wizard (ADR-0043)

DAT uses a horizontal stepper pattern for the 8-stage pipeline:

```text
┌─────────────────────────────────────────────────────────────┐
│  [1]──[2]──[3]──[4]──[5]──[6]──[7]──[8]                    │
│  Upload Context Preview Select Agg Parse Export Complete    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Collapsible Panel: Current Stage Content           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Patterns

### Functional Components Only

```tsx
// ✅ CORRECT
interface StageCardProps {
  stage: DATStage;
  onLock: () => void;
}

export function StageCard({ stage, onLock }: StageCardProps) {
  return <div>...</div>;
}

// ❌ WRONG - No class components
class StageCard extends React.Component { ... }
```

### Named Exports

```tsx
// ✅ CORRECT
export function StageCard() { ... }
export function StagePanel() { ... }

// ❌ WRONG
export default function StageCard() { ... }
```

---

## State Indicators

Stage states should display visual indicators:

| State | Visual |
|-------|--------|
| `UNLOCKED` | Gray circle, editable |
| `LOCKED` | Blue checkmark, read-only |
| `COMPLETED` | Green checkmark, final |
| `ERROR` | Red X, retry available |

---

## API Integration

```tsx
import { useQuery, useMutation } from '@tanstack/react-query';

// Fetch stage state
const { data: stage } = useQuery({
  queryKey: ['stage', stageId],
  queryFn: () => api.get(`/api/dat/v1/stages/${stageId}`)
});

// Lock stage mutation
const lockMutation = useMutation({
  mutationFn: () => api.post(`/api/dat/v1/stages/${stageId}/lock`)
});
```

---

## File Structure

```text
frontend/src/
├── components/
│   ├── stages/           # Stage-specific components
│   ├── wizard/           # Wizard stepper components
│   └── common/           # Shared UI components
├── hooks/
│   └── useStageState.ts  # Stage state management
├── api/
│   └── dat-api.ts        # API client
└── types/
    └── dat.types.ts      # TypeScript types (mirror contracts)
```

---

## Testing

```bash
npm run test              # Run all tests
npm run test:coverage     # With coverage
```
