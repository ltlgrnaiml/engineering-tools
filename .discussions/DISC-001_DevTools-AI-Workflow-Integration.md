# DISC-001: DevTools AI Workflow Integration

> **Status**: `resolved`
> **Created**: 2025-12-30
> **Updated**: 2025-12-30
> **Author**: Mycahya Eggleston
> **AI Session**: Current Session

---

## Summary

Extend the existing DevTools panel to support the full AI Development Workflow (ADR-0043). The DevTools already has a robust ADR reader/editor with folder organization, search, and form-based editing. This proposal extends it to support SPECs, Discussions, and Plans — providing a unified UI for the 6-tier workflow.

---

## Context

### Background

The DevTools panel (`apps/homepage/frontend/src/pages/DevToolsPage.tsx`) currently provides:
- **ADR Reader/Editor** with folder-based organization (core, shared, dat, pptx, sov, devtools)
- **Search** functionality across all ADRs
- **Tabbed interface** (Reader / Editor)
- **Form-based editing** via `ADRFormEditor` component
- **Create new ADR** with folder selection
- **API integration** at `/api/devtools/adrs`

The AI Development Workflow (ADR-0043) introduces:
- `.discussions/` - Design conversation capture (T0)
- `.plans/` - Implementation tracking (T4)
- Existing `.adrs/` (T1) and `docs/specs/` (T2)

### Trigger

After implementing ADR-0043's file-based workflow, the USER recognized that the DevTools panel is the perfect place for a comprehensive UI to manage all workflow artifacts — making the AI-assisted development process more accessible and visual.

---

## Requirements

### Functional Requirements

- [ ] **FR-1**: Add SPEC reader/editor tab (parallel to ADR) with folder organization
- [ ] **FR-2**: Add Discussion viewer/creator with status tracking and artifact linking
- [ ] **FR-3**: Add Plan viewer with milestone/task tracking and progress visualization
- [ ] **FR-4**: Add "New Artifact" button with type selection (ADR, SPEC, Discussion, Plan)
- [ ] **FR-5**: Cross-link artifacts (Discussion → ADR → SPEC → Plan)
- [ ] **FR-6**: Search across all artifact types
- [ ] **FR-7**: Status-based filtering (draft, active, resolved, etc.)
- [ ] **FR-8**: Visual workflow diagram showing tier relationships (2D/3D graph)
- [ ] **FR-9**: Command palette (`Cmd+K` / `Ctrl+K`) for quick navigation and actions
- [ ] **FR-10**: Activity feed showing recent changes across all artifacts
- [ ] **FR-11**: Empty states with onboarding guidance for new users
- [ ] **FR-12**: Export graph visualization as PNG/SVG image

### Non-Functional Requirements

- [ ] **NFR-1**: Responsive design matching existing DevTools styling
- [ ] **NFR-2**: API response < 200ms for artifact lists
- [ ] **NFR-3**: Form validation matching JSON schemas
- [ ] **NFR-4**: Keyboard navigation for power users
- [ ] **NFR-5**: Confirmation dialogs for destructive actions (delete, discard changes)
- [ ] **NFR-6**: Undo support for recent edits (soft delete with restore)

---

## Constraints

- **C-1**: Must use existing tech stack (React, TypeScript, TailwindCSS, Lucide icons)
- **C-2**: Backend API must follow existing `/api/devtools/` pattern
- **C-3**: Must not break existing ADR functionality
- **C-4**: Artifacts stored as files (not database) per existing architecture

---

## Open Questions

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-1 | UI layout pattern? | `answered` | **Sidebar + Map + Reader** (see Session 4) |
| Q-2 | Plan task checkboxes editable in UI? | `deferred` | Future enhancement |
| Q-3 | Real-time file watching? | `deferred` | Future enhancement |
| Q-4 | Implementation phase priority? | `open` | Pending SPEC creation |
| Q-5 | Visualization library choice | `answered` | **react-force-graph** with 2D/3D toggle |
| Q-6 | 2D vs 3D visualization | `answered` | **BOTH** with lazy-loaded toggle button |
| Q-7 | Editor panel behavior? | `answered` | **Slide-in** from right, replaces map+reader |

---

## Options Considered

### Option A: Tabbed Artifact Types

**Description**: Add top-level tabs for each artifact type (ADRs, SPECs, Discussions, Plans). Each tab has its own sidebar list and reader/editor.

**Pros**:
- Clear separation of concerns
- Matches existing ADR-only pattern
- Simpler navigation within artifact type

**Cons**:
- More clicks to switch between related artifacts
- Harder to see cross-artifact relationships

### Option B: Unified View with Type Filter

**Description**: Single artifact list with type filter dropdown. Sidebar shows all artifacts grouped by type, expandable.

**Pros**:
- See all artifacts in one place
- Easier cross-referencing
- Less UI duplication

