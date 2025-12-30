# ADRs Directory - AI Coding Guide

> **Scope**: Architecture Decision Records authoring and maintenance.

---

## What are ADRs?

ADRs (Architecture Decision Records) document the **WHY** behind architectural decisions.

**Tier Position**: Tier 1 (between Contracts and SPECs)

```text
Tier 0: Contracts (SSOT)     ← Data structures
Tier 1: ADRs (WHY)           ← THIS DIRECTORY
Tier 2: SPECs (WHAT)         ← Implementation specs
Tier 3: Guides (HOW)         ← How-to guides
```

---

## Directory Structure

```text
.adrs/
├── INDEX.md              # ADR index (this is the master list)
├── core/                 # Platform-wide ADRs
├── dat/                  # Data Aggregator ADRs
├── pptx/                 # PowerPoint Generator ADRs
├── sov/                  # SOV Analyzer ADRs
├── shared/               # Cross-tool pattern ADRs
└── devtools/             # Developer tooling ADRs
```

---

## ADR Naming Convention

Format: `ADR-{NNNN}_{Title-Kebab-Case}.json`

Examples:
- `ADR-0001_Hybrid-FSM-Architecture.json`
- `ADR-0011_Profile-Driven-Extraction.json`
- `ADR-0033_AI-Assisted-Development-Patterns.json`

---

## ADR Schema

All ADRs must follow `shared/contracts/adr_schema.py`:

```json
{
  "id": "ADR-0001",
  "title": "Hybrid FSM Architecture",
  "status": "Accepted",
  "context": "Why this decision was needed...",
  "decision": "What we decided...",
  "consequences": ["Positive and negative impacts..."],
  "implementation_specs": ["SPEC-0001"],
  "related_adrs": ["ADR-0002", "ADR-0018"]
}
```

---

## ADR Status Lifecycle

```text
Proposed → Accepted → Deprecated
              │
              └── Superseded (by newer ADR)
```

| Status | Meaning |
|--------|---------|
| `Proposed` | Under discussion, not yet approved |
| `Accepted` | Active and enforced |
| `Deprecated` | No longer recommended |
| `Superseded` | Replaced by newer ADR |

---

## Rules for ADR Content

1. **No code snippets** - ADRs explain WHY, not HOW
2. **Reference SPECs** - Use `implementation_specs` for the WHAT
3. **Reference Contracts** - Don't duplicate Pydantic models
4. **Keep focused** - One decision per ADR
5. **Document alternatives** - Show what was considered

---

## Creating a New ADR

1. Check `INDEX.md` for the next available ADR number
2. Create JSON file in appropriate subdirectory
3. Follow the schema in `shared/contracts/adr_schema.py`
4. Update `INDEX.md` with the new entry
5. Create corresponding SPEC if implementation details needed

---

## Validation

ADRs are validated by CI:

```bash
# Validate ADR schema
python tools/validate_adrs.py

# Check ADR-SPEC cross-references
python tools/check_adr_spec_refs.py
```
