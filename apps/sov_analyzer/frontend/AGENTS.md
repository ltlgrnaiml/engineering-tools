# SOV Frontend - AI Coding Guide

> **Scope**: React/TypeScript frontend for SOV Analyzer tool.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| Framework | React 18+ |
| Language | TypeScript (strict mode) |
| Styling | TailwindCSS |
| Charts | D3.js or Recharts |
| State | React Query + Context |

---

## UI Sections

```text
┌─────────────────────────────────────────────────────────────┐
│  1. Data Selection                                          │
│     └── Select DataSet from available datasets              │
├─────────────────────────────────────────────────────────────┤
│  2. Factor Configuration                                    │
│     └── Select factors (categorical) and response (numeric) │
├─────────────────────────────────────────────────────────────┤
│  3. Analysis Results                                        │
│     └── Variance table, F-statistics, p-values              │
├─────────────────────────────────────────────────────────────┤
│  4. Visualizations                                          │
│     └── Box plots, interaction plots, Pareto chart          │
└─────────────────────────────────────────────────────────────┘
```

---

## Component Structure

```text
frontend/src/
├── components/
│   ├── data/
│   │   ├── DatasetSelector.tsx
│   │   └── ColumnSelector.tsx
│   ├── analysis/
│   │   ├── VarianceTable.tsx
│   │   └── FactorConfig.tsx
│   ├── charts/
│   │   ├── BoxPlot.tsx
│   │   ├── InteractionPlot.tsx
│   │   └── ParetoChart.tsx
│   └── common/
│       └── LoadingSpinner.tsx
├── hooks/
│   ├── useDataset.ts
│   └── useAnalysis.ts
└── api/
    └── sov-api.ts
```

---

## Visualization Components

### Variance Table

```tsx
interface VarianceTableProps {
  components: VarianceComponent[];
}

export function VarianceTable({ components }: VarianceTableProps) {
  // Display: Factor | Variance % | F-statistic | p-value
  // Highlight significant factors (p < 0.05)
  // Show total = 100%
  ...
}
```

### Box Plot

```tsx
interface BoxPlotProps {
  data: DataFrame;
  factor: string;
  response: string;
}

export function BoxPlot({ data, factor, response }: BoxPlotProps) {
  // D3.js or Recharts box plot
  // One box per factor level
  // Show median, quartiles, outliers
  ...
}
```

### Pareto Chart

```tsx
interface ParetoChartProps {
  components: VarianceComponent[];
}

export function ParetoChart({ components }: ParetoChartProps) {
  // Bar chart sorted by variance %
  // Cumulative line overlay
  // 80/20 reference line
  ...
}
```

---

## DataSet Selection

```tsx
import { useQuery } from '@tanstack/react-query';

// Fetch available datasets
const { data: datasets } = useQuery({
  queryKey: ['datasets'],
  queryFn: () => api.get('/api/v1/datasets')
});

// Select dataset for analysis
const handleSelect = (datasetId: string) => {
  // Load dataset columns for factor/response selection
  ...
};
```

---

## Testing

```bash
npm run test
npm run test:coverage
```