**Cons**:
- More complex sidebar
- May feel cluttered with many artifacts

### Option C: Hybrid - Dashboard + Detail Views

**Description**: Dashboard home showing workflow overview (tier diagram, recent activity, quick actions). Click through to type-specific detail views.

**Pros**:
- Best of both worlds
- Visual workflow guidance
- Scalable to future artifact types

**Cons**:
- More development effort
- Additional navigation layer

### Recommendation

**Option C (Hybrid)** provides the best user experience for the AI-assisted workflow, giving both overview and detail. Start with Option A (tabs) for MVP, evolve to Option C.

---

## Decision Points

| ID | Decision | Status | Outcome |
|----|----------|--------|---------|
| D-1 | UI layout pattern | `decided` | Sidebar (tabbed file list) + Main Panel (Map + Reader) |
| D-2 | Visualization library | `decided` | `react-force-graph` with 2D/3D toggle |
| D-3 | Editor behavior | `decided` | Slide-in panel replaces viewer |
| D-4 | Map interactivity | `decided` | Click node → focus file, update reader |
| D-5 | Phase 1 scope (MVP features) | `pending` | Awaiting SPEC creation |
| D-6 | Backend API structure | `pending` | Follow `/api/devtools/` pattern |

---

## Scope Definition

### In Scope

- SPEC reader/editor (parallel to existing ADR)
- Discussion viewer/creator
- Plan viewer with progress tracking
- Cross-artifact navigation
- Backend API extensions
- TypeScript contracts for new artifact types

### Out of Scope

- Real-time collaboration (future)
- Git integration for change tracking (future)
- AI-assisted artifact generation (future)
- Mobile-optimized views (future)

---

## Existing Assets

| Component | Location | Reusable For |
|-----------|----------|--------------|
| `DevToolsPage.tsx` | `apps/homepage/frontend/src/pages/` | Base structure |
| `ADRFormEditor` | `apps/homepage/frontend/src/components/` | SPEC form editor |
| ADR API endpoints | `gateway/` or backend | Extend for SPECs/Discussions/Plans |
| ADR/SPEC JSON schemas | `schemas/` | Validation |

---

## Resulting Artifacts

| Artifact Type | ID | Title | Status |
|---------------|----|-------|--------|
| ADR | ADR-0044 | DevTools AI Workflow UI | `pending` |
| SPEC | SPEC-0009 | DevTools Workflow Manager | `pending` |
| Contract | `shared/contracts/devtools/workflow.py` | Workflow artifact contracts | `pending` |
| Plan | PLAN-001 | DevTools Workflow Integration | `pending` |

---

## Conversation Log

### 2025-12-30 - Session Part 1

**Topics Discussed**:
- AI Development Workflow (ADR-0043) implementation completed
- User proposed integrating workflow into DevTools panel
- Explored existing DevToolsPage.tsx structure

**Key Insights**:
- DevTools already has ADR reader/editor with folder org, search, form editing
- Pattern is highly reusable for SPECs, Discussions, Plans
- API pattern at `/api/devtools/adrs` can extend to other types

---

### 2025-12-30 - Session Part 2: Visualization Research

**USER Request**: 
> "I think it is really important for our development team to see how all the different ADRs, SPECs and CONTRACTS are linked, is there a COOL and NEW way we can visualize these connections? Maybe a fancy node map, or a 3d-node map we can move around with cool tool-tips etc!"

**Research Conducted**: Web search for innovative React graph visualization libraries

#### Visualization Library Options Discovered

| Library | Stars | Rendering | 2D | 3D | VR/AR | Best For |
|---------|-------|-----------|----|----|-------|----------|
| **react-force-graph** | 2.9K | WebGL/Canvas | ✅ | ✅ | ✅ | Large graphs, 3D/VR |
| **Reagraph** | 962 | WebGL | ✅ | ✅ | ❌ | React-native, themes |
| **Sigma.js** | High | WebGL | ✅ | ❌ | ❌ | Massive graphs (10K+) |
| **Cytoscape.js** | High | Canvas/SVG | ✅ | ❌ | ❌ | Bio-informatics, complex |
| **Visx** | 17.9K | SVG | ✅ | ❌ | ❌ | Custom low-level |

#### Detailed Analysis

**🥇 react-force-graph (TOP RECOMMENDATION)**
- GitHub: github.com/vasturiano/react-force-graph
- **4 packages**: 2D, 3D, VR, AR with identical interfaces
- Uses d3-force-3d physics engine
- Features: zoom/pan, node dragging, hover/click, directional arrows, particles
- Excellent examples: DAG mode, expand/collapse, bloom effects
- **Low dependency footprint**

