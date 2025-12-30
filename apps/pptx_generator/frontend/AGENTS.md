# PPTX Frontend - AI Coding Guide

> **Scope**: React/TypeScript frontend for PowerPoint Generator tool.

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

## UI Pattern: 7-Step Workflow (ADR-0019)

```text
Step 1: Upload Template    ──►
Step 2: Upload Data        ──►
Step 3: Map Context        ──►
Step 4: Map Metrics        ──►
Step 5: Validate           ──►  "Four Green Bars"
Step 6: Generate           ──►
Step 7: Download
```

---

## Component Structure

```text
frontend/src/
├── components/
│   ├── steps/
│   │   ├── UploadTemplate.tsx
│   │   ├── UploadData.tsx
│   │   ├── MapContext.tsx
│   │   ├── MapMetrics.tsx
│   │   ├── Validate.tsx
│   │   ├── Generate.tsx
│   │   └── Download.tsx
│   ├── mapping/
│   │   ├── ColumnMapper.tsx
│   │   └── ShapePreview.tsx
│   └── common/
│       ├── StepIndicator.tsx
│       └── ValidationBar.tsx
├── hooks/
│   └── useWorkflowState.ts
└── api/
    └── pptx-api.ts
```

---

## Validation UI: "Four Green Bars"

Step 5 shows 4 validation indicators:

```tsx
interface ValidationStatus {
  templateValid: boolean;    // Bar 1: Template parsed
  dataLoaded: boolean;       // Bar 2: Data loaded
  contextMapped: boolean;    // Bar 3: Context columns mapped
  metricsMapped: boolean;    // Bar 4: Metric columns mapped
}

// Generate button disabled until all 4 are green
const canGenerate = Object.values(status).every(Boolean);
```

---

## Mapping Interface

```tsx
interface MappingProps {
  shapes: ShapePlaceholder[];      // From template discovery
  columns: string[];               // From uploaded data
  mappings: Record<string, string>; // shape_name -> column_name
  onMap: (shapeName: string, columnName: string) => void;
}

export function ColumnMapper({ shapes, columns, mappings, onMap }: MappingProps) {
  // Drag-and-drop or dropdown mapping UI
  ...
}
```

---

## Shape Preview

Show shape placeholder with mapped data preview:

```tsx
interface ShapePreviewProps {
  shape: ShapePlaceholder;
  previewData?: any;
}

export function ShapePreview({ shape, previewData }: ShapePreviewProps) {
  // Visual preview of how data will render in shape
  ...
}
```

---

## Testing

```bash
npm run test
npm run test:coverage
```
