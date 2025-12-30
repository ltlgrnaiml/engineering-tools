# Discussions Directory

> **Purpose**: Capture AI ↔ Human design conversations that lead to architectural decisions, specifications, and implementation plans.

## Overview

The `.discussions/` directory is **Tier 0** of the AI Development Workflow. It captures the exploratory conversation between you and your AI coding assistant before formal artifacts (ADRs, SPECs, Plans) are created.

## When to Create a Discussion

Create a new discussion when:
- Proposing a **new feature** or **enhancement**
- Exploring **architectural options** before committing
- **Refactoring** that may have broad implications
- Any work that might require an **ADR** or **SPEC**

## File Naming Convention

```
DISC-{NNN}_{Brief-Description}.md
```

Examples:
- `DISC-001_WebSocket-Real-Time-Updates.md`
- `DISC-002_Profile-Schema-Migration.md`
- `DISC-003_SOV-Streaming-Pipeline.md`

## Discussion Lifecycle

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   DRAFT     │ ──► │   ACTIVE    │ ──► │  RESOLVED   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    Creates artifacts:
                    - ADR (if decision needed)
                    - SPEC (if behavior defined)
                    - PLAN (if implementation scoped)
```

## Quick Start

1. **Create from template**:
   ```bash
   python scripts/workflow/new_discussion.py "Brief Description"
   ```

2. **Or copy template manually**:
   ```bash
   cp .discussions/.templates/DISC_TEMPLATE.md .discussions/DISC-XXX_Name.md
   ```

3. **Fill in sections** as you discuss with AI assistant

4. **Link resulting artifacts** in the `## Resulting Artifacts` section

## Directory Structure

```
.discussions/
├── README.md                    # This file
├── INDEX.md                     # Index of all discussions
├── .templates/
│   └── DISC_TEMPLATE.md         # Template for new discussions
├── DISC-001_Example.md          # Individual discussions
└── ...
```

## Integration with AI Assistant

The AI assistant (Cascade) will:
1. **Detect** when a conversation should become a discussion
2. **Prompt** you to create a discussion file
3. **Update** the discussion as requirements crystallize
4. **Transition** to creating ADRs/SPECs when decisions are made

## Related Directories

| Directory | Purpose | Relationship |
|-----------|---------|--------------|
| `.adrs/` | Architecture decisions | Created FROM discussions |
| `docs/specs/` | Behavioral specifications | Created FROM discussions |
| `.plans/` | Implementation plans | Created FROM discussions or SPECs |
| `.sessions/` | Session logs | References active discussions |

## Schema

See `.templates/DISC_TEMPLATE.md` for the full schema with all fields.

---

*Part of the AI Development Workflow. See `docs/guides/AI_DEVELOPMENT_WORKFLOW.md` for complete documentation.*