**🥈 Reagraph**
- GitHub: github.com/reaviz/reagraph  
- Website: reagraph.dev
- WebGL-powered, React-first design
- Features: clustering, edge bundling, radial context menu, lasso selection
- 15+ built-in layouts (force-directed, tree, radial, hierarchical)
- Light/dark themes, custom nodes
- **Has CLAUDE.md** - AI-friendly codebase!

**🥉 Sigma.js + @react-sigma**
- Website: sigmajs.org
- Designed for MASSIVE graphs (thousands of nodes)
- Works with Graphology for graph algorithms
- Used by: Gephi Lite, GraphCommons, BloodHound
- Best when performance with huge datasets is critical

**Cytoscape.js**
- Most mature, bio-informatics heritage
- react-cytoscapejs wrapper by Plotly
- Extensive algorithm library
- Heavier, more complex API

#### Key Insight for Our Use Case

Our artifact relationship graph will be:
- **Small to medium** (dozens to hundreds of nodes)
- **Hierarchical** (Tier 0→1→2→3→4)
- **Interactive** (click to navigate, hover for tooltips)
- **Visually impressive** (3D would be a differentiator!)

**Recommendation**: 
1. **Primary**: `react-force-graph-3d` for the WOW factor - 3D rotating graph with zoom/pan
2. **Fallback**: `Reagraph` if we want more React-native patterns and built-in themes
3. **Both are lightweight** and won't bloat our bundle

#### Visualization Concept

```
                    [DISC-001] ←──────────────────┐
                        │                         │
                        ▼                         │
                    [ADR-0044]                    │
                        │                         │
            ┌───────────┼───────────┐             │
            ▼           ▼           ▼             │
       [SPEC-001]  [SPEC-002]  [SPEC-003]         │
            │           │           │             │
            ▼           ▼           ▼             │
      [Contract]  [Contract]  [Contract]          │
            │           │           │             │
            └───────────┼───────────┘             │
                        ▼                         │
                   [PLAN-001] ────────────────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      [Fragment]   [Fragment]   [Fragment]
```

In 3D, this becomes a rotating sphere of interconnected nodes!

**Action Items**:
- [x] USER to confirm visualization library choice
- [x] Discuss frontend toolstack changes if needed
- [ ] Define node types and edge relationships
- [ ] Prototype 3D graph visualization

---

### 2025-12-30 - Session Part 3: 2D/3D Toggle Decision

**USER Question**:
> "Can we actually implement both with a button to switch from 2D to 3D?? What kind of code complexity overhead do we accrue with that?"

**Analysis Conducted**: Reviewed react-force-graph API compatibility across packages

#### Key Finding: Identical APIs

The `react-force-graph` library exports 4 packages with **identical interfaces**:
- `react-force-graph-2d` (Canvas)
- `react-force-graph-3d` (WebGL/three.js)
- `react-force-graph-vr` (A-Frame)
- `react-force-graph-ar` (AR.js)

This means **zero code duplication** — same props work across all variants!

#### Complexity Overhead Analysis

| Aspect | Impact | Notes |
|--------|--------|-------|
| Bundle Size | +~200KB | three.js, but only when 3D used |
| Code Duplication | **ZERO** | Same props object, different component |
| State Management | **1 boolean** | `is3D` toggle state |
| Maintenance | **Low** | Update props once, works for both |
| Learning Curve | **Minimal** | Same API across variants |

#### Proposed Architecture

```tsx
// Lazy load 3D to avoid bundle bloat
import ForceGraph2D from 'react-force-graph-2d';
import { lazy, Suspense, useState } from 'react';

const ForceGraph3D = lazy(() => import('react-force-graph-3d'));

function ArtifactGraph({ graphData }) {
  const [is3D, setIs3D] = useState(false);
  
  // Shared props - works for BOTH components
  const graphProps = {
    graphData,
    nodeLabel: 'title',
    nodeColor: node => getTierColor(node.tier),
    linkDirectionalArrowLength: 6,
    onNodeClick: node => navigateToArtifact(node),
  };

  return (
    <>
      <Toggle3DButton is3D={is3D} onToggle={() => setIs3D(!is3D)} />
      
      {is3D ? (
        <Suspense fallback={<LoadingSpinner />}>
          <ForceGraph3D {...graphProps} />
        </Suspense>
      ) : (
        <ForceGraph2D {...graphProps} />
      )}
    </>
  );
}
```

#### Benefits of Dual Mode

| Mode | Best For |
|------|----------|
| **2D** | Focused work, documentation, printing, accessibility |
| **3D** | Presentations, exploration, stakeholder demos, WOW factor |

#### TENTATIVE AGREEMENT ✅

**Decision**: Implement BOTH 2D and 3D with toggle button

**Rationale**:
1. Near-zero complexity overhead due to identical APIs
2. Lazy loading prevents bundle bloat
3. Users get best of both worlds
4. Future-proof: can add VR/AR mode with same pattern

