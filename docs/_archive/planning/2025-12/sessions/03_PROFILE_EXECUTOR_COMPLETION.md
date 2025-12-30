# Patch Plan 03 — Profile Executor Completion & Wiring

**Session:** 021  
**Goal:** Close gaps for profile-driven parse per `IMPL_Profile-Executor-Implementation-Plan.md`, grounded in contracts (Tier 0) → ADRs → SPECs, following Solo-Dev ethos.

## Scope
- Parse stage must honor profile_id in normal wizard flow.
- ContextDefaults must support content_patterns + allow_user_override with enforcement.
- Profile-driven UI experience (table list + defaults) must be exposed via API and used by frontend.
- Output aggregation/join builder must exist and be wired.
- Strategy/config fidelity: TableSelect/SelectConfig must match plan (fields, flatten, headers inference, etc.).

## Constraints / Sources (bottom-up)
- **Contracts (Tier 0):** shared/contracts/dat/profile (profile structure, table/output definitions). Align loader & APIs to contract fields.
- **ADRs:** ADR-0011 (profile-driven extraction), ADR-0040 (streaming), ADR-0041 (UI wizard), ADR-0009/0031/0032 (contracts, errors, idempotency), ADR-0033 (AI-friendly patterns).
- **SPECs:** SPEC-DAT-0011/0012 (profile schema, strategies), SPEC-DAT-0004 (streaming), SPEC-DAT-0002 (flow), SPEC-0034 (API naming).

## Work Items

### A. Parse stage wiring (profile_id propagation)
1) **ParseConfig population:** In `routes.py` lock_parse, pull `profile_id` from context stage artifact or run state and set `config.profile_id`. If missing and required, raise 400.
2) **Execute path:** Ensure `execute_parse` uses `config.profile_id` to load profile and chooses ProfileExecutor path by default when present; legacy path only when no profile.
3) **Tests:** integration test for parse lock with profile set; verify ProfileExecutor path called and outputs parquet; error when profile missing.

### B. ContextDefaults content_patterns + allowlist
1) **Loader:** Add `ContentPattern` dataclass to `profile_loader` and parse `context_defaults.content_patterns` and `allow_user_override` fields from YAML/contracts.
2) **Extractor:** Update `ContextExtractor` to use `context_defaults.content_patterns` (JSONPath) for priority 2; enforce allowlist for user overrides; add `on_fail` handling (warn/error/skip) for JSONPath similar to regex.
3) **Contracts alignment:** Ensure fields/types match contract defaults; add validation if pattern missing path/field.
4) **Tests:** unit tests for priority ordering, allowlist enforcement, on_fail behaviors, content_patterns defaulting.

### C. Strategy/config fidelity
1) **TableSelect:** Expand to include fields: `flatten_nested`, `flatten_separator`, `fields`, `infer_headers`, `default_headers`, `id_vars`, `value_vars`, `var_name`, `value_name`, join configs, etc., matching SelectConfig.
2) **SelectConfig build:** Map all TableSelect fields into SelectConfig in ProfileExecutor. Ensure strategies consume new fields where relevant (flat_object flatten, headers_data infer/default headers, array_of_objects fields filter, repeat_over preserves new fields).
3) **Validation:** Add config validation errors surfaced via logger/exception.
4) **Tests:** unit tests per strategy covering new config knobs.

### D. Output aggregation & joins
1) **Implement `output_builder.py`:** Build outputs from `default_outputs`/`optional_outputs`, apply include_context, aggregations, joins (leveraging AggregationConfig/JoinOutputConfig). Deterministic inputs/outputs.
2) **Integration in parse:** After transforms, build outputs; persist artifacts (per ADR-0014); honor selection of outputs; propagate context columns when include_context.
3) **Tests:** unit tests for output builder (concat, aggregations, joins); integration ensuring outputs exist in parse result manifest.

### E. API endpoints for profile-driven UI
1) **Tables endpoint:** Add `GET /api/dat/profiles/{profile_id}/tables` returning levels, tables, and UI config (table_selection defaults/grouping). Source from profile loader.
2) **Preview endpoint:** If needed, `GET /api/dat/runs/{run_id}/profile-preview` (or reuse existing) to return sampled rows honoring `ui.preview.max_rows`.
3) **Frontend:** TableSelectionPanel fetches profile tables endpoint; groups by level; applies default_selected; PreviewPanel uses profile preview endpoint.
4) **Tests:** API response schema test; frontend unit/integration (if present) or contract test for endpoint shape.

### F. Streaming/size safeguards (consistency with ADR-0040)
- Ensure ProfileExecutor honors streaming thresholds when file size > 10MB (if not already), and parse lock path uses same thresholds.

## Sequencing (deterministic)
1) Expand contracts/loader/config fidelity (B, C prerequisites for others).
2) Wire parse lock profile_id (A) after loader changes.
3) Implement output builder and integrate (D).
4) Add UI-facing endpoints (E) once data shapes stable.
5) Update tests across units/integration; regenerate docs if needed (OpenAPI/JSON Schema).
6) Document profile_id flow (Option B): add SPEC-DAT-0002 addendum describing where profile_id is stored (run metadata), how Context sets it, how Parse consumes it, and fallback rules (CreateRun initial value, Context override). Keep ADRs unchanged; use spec as SSOT narrative.

## Verification Plan
- Unit: ContextExtractor, strategies, output builder.
- Integration: parse lock with profile_id executes ProfileExecutor; outputs generated; profile tables endpoint returns grouped tables and UI defaults; profile preview returns limited rows.
- Contracts: `tools/gen_json_schema.py` (if required) and OpenAPI drift check; lint/ruff; pytest suites under tests/unit/dat/profiles and relevant integration tests.

## Risk/Notes
- Ensure backward-compatible default behavior when no profile_id (legacy path). Solo-dev rule allows clean break; prefer explicit error if profile required but missing.
- Keep TableSelect/SelectConfig under 500 lines file size; split modules if needed.
- Remove dead code during refactor per Rule 7.
