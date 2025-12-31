"""Semantic ADR↔SPEC Connection Audit Tool.

This script performs a comprehensive semantic analysis of all ADRs and SPECs to:
1. Validate existing connections are semantically correct
2. Identify MISSING connections that should exist based on content analysis
3. Generate a full audit report with recommendations

Per SOLO-DEV ETHOS: Deterministic, first-principles evaluation.
"""

import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent


@dataclass
class Document:
    """Represents an ADR or SPEC document."""

    id: str
    doc_type: str  # 'adr' or 'spec'
    title: str
    file_path: Path
    scope: str
    tags: list[str]
    references: list[str]
    # ADR-specific
    implementation_specs: list[str] = field(default_factory=list)
    guardrails: list[dict] = field(default_factory=list)
    # SPEC-specific
    implements_adr: list[str] = field(default_factory=list)
    tier_0_contracts: list[str] = field(default_factory=list)
    # Content for semantic analysis
    context: str = ""
    decision: str = ""
    purpose: str = ""
    content_keywords: set = field(default_factory=set)


@dataclass
class ConnectionAudit:
    """Result of connection validation."""

    source_id: str
    target_id: str
    connection_type: str  # 'implements', 'references', 'cross_cutting'
    status: str  # 'valid', 'invalid', 'missing', 'one_way'
    reason: str
    fix_action: str | None = None


def load_json_file(path: Path) -> dict[str, Any] | None:
    """Load JSON file safely."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  Warning: Could not load {path}: {e}")
        return None


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from text for semantic matching."""
    if not text:
        return set()
    # Normalize and split
    text = text.lower()
    # Remove common words
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "must", "shall", "can", "need", "dare",
        "this", "that", "these", "those", "and", "or", "but", "if", "then",
        "else", "when", "where", "why", "how", "all", "each", "every", "both",
        "few", "more", "most", "other", "some", "such", "no", "nor", "not",
        "only", "own", "same", "so", "than", "too", "very", "just", "for",
        "with", "about", "against", "between", "into", "through", "during",
        "before", "after", "above", "below", "to", "from", "up", "down", "in",
        "out", "on", "off", "over", "under", "again", "further", "once", "of",
    }
    words = re.findall(r'\b[a-z][a-z0-9_-]{2,}\b', text)
    return {w for w in words if w not in stop_words and len(w) > 3}


def normalize_id(ref: str) -> str:
    """Extract normalized ID from reference string."""
    if isinstance(ref, dict):
        ref = ref.get("id", "")
    if not isinstance(ref, str):
        return ""
    # Handle formats like "ADR-0001_title", "ADR-0001#anchor", "ADR-0001: description"
    ref = ref.split("_")[0].split("#")[0].split(":")[0].strip()
    return ref


def load_all_adrs() -> dict[str, Document]:
    """Load all ADR documents."""
    adr_root = PROJECT_ROOT / ".adrs"
    adrs = {}

    for folder in ["core", "dat", "pptx", "sov", "devtools", "shared"]:
        folder_path = adr_root / folder
        if not folder_path.exists():
            continue
        for json_file in folder_path.glob("*.json"):
            data = load_json_file(json_file)
            if not data:
                continue

            adr_id = normalize_id(data.get("id", json_file.stem.split("_")[0]))
            decision_details = data.get("decision_details", {})
            impl_specs = decision_details.get("implementation_specs", [])
            # Normalize impl_specs
            impl_specs = [normalize_id(s) for s in impl_specs if normalize_id(s).startswith("SPEC-")]

            context = data.get("context", "")
            decision = data.get("decision_primary", "")

            doc = Document(
                id=adr_id,
                doc_type="adr",
                title=data.get("title", ""),
                file_path=json_file,
                scope=data.get("scope", "core"),
                tags=data.get("tags", []),
                references=data.get("references", []),
                implementation_specs=impl_specs,
                guardrails=data.get("guardrails", []),
                context=context,
                decision=decision,
                content_keywords=extract_keywords(f"{context} {decision} {data.get('title', '')}"),
            )
            adrs[adr_id] = doc

    return adrs