**Frontend Toolstack Changes**:
- Add dependency: `react-force-graph-2d`
- Add dependency: `react-force-graph-3d` (lazy-loaded)
- Peer dependency: `three.js` (only loaded when 3D active)

**Action Items**:
- [x] Define UI layout pattern
- [ ] Define node type schema (tier, status, color mapping)
- [ ] Define edge relationship schema (implements, references, creates)
- [ ] Design tooltip content for each artifact type
- [ ] Plan integration with existing DevTools navigation

---

### 2025-12-30 - Session Part 4: UI/UX Layout Design

**USER Vision**:
> "I want the user to be able to see a list of files in a tabbed panel on the left, which has panels for the different document types (ADR, SPEC, CONTRACT, etc). On the right when the user clicks a file the Viewer/Reader should open which has the Map on top (with the options for 2D/3D), showing how the chosen file fits in with all the other documents (using the internal doc links for node connections), below the map should be the reader view, with a button that opens an editor panel, maybe the editor panel slides in from the right side of the screen and replaces the map and reader view with the form/wizard."

#### Agreed Layout: Viewer Mode

```text
┌─────────────────────────────────────────────────────────────────────┐
│  DevTools Workflow Manager                              [🔍] [⚙️]  │
├──────────────┬──────────────────────────────────────────────────────┤
│              │  ┌─────────────────────────────────────────────────┐ │
│  📁 ADRs     │  │         INTERACTIVE MAP (2D/3D Toggle)         │ │
│  ├─ ADR-0001 │  │                                                 │ │
│  ├─ ADR-0043 │  │      [DISC]──▶[ADR-0043]──▶[SPEC]──▶[Plan]     │ │
│  └─ ADR-0044 │  │                    ⬇                            │ │
│              │  │               [Contract]                        │ │
│  📋 SPECs    │  │                                                 │ │
│  ├─ SPEC-001 │  └─────────────────────────────────────────────────┘ │
│  └─ SPEC-031 │  ┌─────────────────────────────────────────────────┐ │
│              │  │              READER VIEW                        │ │
│  💬 Discuss  │  │  ═══════════════════════════════════════════    │ │
│  └─ DISC-001 │  │  # ADR-0043: AI Development Workflow           │ │
│              │  │                                                 │ │
│  📑 Plans    │  │  **Status**: Active                            │ │
│  └─ PLAN-001 │  │  **Context**: This ADR establishes...          │ │
│              │  │                                    [✏️ Edit]   │ │
│  🔷 Contracts│  └─────────────────────────────────────────────────┘ │
│  └─ workflow │                                                      │
└──────────────┴──────────────────────────────────────────────────────┘
```

#### Agreed Layout: Editor Mode (Slide-in)

```text
┌─────────────────────────────────────────────────────────────────────┐
│  DevTools Workflow Manager                              [🔍] [⚙️]  │
├──────────────┬──────────────────────────────────────────────────────┤
│              │  ┌─────────────────────────────────────────────────┐ │
│  📁 ADRs     │  │  ◀ Back to Viewer          EDITOR PANEL        │ │
│  ├─ ADR-0001 │  ├─────────────────────────────────────────────────┤ │
│  ├─ ADR-0043◀│  │  Title: [ADR-0043: AI Development Workflow   ] │ │
│  └─ ADR-0044 │  │  Status: [Active ▼]                            │ │
│              │  │  Context:                                       │ │
│  📋 SPECs    │  │  ┌───────────────────────────────────────────┐ │ │
│  ...         │  │  │ This ADR establishes the 6-tier...       │ │ │
│              │  │  └───────────────────────────────────────────┘ │ │
│              │  │  Decision:                                      │ │
│              │  │  ┌───────────────────────────────────────────┐ │ │
│              │  │  │ Implement hierarchical workflow...       │ │ │
│              │  │  └───────────────────────────────────────────┘ │ │
│              │  │                                                 │ │
│              │  │            [Cancel]  [💾 Save]                  │ │
│              │  └─────────────────────────────────────────────────┘ │
└──────────────┴──────────────────────────────────────────────────────┘
```

#### Approved Enhancements

| Enhancement | Description | Priority |
|-------------|-------------|----------|
| **Resizable Split Panes** | Drag divider between Map and Reader | MVP |
| **Map Focus Modes** | Ego-centric (default), Full Graph, Hierarchy View | MVP |
| **Quick Preview on Hover** | Tooltip card before clicking node | MVP |
| **Breadcrumb Trail** | Navigation history (Home → ADR → SPEC → ...) | MVP |
| **Keyboard Navigation** | Tab, arrows, Enter, E(dit), Escape, 2/3 toggle | Nice-to-have |
| **Status Indicators** | ✅ active, ⚠️ review, 📝 draft icons in sidebar | MVP |
| **Mini-Map Inset** | Small 2D overview when in 3D mode | Nice-to-have |
| **Split View** | Compare two artifacts side-by-side | Future |

