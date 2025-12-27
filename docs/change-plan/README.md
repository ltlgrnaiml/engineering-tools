# Engineering Tools Platform - Change Plan

This directory contains the 4-tier change plan for implementing the Engineering Tools Platform monorepo.

## Document Hierarchy

```
change-plan/
├── tier-1-vision/           # WHAT & WHY - Platform vision, goals, ACs
│   └── PLATFORM_VISION.md   # Top-level architecture and acceptance criteria
│
├── tier-2-integration/      # HOW TOOLS CONNECT - Cross-tool workflows
│   ├── CROSS_TOOL_INTEGRATION.md    # Data piping, pipeline orchestration
│   └── HOMEPAGE_CONTROL.md          # Tool launcher and navigation
│
├── tier-3-tools/            # EACH TOOL - Detailed specifications
│   ├── homepage/
│   ├── data-aggregator/
│   ├── pptx-generator/
│   └── sov-analyzer/
│
└── tier-4-implementation/   # STEP-BY-STEP - AI-assistant ready instructions
    ├── phase-1-foundation/
    ├── phase-2-homepage-pptx/
    ├── phase-3-data-aggregator/
    └── phase-4-sov-analyzer/
```

## Reading Order

1. **Start with Tier 1** to understand the overall vision and acceptance criteria
2. **Review Tier 2** to understand how tools integrate and data flows
3. **Dive into Tier 3** for specific tool requirements
4. **Execute from Tier 4** for step-by-step implementation

## Tier Purposes

| Tier | Audience | Purpose |
|------|----------|---------|
| Tier 1 | Architects, PMs | Vision, scope, success criteria |
| Tier 2 | Senior Engineers | Integration patterns, data flows |
| Tier 3 | Engineers | Tool-specific requirements, code maps |
| Tier 4 | AI Assistants, Junior Devs | Step-by-step implementation |

## ADR References

All tiers reference the following foundational ADRs:

- **ADR-0009**: Type Safety & Contract Discipline (Tier 0 contracts)
- **ADR-0015**: 3-Tier Document Model (documentation hierarchy)
- **ADR-0016**: Hybrid Semver Contract Versioning
- **ADR-0017**: Cross-Cutting Guardrails
