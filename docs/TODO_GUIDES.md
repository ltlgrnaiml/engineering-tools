# TODO: GUIDES (Tier 3 Documentation)

> **Status**: Deferred until PROD release
> **Priority**: Low (final documentation pass)
> **Created**: 2025-12-27

---

## Overview

Per ADR-0016 (3-Tier Document Model), GUIDES are Tier 3 documentation that provide step-by-step instructions, examples, and workflows for developers and end users. GUIDES are intentionally deferred until:

1. All code implementation is complete and stable
2. ADRs (Tier 1) are finalized
3. SPECs (Tier 2) are complete
4. Contracts (Tier 0) are validated

## Planned GUIDES

### Core Platform Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| Getting Started | Local development setup | README.md |
| Contract Development | Creating Pydantic contracts | ADR-0010 |
| FSM Implementation | Building guided workflows | ADR-0001, SPEC-0001 |
| Testing Guide | Unit, integration, E2E testing | ADR-0007 |
| Rendering Guide | Using unified rendering engine | ADR-0029, SPEC-0009 |

### DAT Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| Profile Creation | Building extraction profiles | ADR-0012, SPEC-0025 |
| Parser Development | Adding new file adapters | ADR-0012 |
| Export Formats | Configuring export options | ADR-0015 |

### PPTX Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| Template Design | Creating PPTX templates with named shapes | ADR-0019, SPEC-0004 |
| Data Binding | Mapping data to shapes | ADR-0022, SPEC-0005 |
| Custom Renderers | Adding new renderer types | ADR-0022, SPEC-0015 |

### SOV Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| ANOVA Configuration | Setting up ANOVA analysis | ADR-0023, SPEC-0006 |
| Visualization Customization | Customizing chart appearance | ADR-0025, SPEC-0017 |

## Completion Criteria

Before creating GUIDES:

- [ ] All tools (DAT, PPTX, SOV) have working implementations
- [ ] All ADRs are in "Accepted" status
- [ ] All SPECs reference implemented contracts
- [ ] CI/CD pipeline validates contract compliance
- [ ] End-to-end workflows are tested

## Notes

- GUIDES should be written for the target audience (developers vs. end users)
- Include working code examples
- Reference SPECs and ADRs for architectural context
- Keep step-by-step instructions concise and actionable
- Use MkDocs format for integration with documentation site

---
*Created: 2025-12-27*
*To be completed: Before PROD release*