#### Map Interactivity Rules

| Action | Behavior |
|--------|----------|
| **Click node** | Focus that file → update Reader + re-center Map |
| **Hover node** | Show tooltip card with summary |
| **Drag node** | Rearrange graph layout (persists during session) |
| **Scroll/Pinch** | Zoom in/out |
| **Click + Drag background** | Pan the view |
| **Double-click node** | Open editor for that file |
| **Ctrl+Click node** | Open in new browser tab (future) |

#### Edge Relationship Types

| Edge Type | Visual | Meaning |
|-----------|--------|----------|
| `implements` | Solid arrow | SPEC implements ADR |
| `references` | Dashed line | Cross-reference |
| `creates` | Dotted arrow | Discussion creates ADR |
| `tracked_by` | Solid line | Artifact tracked by Plan |

#### Node Color Scheme by Tier

| Tier | Type | Color | Hex |
|------|------|-------|-----|
| T0 | Discussion | 🔵 Blue | `#3B82F6` |
| T1 | ADR | 🟢 Green | `#22C55E` |
| T2 | SPEC | 🟡 Yellow | `#EAB308` |
| T3 | Contract | 🟣 Purple | `#A855F7` |
| T4 | Plan | 🔴 Red | `#EF4444` |
| T5 | Fragment | ⚪ Gray | `#6B7280` |

#### Component Architecture

```text
<WorkflowManager>
  ├── <Sidebar>
  │   ├── <SearchBar>
  │   ├── <TabList>           // ADRs, SPECs, Discussions, Plans, Contracts
  │   └── <FileTree>
  │       └── <FileItem>      // with status icon, click handler
  │
  └── <MainPanel>
      ├── <ViewerMode>        // default view
      │   ├── <ArtifactGraph> // 2D/3D toggle, interactive
      │   │   ├── <GraphControls>   // zoom, pan, mode, 2D/3D
      │   │   ├── <ForceGraph2D> or <ForceGraph3D>
      │   │   └── <MiniMap>         // optional inset
      │   ├── <ResizableDivider>
      │   └── <ArtifactReader>
      │       ├── <Breadcrumbs>
      │       ├── <ContentRenderer> // markdown/json viewer
      │       └── <EditButton>
      │
      └── <EditorMode>        // slides in, replaces viewer
          ├── <BackButton>
          ├── <ArtifactForm>  // type-specific fields
          └── <SaveControls>
</WorkflowManager>
```

#### Edge Cases Considered

| Scenario | Behavior |
|----------|----------|
| File with no links | Show "orphan" badge, suggest linking |
| Circular references | Handle gracefully, show cycle indicator |
| Deep graph (10+ levels) | Collapse distant nodes, expand on demand |
| New file creation | Start in editor, auto-suggest links |
| Deleted file reference | Show broken link indicator in map |
| External file edit | Refresh on focus (file watching deferred) |

#### TENTATIVE AGREEMENT ✅

**Layout Pattern**: Sidebar (tabbed file tree) + Main Panel (Map on top, Reader below, Editor slides in)

**Key Behaviors**:
1. Click file in sidebar → opens in Reader, Map centers on file
2. Click node in Map → switches focus to that file
3. Edit button → Editor slides in from right
4. Back button → returns to Viewer mode
5. 2D/3D toggle persists user preference

---

### 2025-12-30 - Session Part 5: Workflow Automation Architecture

**USER Question**:
> "What about the full WORKFLOW? We need some way to enable a FULL Wizard that walks the developer through each step. Can you explain which portions would be automated and how we can automate the workflow?"

#### Two Interaction Modes

The system supports two complementary interaction modes that share a **common file system**:

| Mode | Interface | Best For |
|------|-----------|----------|
| **AI Chat** (Windsurf/Cascade) | Conversational | Rich content, code generation, execution |
| **DevTools UI** (Web) | Forms/Wizard | Structure, tracking, visualization |

Both modes read/write the same files — **files are the single source of truth**.

#### Automation Responsibility Matrix

| Task | DevTools UI | AI Chat |
|------|:-----------:|:-------:|
| Create artifact from template | ✅ | |
| Fill in rich content | | ✅ |
| Edit structured fields (forms) | ✅ | |
| Edit unstructured content | | ✅ |
| Generate next artifact from previous | | ✅ |
| Track progress/status | ✅ | |
| Execute code changes (Contracts, Fragments) | | ✅ |
| Visualize relationships (Graph) | ✅ | |
| Suggest next steps | ✅ | ✅ |

#### Wizard Flow (DevTools UI)