def load_all_specs() -> dict[str, Document]:
    """Load all SPEC documents."""
    spec_root = PROJECT_ROOT / "docs" / "specs"
    specs = {}

    for folder in ["core", "dat", "pptx", "sov", "devtools"]:
        folder_path = spec_root / folder
        if not folder_path.exists():
            continue
        for json_file in folder_path.glob("*.json"):
            data = load_json_file(json_file)
            if not data:
                continue

            spec_id = normalize_id(data.get("id", json_file.stem.split("_")[0]))
            impl_adrs = data.get("implements_adr", [])
            if isinstance(impl_adrs, str):
                impl_adrs = [impl_adrs]
            impl_adrs = [normalize_id(a) for a in impl_adrs]

            purpose = data.get("purpose", "")
            overview = data.get("overview", {})
            if isinstance(overview, dict):
                purpose = overview.get("purpose", purpose)

            doc = Document(
                id=spec_id,
                doc_type="spec",
                title=data.get("title", ""),
                file_path=json_file,
                scope=data.get("scope", "core"),
                tags=data.get("tags", []),
                references=data.get("references", []),
                implements_adr=impl_adrs,
                tier_0_contracts=data.get("tier_0_contracts", []),
                purpose=purpose,
                content_keywords=extract_keywords(f"{purpose} {data.get('title', '')}"),
            )
            specs[spec_id] = doc

    return specs


def compute_semantic_similarity(doc1: Document, doc2: Document) -> float:
    """Compute simple keyword overlap similarity between two documents."""
    if not doc1.content_keywords or not doc2.content_keywords:
        return 0.0
    intersection = doc1.content_keywords & doc2.content_keywords
    union = doc1.content_keywords | doc2.content_keywords
    if not union:
        return 0.0
    return len(intersection) / len(union)


