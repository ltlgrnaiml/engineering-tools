# AI Coding Assistant Platform - Extraction Plan

## Project Name Candidates

- **AI Dev Orchestrator** - Orchestrates AI-assisted development
- **PlanForge** - Forge execution plans for AI assistants
- **SpecFlow AI** - Spec-driven AI development
- **CodePilot Framework** - Framework for piloting AI coding

## What to Extract (Core System)

### Tier 1: Schemas & Contracts (CRITICAL)

| File | Purpose | Adaptation Needed |
|------|---------|-------------------|
| `plan_schema.py` | L1/L2/L3 granularity system | Remove engineering-tools specifics |
| `adr_schema.py` | Architecture Decision Records | Keep as-is |
| `spec_schema.py` | Technical Specifications | Keep as-is |

### Tier 2: ADRs (Transferable Knowledge)

| ADR | Title | Why Extract |
|-----|-------|-------------|
| ADR-0033 | AI-Assisted Development Patterns | **Core philosophy** |
| ADR-0041 | AI Development Workflow | **6-tier hierarchy** |
| ADR-0015 | 3-Tier Document Model | Documentation strategy |
| ADR-0009 | Type-Safety & Contract Discipline | Pydantic patterns |
| ADR-0016 | Calendar Versioning | Version format |

### Tier 3: Workflow Infrastructure

| Directory | Purpose | Extract |
|-----------|---------|---------|
| `.discussions/` | Design conversations | ✅ Templates + AGENTS.md |
| `.plans/` | Execution plans | ✅ Templates + AGENTS.md |
| `.sessions/` | Session continuity | ✅ Structure |
| `.questions/` | Open questions | ✅ Structure |
| `.experiments/` | A/B testing framework | ✅ EXP-001 as example |

### Tier 4: Experiment Framework

| Component | Purpose |
|-----------|---------|
| `SCORECARD_V2.json` | Model evaluation rubric |
| `FINAL_REPORT.md` | Example analysis |
| `save_results.py` | Automated results collection |
| `aggregate_results.py` | Results aggregation |

---

## What NOT to Extract (Domain-Specific)

| Component | Reason |
|-----------|--------|
| `shared/contracts/dat/` | DAT-specific |
| `shared/contracts/pptx/` | PPTX-specific |
| `shared/contracts/sov/` | SOV-specific |
| `apps/` | Tool implementations |
| `gateway/` | API services (keep as example) |
| Tool-specific ADRs | ADR-0001-DAT, ADR-0018, etc. |

---

## New Project Structure

```
ai-dev-orchestrator/
├── README.md                    # Getting started
├── pyproject.toml               # uv/pip dependencies
├── .gitignore
│
├── AGENTS.md                    # Global AI instructions
├── AI_CODING_GUIDE.md           # Human + AI coding guide
│
├── contracts/                   # Pydantic schemas (SSOT)
│   ├── __init__.py
│   ├── plan_schema.py           # L1/L2/L3 plans
│   ├── adr_schema.py            # ADR structure
│   ├── spec_schema.py           # SPEC structure
│   └── discussion_schema.py     # Discussion structure
│
├── .adrs/                       # Architecture decisions
│   ├── INDEX.md
│   ├── AGENTS.md
│   ├── core/
│   │   ├── ADR-0001_AI-Development-Workflow.json
│   │   ├── ADR-0002_AI-Assisted-Development-Patterns.json
│   │   ├── ADR-0003_3-Tier-Document-Model.json
│   │   ├── ADR-0004_Plan-Granularity-Levels.json
│   │   └── ADR-0005_Contract-Discipline.json
│   └── .templates/
│       └── ADR_TEMPLATE.json
│
├── docs/
│   ├── specs/                   # Technical specifications
│   │   ├── INDEX.md
│   │   └── SPEC-001_Plan-Schema.json
│   └── guides/
│       ├── GETTING_STARTED.md
│       ├── PLAN_AUTHORING.md
│       └── EXPERIMENT_DESIGN.md
│
├── .discussions/                # Design conversations
│   ├── INDEX.md
│   ├── AGENTS.md
│   ├── README.md
│   └── .templates/
│       └── DISC_TEMPLATE.md
│
├── .plans/                      # Execution plans
│   ├── INDEX.md
│   ├── AGENTS.md
│   ├── README.md
│   └── .templates/
│       └── PLAN_TEMPLATE.json
│
├── .sessions/                   # Session continuity
│   └── README.md
│
├── .questions/                  # Open questions
│   └── README.md
│
├── .experiments/                # A/B testing framework
│   ├── README.md
│   ├── EXP-001_L1-vs-L3/        # Example experiment
│   │   ├── FINAL_REPORT.md
│   │   ├── SCORECARD_V2.json
│   │   └── scripts/
│   │       ├── save_results.py
│   │       └── aggregate_results.py
│   └── .templates/
│       └── EXPERIMENT_TEMPLATE/
│
├── scripts/                     # Automation
│   ├── new_discussion.py
│   ├── new_plan.py
│   ├── new_experiment.py
│   └── verify_plan.py
│
├── examples/                    # Example projects
│   ├── simple_crud_app/
│   │   ├── PLAN-001.json
│   │   └── README.md
│   └── api_refactor/
│       ├── PLAN-001.json
│       └── README.md
│
└── tests/
    ├── test_plan_schema.py
    └── test_adr_schema.py
```

---

## Product Vision

### Target Users

1. **Solo developers** using AI coding assistants
2. **Teams** wanting consistent AI-assisted workflows
3. **AI tool vendors** needing structured input formats

### Key Features

1. **Plan Granularity System** (L1/L2/L3)
   - L1: Context for premium models
   - L2: Constraints for mid-tier models
   - L3: Step-by-step for budget models

2. **6-Tier Workflow**
   - Discussion → ADR → SPEC → Contract → Plan → Fragment

3. **Experiment Framework**
   - A/B test different AI models
   - Measure stochastic variation
   - Cost-effectiveness analysis

4. **Session Continuity**
   - Cross-session handoff
   - Progress tracking
   - Evidence capture

### Monetization Ideas

- **Open Core**: Free framework, paid templates/examples
- **SaaS**: Hosted experiment platform
- **Enterprise**: Custom integrations, consulting

---

## Extraction Steps

1. Create new project directory
2. Copy and adapt contracts (remove domain specifics)
3. Copy core ADRs (renumber for new project)
4. Copy workflow infrastructure (.discussions, .plans, etc.)
5. Copy experiment framework
6. Create new README with getting started guide
7. Add example projects
8. Set up pyproject.toml with minimal dependencies

---

*Created: December 30, 2025*
*Source: engineering-tools EXP-001 experiment*