```text
NEW WORKFLOW WIZARD
═══════════════════

Step 1: What are you building?
  ○ New Feature          → starts at Discussion (T0)
  ○ Architecture Change  → starts at Discussion (T0)
  ○ Bug Fix              → starts at Plan (T4)
  ○ Simple Enhancement   → starts at SPEC (T2)
  ○ New Data Structure   → starts at Contract (T3, manual)

Step 2: Create Initial Artifact
  → UI wizard creates file with basic structure
  → Prompts user to refine with AI

Step 3: AI Handoff
  → UI generates context-aware prompt
  → User copies prompt to AI chat
  → AI refines content, creates next artifact

Step 4: Progress Tracking
  → UI displays workflow progress
  → Shows which artifacts exist, which are pending
  → Visualizes relationships in graph
```

#### Handoff Protocol: UI → AI → UI

```text
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   DevTools UI   │         │    AI Chat      │         │   DevTools UI   │
│   (Structure)   │         │   (Content)     │         │   (Tracking)    │
├─────────────────┤         ├─────────────────┤         ├─────────────────┤
│ 1. User clicks  │         │                 │         │                 │
│    "New Feature"│         │                 │         │                 │
│        │        │         │                 │         │                 │
│        ▼        │         │                 │         │                 │
│ 2. Wizard creates│        │                 │         │                 │
│    DISC-XXX.md  │────────▶│ 3. AI reads file│         │                 │
│    (skeleton)   │         │    refines it   │         │                 │
│                 │         │        │        │         │                 │
│                 │         │        ▼        │         │                 │
│                 │         │ 4. AI creates   │────────▶│ 5. UI detects   │
│                 │         │    ADR-XXXX.json│         │    new file     │
│                 │         │                 │         │        │        │
│                 │         │                 │         │        ▼        │
│                 │         │                 │         │ 6. Graph updates│
│                 │         │                 │         │    shows link   │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

#### Smart Prompt Generation

DevTools UI generates **context-aware prompts** for AI handoff:

| Current State | Generated Prompt |
|---------------|------------------|
| Discussion created, no ADR | "Please review DISC-XXX and create an ADR capturing the key decisions." |
| ADR active, no SPEC | "ADR-XXXX is approved. Please create a SPEC with detailed requirements." |
| SPEC active, no Plan | "SPEC-XXX is ready. Please create an implementation Plan with fragments." |
| Plan created, tasks pending | "Let's execute PLAN-XXX. Start with the first incomplete task." |

#### File Detection & Parsing

DevTools backend scans artifact directories and parses files:

```python
# Backend API: GET /api/devtools/artifacts
def get_all_artifacts():
    artifacts = []
    
    # Scan each artifact directory
    for disc in scan_directory('.discussions/', '*.md'):
        artifacts.append(parse_discussion(disc))
    
    for adr in scan_directory('.adrs/', '*.json', recursive=True):
        artifacts.append(parse_adr(adr))
    
    for spec in scan_directory('docs/specs/', '*.json', recursive=True):
        artifacts.append(parse_spec(spec))
    
    for plan in scan_directory('.plans/', '*.md'):
        artifacts.append(parse_plan(plan))
    
    # Build relationship graph from references
    graph = build_relationship_graph(artifacts)
    
    return { 'artifacts': artifacts, 'graph': graph }
```

#### TENTATIVE AGREEMENT ✅

**Automation Architecture**:
1. **DevTools UI** = Orchestration layer (structure, tracking, visualization)
2. **AI Chat** = Content engine (writing, code generation, execution)
3. **Files** = Single source of truth (both modes read/write same files)
4. **Handoff** = UI generates prompts, AI creates files, UI detects and displays

---

### 2025-12-30 - Session Part 6: Workflow Action Bar & Config Management

**USER Request**:
> "Where do we have buttons for the Workflows? Should we have a bar at the top for the different workflow actions?"

#### Agreed: Header Action Bar + Workflow Stepper (Option A + D)

**Normal Mode** (Header Action Bar):

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  [➕ New Workflow ▼]  [📋 DISC-001 ▼]                        [🔍] [⚙️]      │
├──────────────┬──────────────────────────────────────────────────────────────┤
│  Sidebar     │  Main Panel (Map + Reader)                                   │
```

**New Workflow Dropdown**:

```text
┌────────────────────────┐
│ 🚀 New Feature         │  → starts Discussion
│ 🏗️ Architecture Change │  → starts Discussion  
│ 🐛 Bug Fix             │  → starts Plan
│ ✨ Enhancement         │  → starts SPEC
│ 📦 New Data Structure  │  → manual (Contract)
├────────────────────────┤
│ 📄 New ADR             │
│ 📋 New SPEC            │
│ 💬 New Discussion      │
│ 📑 New Plan            │
└────────────────────────┘
```

