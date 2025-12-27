# TODO: GUIDES (Tier 3 Documentation)

> **Status**: Deferred until PROD release
> **Priority**: Low (final documentation pass)
> **Created**: 2025-12-27

---

## Overview

Per ADR-0015 (3-Tier Document Model), GUIDES are Tier 3 documentation that provide step-by-step instructions, examples, and workflows for developers and end users. GUIDES are intentionally deferred until:

1. All code implementation is complete and stable
2. ADRs (Tier 1) are finalized
3. SPECs (Tier 2) are complete
4. Contracts (Tier 0) are validated

## Planned GUIDES

### Core Platform Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| Getting Started | Local development setup | README.md |
| Contract Development | Creating Pydantic contracts | ADR-0009 |
| FSM Implementation | Building guided workflows | ADR-0001, SPEC-0001 |
| Testing Guide | Unit, integration, E2E testing | ADR-0005 |
| Rendering Guide | Using unified rendering engine | ADR-0028, SPEC-0031 |

### DAT Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| Profile Creation | Building extraction profiles | ADR-0011, SPEC-DAT-0002 |
| Parser Development | Adding new file adapters | ADR-0011 |
| Export Formats | Configuring export options | ADR-0014 |

### PPTX Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| Template Design | Creating PPTX templates with named shapes | ADR-0018, SPEC-PPTX-0019 |
| Data Binding | Mapping data to shapes | ADR-0021, SPEC-PPTX-0020 |
| Custom Renderers | Adding new renderer types | ADR-0021, SPEC-PPTX-0023 |

### SOV Guides

| Guide | Description | Prerequisites |
|-------|-------------|---------------|
| ANOVA Configuration | Setting up ANOVA analysis | ADR-0022, SPEC-SOV-0024 |
| Visualization Customization | Customizing chart appearance | ADR-0024, SPEC-SOV-0027 |

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
