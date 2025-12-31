# DISC-004: PII Sanitization Pipeline

**Status**: resolved  
**Created**: 2025-12-30  
**Author**: AI-Assisted  
**Depends On**: DISC-002

---

## Summary

Design a PII (Personally Identifiable Information) sanitization pipeline to safely include codebase context in LLM prompts without exposing sensitive data.

---

## Context

RAG system will inject code snippets, configs, and docs into prompts. Must sanitize:

- API keys, secrets, tokens
- Email addresses, names
- Internal URLs, IPs
- Database connection strings
- Customer-specific data

---

## Requirements (To Be Filled)

### Functional

- [ ] FR-1: Detect and redact API keys/secrets
- [ ] FR-2: Replace emails with placeholders
- [ ] FR-3: Mask internal URLs/IPs
- [ ] FR-4: Configurable pattern rules
- [ ] FR-5: Audit log of redactions

### Non-Functional

- [ ] NFR-1: <10ms latency per sanitization
- [ ] NFR-2: Zero false negatives for known patterns
- [ ] NFR-3: Reversible redaction (for debugging)

---

## Options Considered

### Option A: Regex-Based (MVP)

**Pros**: Simple, fast, no dependencies  
**Cons**: Limited to known patterns, false positives

### Option B: Microsoft Presidio

**Pros**: ML-based, comprehensive, battle-tested  
**Cons**: Heavy dependency, slower

### Option C: Custom NER Model

**Pros**: Project-specific accuracy  
**Cons**: Training data needed, maintenance

---

## Pattern Categories

| Category | Example Pattern | Replacement |
|----------|-----------------|-------------|
| API Keys | `sk-...`, `AKIA...` | `[REDACTED_API_KEY]` |
| Secrets | `password=...` | `[REDACTED_SECRET]` |
| Emails | `user@domain.com` | `[EMAIL]` |
| IPs | `192.168.x.x` | `[INTERNAL_IP]` |
| URLs | `https://internal...` | `[INTERNAL_URL]` |

---

## Decision

**Chosen: Option A - Regex-Based MVP**

**Rationale**:
1. Simple, fast, no external dependencies
2. Sufficient for known patterns (API keys, emails, IPs)
3. Can upgrade to Presidio later if needed
4. Aligns with MVP-first philosophy

**Configuration**:

| Setting | Value | Rationale |
|---------|-------|----------|
| False Positive Rate | **<5%** | Balance safety vs usability |
| Reversible Redaction | **Dev only** | Debug capability without prod risk |
| Pattern Source | Configurable YAML | Easy to extend |

**Implementation**:
```python
# Dev mode: reversible
redacted = sanitize(content, reversible=IS_DEV_MODE)

# Prod mode: permanent
redacted = sanitize(content, reversible=False)
```

---

## Deferred Decisions

| Decision | Reason | Revisit When |
|----------|--------|-------------|
| Compliance (GDPR/SOC2) | Legal review needed | Before public release |
| Presidio upgrade | Evaluate after MVP | If false positive rate >5% |

---

## Open Questions

1. ~~What's acceptable false positive rate?~~ → **<5%**
2. ~~Should redaction be reversible for debugging?~~ → **Dev only**
3. ~~Project-specific patterns to add?~~ → **Inventory during implementation**
4. ~~Compliance requirements (GDPR, SOC2)?~~ → **Deferred to legal review**

---

## Next Steps

- [x] Decision: Regex MVP with <5% FP rate ✅
- [x] Decision: Reversible in dev only ✅
- [ ] Inventory sensitive patterns in codebase
- [ ] Implement regex-based sanitizer
- [ ] Add pattern configuration YAML