**Workflow Mode** (Stepper appears when actively creating):

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  🚀 New Feature: "DevTools Integration"                       [X Cancel]    │
│  ───────────────────────────────────────────────────────────────────────────│
│    ✅ Discussion  →  🔵 ADR  →  ○ SPEC  →  ○ Plan                           │
│       DISC-001       Creating...                                            │
├──────────────┬──────────────────────────────────────────────────────────────┤
```

#### TENTATIVE AGREEMENT ✅

**Toolbar UI**:
1. **Header Action Bar** always visible with [➕ New Workflow ▼] button
2. **Workflow Stepper** appears when user is actively stepping through workflow
3. **Active Artifact Selector** [📋 DISC-001 ▼] for quick context switching

---

### 2025-12-30 - Session Part 7: Config/Profile Management Scope

**USER Request**:
> "I want to be able to let the Powerusers, and devs to have a tool to add, delete, modify the existing Configuration/Profile files from each tool... Should this be fully separate utility or try to smash it together with the current plan?"

#### Analysis: Two Different Domains

| Aspect | Workflow Artifacts | Config/Profile Files |
|--------|-------------------|---------------------|
| **Purpose** | Document decisions & plans | Configure tool behavior |
| **Files** | `.discussions/`, `.adrs/`, `.plans/`, `docs/specs/` | `profiles/`, `configs/`, tool-specific |
| **Lifecycle** | draft → active → resolved | active (edited in place) |
| **Relationships** | Hierarchical (DISC→ADR→SPEC→Plan) | Per-tool, independent |
| **Users** | Developers, AI assistants | Power users, operators |
| **Frequency** | Per-feature/change | Per-job/dataset |

#### Options

**Option A: Separate Utility (Config Manager)**

```text
DevTools Panel
├── Workflow Manager (current plan)
│   ├── Discussions, ADRs, SPECs, Plans
│   └── Artifact Graph
│
└── Config Manager (separate tab/page)
    ├── DAT Profiles
    ├── SOV Configurations  
    ├── PPTX Templates
    └── Tool-specific configs
```

**Pros**: Clean separation, focused UX, different permissions possible
**Cons**: Two places to learn, no cross-linking

**Option B: Integrated (Single Panel, Multiple Modes)**

```text
DevTools Panel
├── Mode Toggle: [Workflow] [Configs]
│
├── Workflow Mode
│   └── (current plan)
│
└── Config Mode
    ├── Tool selector: [DAT] [SOV] [PPTX]
    └── Profile/Config editor per tool
```

**Pros**: Single entry point, unified experience
**Cons**: More complex, may confuse the two domains

**Option C: Hybrid (Integrated but Visually Distinct)**

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  DevTools                                                                    │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │  [📐 Workflow Manager]  [⚙️ Config Manager]  [📊 Monitoring]           │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────────────────┤
```

**Pros**: Clear navigation, room for future tools (Monitoring, etc.)
**Cons**: Additional nav layer

#### My Recommendation: Option C (Hybrid)

**Rationale**:
1. DevTools becomes a **toolbox** with multiple utilities
2. Clear mental model: "Workflow" vs "Config" vs future tools
3. Shared components (sidebar pattern, editor pattern) can be reused
4. Scales better as platform grows

**Proposed Tab Structure**:

| Tab | Purpose | Contents |
|-----|---------|----------|
| **Workflow Manager** | AI-assisted development | Discussions, ADRs, SPECs, Plans, Graph |
| **Config Manager** | Tool configuration | DAT Profiles, SOV Configs, PPTX Templates |
| **System Monitor** | (future) | Logs, metrics, health checks |

#### Decision

| ID | Question | Status | Answer |
|----|----------|--------|--------|
| Q-8 | Should Config Manager be in scope for this feature or separate DISC? | `answered` | **Phase 2** — separate DISC-002 after Workflow Manager ships |

#### TENTATIVE AGREEMENT ✅

**Phased Delivery**:
- **Phase 1**: Workflow Manager (this DISC → ADR-0044 → SPEC-0009 → PLAN-001)
- **Phase 2**: Config Manager (DISC-002 → ADR-0045 → SPEC-0010 → PLAN-002)

---

---

### 2025-12-30 - Session Part 8: Workflow Modes & Scenarios

**USER Request**:
> "We need both USER Manual (as much as can be done) and AI assisted flows with different levels of AI assist. Please map out the most value added scenarios you can envision with our current scope."

#### Three Workflow Modes Defined

| Mode | User Effort | AI Involvement | Use Case |
|------|-------------|----------------|----------|
| **Manual** | High | None | Full control, learning, offline |
| **AI-Lite** | Medium | Prompts + Templates | Guided structure, user writes content |
| **AI-Full** | Low | End-to-end generation | Rapid prototyping, experienced users |

#### Scenario 1: New Feature Development

