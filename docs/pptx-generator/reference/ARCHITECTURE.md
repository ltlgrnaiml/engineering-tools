# Architecture Overview

## System Design

PowerPoint Generator is integrated into the Engineering Tools Platform as a tool accessible through the gateway.

```text
┌─────────────────────────────────────────────────────────────────┐
│                    Homepage (React SPA)                          │
│                    http://localhost:3000                         │
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│   │     DAT      │  │     SOV      │  │     PPTX     │         │
│   │   (iframe)   │  │   (iframe)   │  │   (iframe)   │         │
│   └──────────────┘  └──────────────┘  └──────────────┘         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                    API Gateway (FastAPI)                         │
│                    http://localhost:8000                         │
├─────────────────────────────────────────────────────────────────┤
│  /api/datasets/v1  │  /api/pipelines/v1  │  /api/pptx/*         │
└────────────────────┴──────────────────────┴─────────────────────┘
                                                   │
                                            ┌──────▼──────┐
                                            │ PPTX Backend│
                                            │ (FastAPI)   │
                                            └──────┬──────┘
                                                   │
                                              ┌────┴────┐
                                              │         │
                                          ┌───▼──┐  ┌──▼───┐
                                          │Files │  │Memory│
                                          │System│  │ DB   │
                                          └──────┘  └──────┘
```

## Backend Architecture

### Layered Architecture

```text
┌─────────────────────────────────────┐
│         API Layer                   │
│  (FastAPI Routes & Endpoints)       │
│  apps/pptx_generator/backend/api/   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│       Service Layer                 │
│  (Business Logic & Processing)      │
│  apps/pptx_generator/backend/services/
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│        Models Layer                 │
│   (Pydantic Data Validation)        │
│  apps/pptx_generator/backend/models/│
└─────────────────────────────────────┘
```

### Core Components

#### 1. API Layer (`apps/pptx_generator/backend/api/`)

Handles HTTP requests and responses:

- **health.py**: Health check endpoints
- **projects.py**: Project CRUD operations
- **templates.py**: Template upload and parsing
- **data.py**: Data file and mapping management
- **dataset_input.py**: DataSet integration for cross-tool workflows
- **requirements.py**: DRM, mappings, and validation endpoints
- **config_defaults.py**: Configuration file management
- **preview.py**: Slide preview and generation summary
- **generation.py**: Presentation generation

#### 2. Service Layer (`apps/pptx_generator/backend/services/`)

Contains business logic:

- **template_parser.py**: Extracts shape information from PowerPoint templates
- **data_processor.py**: Processes data files and applies transformations
- **presentation_generator.py**: Generates PowerPoint presentations
- **storage.py**: Manages file storage operations

#### 3. Models Layer (`apps/pptx_generator/backend/models/`)

Pydantic models for data validation:

- **project.py**: Project-related models
- **template.py**: Template and shape map models
- **data.py**: Data file and mapping models
- **generation.py**: Generation request/response models

### Integration with Gateway

The PPTX backend is mounted on the gateway at `/api/pptx`:

```python
# gateway/main.py
from apps.pptx_generator.backend.main import app as pptx_app
app.mount("/api/pptx", pptx_app)
```

This means PPTX API endpoints are available at:

- `GET /api/pptx/api/v1/health`
- `POST /api/pptx/api/v1/projects`
- etc.

### DataSet Integration

PPTX Generator can load data from the shared DataSet store:

```python
# apps/pptx_generator/backend/api/dataset_input.py
@router.post("/{project_id}/from-dataset")
async def load_from_dataset(project_id: UUID, request: DataSetInputRequest):
    """Load data from an existing DataSet into a PPTX project."""
    from shared.storage.artifact_store import ArtifactStore
    store = ArtifactStore()
    df, manifest = store.read_dataset(request.dataset_id)
    # Create DataFile from DataSet...
```

## Frontend Architecture

### Component Structure

```text
apps/pptx_generator/frontend/src/
├── components/              # Reusable UI components
│   ├── ConfigEditor.tsx    # Configuration file editor
│   ├── ConfirmDialog.tsx   # Rollback confirmation
│   ├── ContextMappingEditor.tsx
│   ├── EnvironmentProfileSelector.tsx
│   ├── FourBarsGate.tsx    # Validation display
│   ├── Layout.tsx          # Main layout wrapper
│   ├── MetricsMappingEditor.tsx
│   ├── SlidePreview.tsx    # Pre-generation preview
│   └── WorkflowBreadcrumb.tsx
├── pages/                   # Page-level components
│   ├── HomePage.tsx        # Project list
│   ├── ProjectPage.tsx     # Project details
│   └── WorkflowPage.tsx    # Guided workflow
├── lib/                     # Utilities
│   └── api.ts              # API client
└── types/                   # TypeScript definitions
    └── index.ts            # Shared types
```

### API Client Configuration

The frontend connects to the gateway with API path rewriting:

```typescript
// vite.config.ts
server: {
  port: 5175,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '/api/pptx/api'),
    },
  },
}
```

### Routing

React Router for client-side routing:

- `/` - Home page (project list)
- `/projects/:projectId` - Project details
- `/projects/:projectId/workflow` - Guided workflow

## Data Flow

### 1. Upload Template

```text
Client → API → Storage Service → File System
             → Template Parser → Shape Map
```

### 2. Load from DataSet

```text
Client → API → ArtifactStore → Read Parquet
             → DataFile Record → Project Update
```

### 3. Generate Presentation

```text
Client → API → Data Processor → Prepared Data
             → Presentation Generator → PowerPoint File
             → Storage Service → File System
```

## Project Status Flow

1. `CREATED` - Project created
2. `DRM_EXTRACTED` - Template parsed and DRM extracted
3. `ENVIRONMENT_CONFIGURED` - Environment profile set
4. `DATA_UPLOADED` - Data file uploaded
5. `MAPPINGS_CONFIGURED` - Context and metrics mappings saved
6. `PLAN_FROZEN` - Execution plan built and frozen
7. `READY_TO_GENERATE` - All components ready for generation
8. `GENERATING` - Presentation generation in progress
9. `COMPLETED` - Presentation generated successfully
10. `FAILED` - Generation failed