def audit_connections(adrs: dict[str, Document], specs: dict[str, Document]) -> list[ConnectionAudit]:
    """Perform full connection audit."""
    audits = []

    # 1. Check SPEC → ADR connections (implements_adr)
    print("\n[1/4] Auditing SPEC → ADR connections...")
    for spec_id, spec in specs.items():
        for adr_ref in spec.implements_adr:
            adr_id = normalize_id(adr_ref)
            if adr_id not in adrs:
                audits.append(ConnectionAudit(
                    source_id=spec_id,
                    target_id=adr_id,
                    connection_type="implements",
                    status="invalid",
                    reason=f"SPEC {spec_id} references non-existent ADR {adr_id}",
                    fix_action=f"Remove {adr_id} from {spec_id}.implements_adr",
                ))
                continue

            adr = adrs[adr_id]
            # Check bi-directional
            if spec_id not in adr.implementation_specs:
                audits.append(ConnectionAudit(
                    source_id=spec_id,
                    target_id=adr_id,
                    connection_type="implements",
                    status="one_way",
                    reason=f"SPEC {spec_id} implements {adr_id}, but ADR doesn't list SPEC",
                    fix_action=f"Add {spec_id} to {adr_id}.decision_details.implementation_specs",
                ))
            else:
                # Check semantic validity
                similarity = compute_semantic_similarity(spec, adr)
                if similarity < 0.05:
                    audits.append(ConnectionAudit(
                        source_id=spec_id,
                        target_id=adr_id,
                        connection_type="implements",
                        status="questionable",
                        reason=f"Low semantic similarity ({similarity:.2%}) - verify connection is intentional",
                    ))
                else:
                    audits.append(ConnectionAudit(
                        source_id=spec_id,
                        target_id=adr_id,
                        connection_type="implements",
                        status="valid",
                        reason=f"Bi-directional, semantic similarity: {similarity:.2%}",
                    ))

    # 2. Check ADR → SPEC connections (implementation_specs)
    print("[2/4] Auditing ADR → SPEC connections...")
    for adr_id, adr in adrs.items():
        for spec_ref in adr.implementation_specs:
            spec_id = normalize_id(spec_ref)
            if spec_id not in specs:
                audits.append(ConnectionAudit(
                    source_id=adr_id,
                    target_id=spec_id,
                    connection_type="implemented_by",
                    status="invalid",
                    reason=f"ADR {adr_id} references non-existent SPEC {spec_id}",
                    fix_action=f"Remove {spec_id} from {adr_id}.decision_details.implementation_specs",
                ))
                continue

            spec = specs[spec_id]
            # Check bi-directional
            if adr_id not in spec.implements_adr:
                audits.append(ConnectionAudit(
                    source_id=adr_id,
                    target_id=spec_id,
                    connection_type="implemented_by",
                    status="one_way",
                    reason=f"ADR {adr_id} claims {spec_id}, but SPEC doesn't reference ADR",
                    fix_action=f"Add {adr_id} to {spec_id}.implements_adr",
                ))

    # 3. Check ADR → ADR cross-references
    print("[3/4] Auditing ADR → ADR cross-references...")
    for adr_id, adr in adrs.items():
        for ref in adr.references:
            if not isinstance(ref, str):
                continue
            ref_id = normalize_id(ref)
            if not ref_id.startswith("ADR-"):
                continue
            if ref_id not in adrs:
                audits.append(ConnectionAudit(
                    source_id=adr_id,
                    target_id=ref_id,
                    connection_type="references",
                    status="invalid",
                    reason=f"ADR {adr_id} references non-existent ADR {ref_id}",
                ))
                continue

            target_adr = adrs[ref_id]
            # Check if reverse reference exists
            target_refs = [normalize_id(r) for r in target_adr.references if isinstance(r, str)]
            if adr_id not in target_refs:
                audits.append(ConnectionAudit(
                    source_id=adr_id,
                    target_id=ref_id,
                    connection_type="references",
                    status="one_way",
                    reason=f"ADR {adr_id} references {ref_id}, but {ref_id} doesn't reference back",
                    fix_action=f"Add {adr_id} to {ref_id}.references",
                ))

    # 4. Find MISSING connections based on semantic analysis
    print("[4/4] Identifying potentially missing connections...")
    SIMILARITY_THRESHOLD = 0.15  # 15% keyword overlap suggests connection

    for spec_id, spec in specs.items():
        for adr_id, adr in adrs.items():
            # Skip if already connected
            if adr_id in spec.implements_adr:
                continue
            if spec_id in adr.implementation_specs:
                continue

            similarity = compute_semantic_similarity(spec, adr)
            if similarity >= SIMILARITY_THRESHOLD:
                # Check scope alignment
                scope_match = spec.scope == adr.scope or adr.scope == "core"
                if scope_match:
                    audits.append(ConnectionAudit(
                        source_id=spec_id,
                        target_id=adr_id,
                        connection_type="potential_implements",
                        status="missing",
                        reason=f"High semantic similarity ({similarity:.2%}) suggests {spec_id} may implement {adr_id}",
                        fix_action=f"Review: Should {spec_id} implement {adr_id}?",
                    ))

    # 5. Find orphan ADRs (no SPECs)
    print("[5/5] Identifying orphan ADRs...")
    for adr_id, adr in adrs.items():
        has_implementing_spec = False
        for spec in specs.values():
            if adr_id in spec.implements_adr:
                has_implementing_spec = True
                break
        if not has_implementing_spec and not adr.implementation_specs:
            audits.append(ConnectionAudit(
                source_id=adr_id,
                target_id="(none)",
                connection_type="orphan",
                status="missing",
                reason=f"ADR {adr_id} has no implementing SPECs - may need SPEC or is policy-only",
            ))

    return audits