**Manual Flow**:
```
User clicks "New Feature" →
  UI shows form: Title, Summary, Initial Thoughts →
  Backend creates DISC-XXX.md from template →
  User manually writes Discussion content →
  User clicks "Create ADR from Discussion" →
  UI shows ADR form pre-filled with DISC reference →
  User writes ADR content →
  ... repeat for SPEC, Contract, Plan
```

**AI-Lite Flow**:
```
User clicks "New Feature" →
  UI shows form: Title, one-line description →
  Backend creates DISC-XXX.md skeleton →
  UI generates prompt: "I'm starting DISC-XXX about {title}. Help me flesh out..."
  User copies prompt → pastes to AI chat →
  AI helps write content → User pastes back or AI saves directly →
  When complete, UI suggests: "Ready to create ADR? [Generate ADR Prompt]"
```

**AI-Full Flow**:
```
User clicks "New Feature" →
  UI shows simple form: Title, 2-3 sentence description →
  User clicks "Generate Full Workflow" →
  Backend generates: DISC, ADR, SPEC (all with content) →
  UI shows all created artifacts in graph →
  User reviews, edits as needed
```

#### Scenario 2: Bug Fix

**Manual**: User creates Plan directly with tasks, executes manually.

**AI-Lite**: UI generates debugging prompt with error context, AI suggests tasks.

**AI-Full**: Paste error log → AI creates full debugging plan with verification commands.

#### Scenario 3: Architecture Change

Full workflow (Discussion → ADR → SPEC → Contract → Plan) with mode-appropriate assistance at each stage.

#### Scenario 4: Simple Enhancement

SPEC-first workflow (SPEC → Plan → Fragment) for smaller changes.

#### High-Value Backend APIs Required

| Endpoint | Purpose | Mode Support |
|----------|---------|--------------|
| `POST /workflows` | Start workflow, create initial artifact | All |
| `GET /workflows/{id}/status` | Check which artifacts exist | All |
| `POST /workflows/{id}/advance` | Create next artifact in chain | Manual, AI-Lite |
| `POST /artifacts/generate` | AI generates artifact content | AI-Full |
| `GET /artifacts/{id}/prompt` | Get context-aware AI prompt | AI-Lite |
| `POST /artifacts/from-template` | Create from template | Manual |
| `GET /workflows/{id}/suggestions` | What should user do next? | All |

#### High-Value Frontend Features

| Feature | Manual | AI-Lite | AI-Full |
|---------|--------|---------|---------|
| Template-based creation | ✅ | ✅ | ✅ |
| Form wizard per artifact type | ✅ | ✅ | ✅ |
| Cross-reference linking UI | ✅ | ✅ | ✅ |
| Progress tracking (file-based) | ✅ | ✅ | ✅ |
| Copy prompt to clipboard | - | ✅ | - |
| Prompt preview/customization | - | ✅ | - |
| One-click generation | - | - | ✅ |
| Review/approve workflow | - | - | ✅ |

#### MVP Scope Decision

**Phase 1: Manual + AI-Lite** (highest value, lowest risk)
- Backend: Workflow creation, status tracking, prompt generation, templates
- Frontend: Wizard forms, "Copy AI Prompt" button, file-based progress tracking

**Phase 2: AI-Full**
- Backend AI generation endpoints
- One-click artifact generation
- Review/approve UI

#### TENTATIVE AGREEMENT ✅

**Workflow Modes**: Three modes (Manual, AI-Lite, AI-Full) with phased delivery.

---

## Resolution

**Resolution Date**: 2025-12-30

**Outcome**: Discussion COMPLETE — ready for ADR/SPEC updates

**Decisions Made** (7 sessions):

| ID | Decision | Outcome |
|----|----------|---------|
| D-1 | UI Layout | Sidebar (tabbed file tree) + Main Panel (Map + Reader) |
| D-2 | Visualization | `react-force-graph` with 2D/3D toggle, lazy-loaded |
| D-3 | Editor | Slide-in panel replaces viewer |
| D-4 | Map Interactivity | Click node → focus file, update reader |
| D-5 | Toolbar | Header Action Bar + Workflow Stepper |
| D-6 | Automation | UI orchestration + AI content engine, file-based SSOT |
| D-7 | Config Manager | Deferred to Phase 2 (DISC-002) |

**Next Steps** (per ADR-0043 workflow):
1. ✅ Discussion complete (DISC-001)
2. ✅ **ADR-0045**: DevTools Workflow Manager UI Architecture (active)
3. ✅ **SPEC-0003**: DevTools Workflow Manager (draft)
4. → **Create PLAN-001**: DevTools Workflow Integration (implementation tasks)
5. → (Phase 2) Create DISC-002: Config Manager

---

*Template version: 1.0.0 | See `.discussions/README.md` for usage instructions*