def print_audit_report(audits: list[ConnectionAudit], adrs: dict, specs: dict):
    """Print comprehensive audit report."""
    print("\n" + "=" * 80)
    print("SEMANTIC ADR↔SPEC CONNECTION AUDIT REPORT")
    print("=" * 80)
    print(f"\nTotal ADRs: {len(adrs)}")
    print(f"Total SPECs: {len(specs)}")
    print(f"Total connections audited: {len(audits)}")

    # Group by status
    by_status = defaultdict(list)
    for audit in audits:
        by_status[audit.status].append(audit)

    print(f"\n{'Status':<15} {'Count':<10}")
    print("-" * 25)
    for status in ["valid", "one_way", "missing", "invalid", "questionable"]:
        count = len(by_status.get(status, []))
        print(f"{status:<15} {count:<10}")

    # Print issues by category
    if by_status.get("invalid"):
        print("\n" + "=" * 80)
        print("ERRORS: Invalid References (pointing to non-existent artifacts)")
        print("=" * 80)
        for audit in by_status["invalid"]:
            print(f"  ✗ {audit.source_id} → {audit.target_id}")
            print(f"    {audit.reason}")
            if audit.fix_action:
                print(f"    FIX: {audit.fix_action}")

    if by_status.get("one_way"):
        print("\n" + "=" * 80)
        print("WARNINGS: One-Way References (bi-directional gap)")
        print("=" * 80)
        for audit in by_status["one_way"]:
            print(f"  ⚠ [{audit.connection_type}] {audit.source_id} → {audit.target_id}")
            print(f"    {audit.reason}")
            if audit.fix_action:
                print(f"    FIX: {audit.fix_action}")

    if by_status.get("missing"):
        print("\n" + "=" * 80)
        print("INFO: Potentially Missing Connections (semantic analysis)")
        print("=" * 80)
        for audit in by_status["missing"]:
            print(f"  ℹ [{audit.connection_type}] {audit.source_id} → {audit.target_id}")
            print(f"    {audit.reason}")
            if audit.fix_action:
                print(f"    ACTION: {audit.fix_action}")

    if by_status.get("questionable"):
        print("\n" + "=" * 80)
        print("REVIEW: Low Semantic Similarity (verify intentional)")
        print("=" * 80)
        for audit in by_status["questionable"]:
            print(f"  ? {audit.source_id} → {audit.target_id}")
            print(f"    {audit.reason}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    valid_count = len(by_status.get("valid", []))
    total_connections = len([a for a in audits if a.connection_type in ("implements", "implemented_by")])
    one_way_count = len(by_status.get("one_way", []))
    missing_count = len([a for a in by_status.get("missing", []) if a.connection_type == "potential_implements"])
    orphan_count = len([a for a in by_status.get("missing", []) if a.connection_type == "orphan"])

    print(f"  Valid bi-directional connections: {valid_count}")
    print(f"  One-way connections needing fix: {one_way_count}")
    print(f"  Potentially missing connections: {missing_count}")
    print(f"  Orphan ADRs (no SPECs): {orphan_count}")

    return by_status


def export_audit_json(audits: list[ConnectionAudit], output_path: Path):
    """Export audit results to JSON."""
    data = {
        "total_audits": len(audits),
        "by_status": {},
        "audits": [],
    }

    by_status = defaultdict(int)
    for audit in audits:
        by_status[audit.status] += 1
        data["audits"].append({
            "source_id": audit.source_id,
            "target_id": audit.target_id,
            "connection_type": audit.connection_type,
            "status": audit.status,
            "reason": audit.reason,
            "fix_action": audit.fix_action,
        })

    data["by_status"] = dict(by_status)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"\nAudit exported to: {output_path}")


def main():
    print("=" * 80)
    print("Semantic ADR↔SPEC Connection Audit")
    print("Per ADR-0010, ADR-0016: Full Cross-Reference Validation")
    print("=" * 80)

    print("\nLoading ADRs...")
    adrs = load_all_adrs()
    print(f"  Loaded {len(adrs)} ADRs")

    print("\nLoading SPECs...")
    specs = load_all_specs()
    print(f"  Loaded {len(specs)} SPECs")

    print("\nPerforming semantic audit...")
    audits = audit_connections(adrs, specs)

    by_status = print_audit_report(audits, adrs, specs)

    # Export to JSON
    output_path = PROJECT_ROOT / "semantic-audit-report.json"
    export_audit_json(audits, output_path)

    return by_status


if __name__ == "__main__":
    main()
