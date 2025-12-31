#!/usr/bin/env python
"""Check for reference drift between ADRs, SPECs, Contracts, and Docs.

Per ADR-0010: Type Safety & Contract Discipline.
Per ADR-0016: 3-Tier Document Model.

This script validates cross-references between:
- ADRs (Architecture Decision Records)
- SPECs (Specifications)
- Contracts (Pydantic models in shared/contracts/)
- Docs (SPEC_INDEX.md, ADR_INDEX.md)

Validation includes:
- Bi-directional ADR ↔ SPEC references (mutual consistency)
- Bi-directional ADR ↔ ADR references
- ADRs without any implementing SPECs (orphan detection)
- Broken references to non-existent artifacts

Usage:
    python tools/check_reference_drift.py [--fail-on-error] [--json-output report.json]
    python tools/check_reference_drift.py --autofix  # Auto-fix detected issues

Exit codes:
    0 - No drift detected
    1 - Non-critical drift detected (warnings)
    2 - Critical drift detected (broken references)
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent


class DriftSeverity(str, Enum):
    """Severity levels for reference drift."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass
class DriftItem:
    """Single drift detection result with actionable fix information."""

    source_type: str  # ADR, SPEC, INDEX
    source_id: str
    target_type: str  # ADR, SPEC, CONTRACT
    target_id: str
    severity: DriftSeverity
    message: str
    source_path: Path | None = None  # File to modify for fix
    target_path: Path | None = None  # Related file
    fix_action: str | None = None  # Action to take: "add_reference", "remove_reference"
    fix_field: str | None = None  # JSON field to modify
    fix_value: Any = None  # Value to add/set


@dataclass
class DriftReport:
    """Full drift report."""

    items: list[DriftItem] = field(default_factory=list)
    adr_count: int = 0
    spec_count: int = 0
    contract_modules_checked: int = 0

    @property
    def error_count(self) -> int:
        """Count of error severity items."""
        return sum(1 for item in self.items if item.severity == DriftSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning severity items."""
        return sum(1 for item in self.items if item.severity == DriftSeverity.WARNING)


def load_json_file(path: Path) -> dict[str, Any] | None:
    """Load JSON file safely."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  Warning: Could not load {path}: {e}")
        return None


def extract_adr_id(filename: str) -> str:
    """Extract ADR ID from filename (e.g., ADR-0001_title.json -> ADR-0001)."""
    return filename.split("_")[0] if "_" in filename else filename.replace(".json", "")


def extract_spec_id(filename: str) -> str:
    """Extract SPEC ID from filename (e.g., SPEC-0001_title.json -> SPEC-0001)."""
    return filename.split("_")[0] if "_" in filename else filename.replace(".json", "")


def find_all_adrs() -> dict[str, Path]:
    """Find all ADR files and return {ADR_ID: path} mapping."""
    adr_root = PROJECT_ROOT / ".adrs"
    adrs = {}

    for folder in ["core", "dat", "pptx", "sov", "devtools", "shared"]:
        folder_path = adr_root / folder
        if folder_path.exists():
            for json_file in folder_path.glob("*.json"):
                adr_id = extract_adr_id(json_file.name)
                adrs[adr_id] = json_file

    return adrs


def find_all_specs() -> dict[str, Path]:
    """Find all SPEC files and return {SPEC_ID: path} mapping."""
    spec_root = PROJECT_ROOT / "docs" / "specs"
    specs = {}

    for folder in ["core", "dat", "pptx", "sov", "devtools"]:
        folder_path = spec_root / folder
        if folder_path.exists():
            for json_file in folder_path.glob("*.json"):
                spec_id = extract_spec_id(json_file.name)
                specs[spec_id] = json_file

    return specs


def find_all_contract_modules() -> set[str]:
    """Find all contract modules in shared/contracts/."""
    contracts_root = PROJECT_ROOT / "shared" / "contracts"
    modules = set()

    if not contracts_root.exists():
        return modules

    for py_file in contracts_root.rglob("*.py"):
        if py_file.name.startswith("_"):
            continue
        # Convert path to module name
        relative = py_file.relative_to(PROJECT_ROOT)
        module = str(relative).replace("/", ".").replace("\\", ".").replace(".py", "")
        modules.add(module)

    return modules


def validate_adr_references(adrs: dict[str, Path], specs: dict[str, Path]) -> list[DriftItem]:
    """Validate references within ADR files."""
    items = []

    for adr_id, adr_path in adrs.items():
        adr_data = load_json_file(adr_path)
        if not adr_data:
            continue

        # Check implementation_specs references
        impl_specs = adr_data.get("decision_details", {}).get("implementation_specs", [])
        for spec_ref in impl_specs:
            # Handle dict format (e.g., {"id": "SPEC-0001", "title": "..."})
            if isinstance(spec_ref, dict):
                spec_ref = spec_ref.get("id", "")
            # Skip non-SPEC references (shadcn/ui, shared.contracts, docs/, etc.)
            if not isinstance(spec_ref, str) or not spec_ref.startswith("SPEC-"):
                continue
            # Extract SPEC ID from reference (e.g., "SPEC-0001_title" or "SPEC-0001")
            spec_id = spec_ref.split("_")[0] if "_" in spec_ref else spec_ref
            if spec_id not in specs:
                items.append(DriftItem(
                    source_type="ADR",
                    source_id=adr_id,
                    target_type="SPEC",
                    target_id=spec_id,
                    severity=DriftSeverity.ERROR,
                    message=f"ADR {adr_id} references non-existent SPEC: {spec_id}",
                ))

        # Check ADR cross-references in 'references' field
        references = adr_data.get("references", [])
        for ref in references:
            if isinstance(ref, str) and ref.startswith("ADR-"):
                # Extract ADR ID from reference string
                ref_id = ref.split("_")[0].split(":")[0]
                if ref_id not in adrs:
                    items.append(DriftItem(
                        source_type="ADR",
                        source_id=adr_id,
                        target_type="ADR",
                        target_id=ref_id,
                        severity=DriftSeverity.ERROR,
                        message=f"ADR {adr_id} references non-existent ADR: {ref_id}",
                    ))

    return items


def validate_spec_references(
    specs: dict[str, Path],
    adrs: dict[str, Path],
    contract_modules: set[str],
) -> list[DriftItem]:
    """Validate references within SPEC files."""
    items = []

    for spec_id, spec_path in specs.items():
        spec_data = load_json_file(spec_path)
        if not spec_data:
            continue

        # Check implements_adr references (can be string or list)
        impl_adrs = spec_data.get("implements_adr", [])
        if isinstance(impl_adrs, str):
            impl_adrs = [impl_adrs]
        for adr_ref in impl_adrs:
            # Extract ADR ID from reference
            adr_id = adr_ref.split("_")[0] if "_" in adr_ref else adr_ref
            # Handle anchor references like ADR-0018#path-safety
            adr_id = adr_id.split("#")[0]
            if adr_id not in adrs:
                items.append(DriftItem(
                    source_type="SPEC",
                    source_id=spec_id,
                    target_type="ADR",
                    target_id=adr_id,
                    severity=DriftSeverity.ERROR,
                    message=f"SPEC {spec_id} references non-existent ADR: {adr_id}",
                ))

        # Check tier_0_contracts references
        tier0_contracts = spec_data.get("tier_0_contracts", [])
        for contract in tier0_contracts:
            if isinstance(contract, dict):
                module = contract.get("module", "")
            else:
                module = contract

            # Normalize module path
            if module and not module.startswith("shared."):
                module = f"shared.{module}"

            if module and module not in contract_modules:
                # Only warn - module might be planned but not implemented
                items.append(DriftItem(
                    source_type="SPEC",
                    source_id=spec_id,
                    target_type="CONTRACT",
                    target_id=module,
                    severity=DriftSeverity.WARNING,
                    message=f"SPEC {spec_id} references potentially missing contract: {module}",
                ))

    return items


def validate_bidirectional_adr_spec(
    adrs: dict[str, Path], specs: dict[str, Path]
) -> list[DriftItem]:
    """Validate bi-directional ADR ↔ SPEC references.
    
    Checks:
    1. If SPEC references ADR via implements_adr, ADR should list SPEC in implementation_specs
    2. If ADR references SPEC via implementation_specs, SPEC should reference ADR
    3. ADRs without any implementing SPECs (orphan ADRs)
    """
    items = []

    # Build reverse lookup: which SPECs implement each ADR
    adr_to_specs: dict[str, list[str]] = {adr_id: [] for adr_id in adrs}
    spec_implements: dict[str, list[str]] = {}  # SPEC -> list of ADRs it implements

    for spec_id, spec_path in specs.items():
        spec_data = load_json_file(spec_path)
        if not spec_data:
            continue

        impl_adrs = spec_data.get("implements_adr", [])
        if isinstance(impl_adrs, str):
            impl_adrs = [impl_adrs]

        normalized_adrs = []
        for adr_ref in impl_adrs:
            adr_id = adr_ref.split("_")[0] if "_" in adr_ref else adr_ref
            adr_id = adr_id.split("#")[0]  # Handle anchors
            normalized_adrs.append(adr_id)
            if adr_id in adr_to_specs:
                adr_to_specs[adr_id].append(spec_id)

        spec_implements[spec_id] = normalized_adrs

    # Build forward lookup: which SPECs each ADR claims
    adr_claims_specs: dict[str, list[str]] = {}

    for adr_id, adr_path in adrs.items():
        adr_data = load_json_file(adr_path)
        if not adr_data:
            continue

        impl_specs = adr_data.get("decision_details", {}).get("implementation_specs", [])
        normalized_specs = []
        for spec_ref in impl_specs:
            if isinstance(spec_ref, dict):
                spec_ref = spec_ref.get("id", "")
            if not isinstance(spec_ref, str) or not spec_ref.startswith("SPEC-"):
                continue
            spec_id = spec_ref.split("_")[0] if "_" in spec_ref else spec_ref
            normalized_specs.append(spec_id)

        adr_claims_specs[adr_id] = normalized_specs

    # Check 1: SPEC → ADR but ADR doesn't list SPEC
    for spec_id, impl_adrs in spec_implements.items():
        spec_path = specs.get(spec_id)
        for adr_id in impl_adrs:
            if adr_id not in adrs:
                continue  # Already caught by validate_spec_references
            adr_path = adrs[adr_id]
            claimed_specs = adr_claims_specs.get(adr_id, [])
            if spec_id not in claimed_specs:
                items.append(DriftItem(
                    source_type="SPEC",
                    source_id=spec_id,
                    target_type="ADR",
                    target_id=adr_id,
                    severity=DriftSeverity.WARNING,
                    message=f"SPEC {spec_id} implements {adr_id}, but ADR doesn't list this SPEC in implementation_specs",
                    source_path=spec_path,
                    target_path=adr_path,
                    fix_action="add_reference",
                    fix_field="decision_details.implementation_specs",
                    fix_value=spec_id,
                ))

    # Check 2: ADR → SPEC but SPEC doesn't reference ADR
    for adr_id, claimed_specs in adr_claims_specs.items():
        adr_path = adrs.get(adr_id)
        for spec_id in claimed_specs:
            if spec_id not in specs:
                continue  # Already caught by validate_adr_references
            spec_path = specs[spec_id]
            spec_adrs = spec_implements.get(spec_id, [])
            if adr_id not in spec_adrs:
                items.append(DriftItem(
                    source_type="ADR",
                    source_id=adr_id,
                    target_type="SPEC",
                    target_id=spec_id,
                    severity=DriftSeverity.WARNING,
                    message=f"ADR {adr_id} claims {spec_id} as implementation, but SPEC doesn't reference this ADR",
                    source_path=adr_path,
                    target_path=spec_path,
                    fix_action="add_reference",
                    fix_field="implements_adr",
                    fix_value=adr_id,
                ))

    # Check 3: Orphan ADRs (no implementing SPECs)
    for adr_id, implementing_specs in adr_to_specs.items():
        if not implementing_specs:
            adr_path = adrs[adr_id]
            items.append(DriftItem(
                source_type="ADR",
                source_id=adr_id,
                target_type="SPEC",
                target_id="(none)",
                severity=DriftSeverity.INFO,
                message=f"ADR {adr_id} has no implementing SPECs - consider creating a SPEC",
                source_path=adr_path,
                target_path=None,
                fix_action=None,  # Can't autofix - needs manual SPEC creation
                fix_field=None,
                fix_value=None,
            ))

    return items


def validate_bidirectional_adr_adr(adrs: dict[str, Path]) -> list[DriftItem]:
    """Validate bi-directional ADR ↔ ADR references.
    
    Checks if ADR-A references ADR-B, whether ADR-B also references ADR-A.
    """
    items = []

    # Build reference graph
    adr_refs: dict[str, list[str]] = {}

    for adr_id, adr_path in adrs.items():
        adr_data = load_json_file(adr_path)
        if not adr_data:
            continue

        references = adr_data.get("references", [])
        ref_adrs = []
        for ref in references:
            if isinstance(ref, str) and ref.startswith("ADR-"):
                ref_id = ref.split("_")[0].split(":")[0].split("#")[0]
                if ref_id in adrs and ref_id != adr_id:
                    ref_adrs.append(ref_id)

        adr_refs[adr_id] = ref_adrs

    # Check for one-way references
    checked_pairs = set()
    for adr_id, refs in adr_refs.items():
        adr_path = adrs[adr_id]
        for ref_id in refs:
            pair = tuple(sorted([adr_id, ref_id]))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            ref_path = adrs[ref_id]
            reverse_refs = adr_refs.get(ref_id, [])

            if adr_id not in reverse_refs:
                items.append(DriftItem(
                    source_type="ADR",
                    source_id=adr_id,
                    target_type="ADR",
                    target_id=ref_id,
                    severity=DriftSeverity.INFO,
                    message=f"ADR {adr_id} references {ref_id}, but {ref_id} doesn't reference back",
                    source_path=adr_path,
                    target_path=ref_path,
                    fix_action="add_reference",
                    fix_field="references",
                    fix_value=adr_id,
                ))

    return items


def validate_index_references(adrs: dict[str, Path], specs: dict[str, Path]) -> list[DriftItem]:
    """Validate ADR_INDEX.md and SPEC_INDEX.md references."""
    items = []

    # Check ADR_INDEX.md
    adr_index_path = PROJECT_ROOT / ".adrs" / "ADR_INDEX.md"
    if adr_index_path.exists():
        with open(adr_index_path, encoding="utf-8") as f:
            content = f.read()

        # Find ADR references in tables (| ADR-XXXX |)
        import re
        adr_refs = re.findall(r"\|\s*(ADR-\d{4})\s*\|", content)
        for adr_ref in adr_refs:
            if adr_ref not in adrs:
                # Check if it's in the mapping table (old IDs are expected)
                if "Mapping Reference" not in content or adr_ref not in content.split("Mapping Reference")[0]:
                    items.append(DriftItem(
                        source_type="INDEX",
                        source_id="ADR_INDEX.md",
                        target_type="ADR",
                        target_id=adr_ref,
                        severity=DriftSeverity.WARNING,
                        message=f"ADR_INDEX.md references ADR not found as file: {adr_ref}",
                    ))

    # Check SPEC_INDEX.md
    spec_index_path = PROJECT_ROOT / "docs" / "specs" / "SPEC_INDEX.md"
    if spec_index_path.exists():
        with open(spec_index_path, encoding="utf-8") as f:
            content = f.read()

        # Find SPEC references in tables
        import re
        spec_refs = re.findall(r"\|\s*(SPEC-\d{4})\s*\|", content)
        for spec_ref in spec_refs:
            if spec_ref not in specs:
                # Check if it's in the mapping table
                if "Mapping Reference" not in content or spec_ref not in content.split("Mapping Reference")[0]:
                    items.append(DriftItem(
                        source_type="INDEX",
                        source_id="SPEC_INDEX.md",
                        target_type="SPEC",
                        target_id=spec_ref,
                        severity=DriftSeverity.WARNING,
                        message=f"SPEC_INDEX.md references SPEC not found as file: {spec_ref}",
                    ))

    return items


def apply_autofix(items: list[DriftItem]) -> tuple[int, int]:
    """Apply automatic fixes for drift items that support it.
    
    Returns:
        Tuple of (fixed_count, skipped_count)
    """
    fixed = 0
    skipped = 0

    for item in items:
        if not item.fix_action or not item.target_path:
            skipped += 1
            continue

        if item.fix_action == "add_reference":
            try:
                success = _add_reference_to_file(
                    item.target_path, item.fix_field, item.fix_value
                )
                if success:
                    fixed += 1
                    print(f"  ✓ Fixed: Added {item.fix_value} to {item.fix_field} in {item.target_path.name}")
                else:
                    skipped += 1
                    print(f"  ✗ Skipped: Could not add reference to {item.target_path.name}")
            except Exception as e:
                skipped += 1
                print(f"  ✗ Error fixing {item.target_path.name}: {e}")
        else:
            skipped += 1

    return fixed, skipped


def _add_reference_to_file(file_path: Path, field_path: str, value: Any) -> bool:
    """Add a reference to a JSON file at the specified field path.
    
    Args:
        file_path: Path to JSON file
        field_path: Dot-separated path to field (e.g., "decision_details.implementation_specs")
        value: Value to add to the field (appended if list, set if scalar)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return False

    # Navigate to parent of target field
    parts = field_path.split(".")
    current = data

    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    final_key = parts[-1]

    # Add value to field
    if final_key not in current:
        current[final_key] = []

    existing = current[final_key]

    if isinstance(existing, list):
        # Check if already present
        if value not in existing:
            existing.append(value)
    elif isinstance(existing, str):
        # Convert to list if single string
        if existing != value:
            current[final_key] = [existing, value]
    else:
        current[final_key] = [value]

    # Write back
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True


def print_report(report: DriftReport, show_fix_hints: bool = True) -> None:
    """Print drift report to console with actionable fix information."""
    print("\n" + "=" * 60)
    print("Reference Drift Detection Report")
    print("=" * 60)

    print("\nScanned:")
    print(f"  - {report.adr_count} ADRs")
    print(f"  - {report.spec_count} SPECs")
    print(f"  - {report.contract_modules_checked} contract modules")

    if not report.items:
        print("\n✓ No reference drift detected - all cross-references are valid")
        return

    # Count by severity
    info_count = sum(1 for item in report.items if item.severity == DriftSeverity.INFO)
    fixable_count = sum(1 for item in report.items if item.fix_action)

    print(f"\nFound {len(report.items)} issues:")
    print(f"  - {report.error_count} errors (broken references)")
    print(f"  - {report.warning_count} warnings (missing bi-directional refs)")
    print(f"  - {info_count} info (recommendations)")
    print(f"  - {fixable_count} auto-fixable with --autofix")

    # Group by severity then source
    by_severity: dict[DriftSeverity, dict[str, list[DriftItem]]] = {
        DriftSeverity.ERROR: {},
        DriftSeverity.WARNING: {},
        DriftSeverity.INFO: {},
    }

    for item in report.items:
        key = f"{item.source_type}:{item.source_id}"
        if key not in by_severity[item.severity]:
            by_severity[item.severity][key] = []
        by_severity[item.severity][key].append(item)

    # Print errors first
    if by_severity[DriftSeverity.ERROR]:
        print("\n" + "-" * 40)
        print("ERRORS (broken references):")
        for source, items in sorted(by_severity[DriftSeverity.ERROR].items()):
            print(f"\n  [{source}]")
            for item in items:
                print(f"    ✗ {item.message}")
                if show_fix_hints and item.source_path:
                    print(f"      File: {item.source_path}")

    # Print warnings
    if by_severity[DriftSeverity.WARNING]:
        print("\n" + "-" * 40)
        print("WARNINGS (bi-directional reference gaps):")
        for source, items in sorted(by_severity[DriftSeverity.WARNING].items()):
            print(f"\n  [{source}]")
            for item in items:
                print(f"    ⚠ {item.message}")
                if show_fix_hints and item.fix_action:
                    print(f"      Fix: Add '{item.fix_value}' to '{item.fix_field}' in {item.target_path.name if item.target_path else 'N/A'}")

    # Print info
    if by_severity[DriftSeverity.INFO]:
        print("\n" + "-" * 40)
        print("INFO (recommendations):")
        for source, items in sorted(by_severity[DriftSeverity.INFO].items()):
            print(f"\n  [{source}]")
            for item in items:
                print(f"    ℹ {item.message}")
                if show_fix_hints and item.source_path:
                    print(f"      File: {item.source_path}")

    if fixable_count > 0:
        print("\n" + "-" * 40)
        print(f"TIP: Run with --autofix to automatically fix {fixable_count} issues")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check for reference drift between ADRs, SPECs, and Contracts"
    )
    parser.add_argument(
        "--fail-on-error",
        action="store_true",
        help="Exit with error code on broken references",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Exit with error code on any warning",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Write report as JSON to file",
    )
    parser.add_argument(
        "--autofix",
        action="store_true",
        help="Automatically fix bi-directional reference issues",
    )
    parser.add_argument(
        "--skip-orphan-check",
        action="store_true",
        help="Skip checking for ADRs without implementing SPECs",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Reference Drift Detection")
    print("Per ADR-0010, ADR-0016: Cross-Reference Validation")
    print("=" * 60)

    # Find all artifacts
    print("\nScanning artifacts...")
    adrs = find_all_adrs()
    specs = find_all_specs()
    contract_modules = find_all_contract_modules()

    print(f"  Found {len(adrs)} ADRs")
    print(f"  Found {len(specs)} SPECs")
    print(f"  Found {len(contract_modules)} contract modules")

    # Validate references
    print("\nValidating references...")
    all_items: list[DriftItem] = []

    print("  Checking ADR → SPEC/ADR references...")
    all_items.extend(validate_adr_references(adrs, specs))

    print("  Checking SPEC → ADR/Contract references...")
    all_items.extend(validate_spec_references(specs, adrs, contract_modules))

    print("  Checking bi-directional ADR ↔ SPEC consistency...")
    bidir_items = validate_bidirectional_adr_spec(adrs, specs)
    if args.skip_orphan_check:
        # Filter out orphan ADR info items
        bidir_items = [i for i in bidir_items if i.target_id != "(none)"]
    all_items.extend(bidir_items)

    print("  Checking bi-directional ADR ↔ ADR consistency...")
    all_items.extend(validate_bidirectional_adr_adr(adrs))

    print("  Checking INDEX → ADR/SPEC references...")
    all_items.extend(validate_index_references(adrs, specs))

    # Build report
    report = DriftReport(
        items=all_items,
        adr_count=len(adrs),
        spec_count=len(specs),
        contract_modules_checked=len(contract_modules),
    )

    print_report(report)

    # Apply autofix if requested
    if args.autofix:
        fixable_items = [i for i in report.items if i.fix_action]
        if fixable_items:
            print("\n" + "=" * 60)
            print("Applying automatic fixes...")
            print("=" * 60)
            fixed, skipped = apply_autofix(fixable_items)
            print(f"\nAutofix complete: {fixed} fixed, {skipped} skipped")
        else:
            print("\nNo auto-fixable issues found.")

    # Write JSON output if requested
    if args.json_output:
        json_report = {
            "adr_count": report.adr_count,
            "spec_count": report.spec_count,
            "contract_modules_checked": report.contract_modules_checked,
            "error_count": report.error_count,
            "warning_count": report.warning_count,
            "items": [
                {
                    "source_type": item.source_type,
                    "source_id": item.source_id,
                    "target_type": item.target_type,
                    "target_id": item.target_id,
                    "severity": item.severity.value,
                    "message": item.message,
                    "source_path": str(item.source_path) if item.source_path else None,
                    "target_path": str(item.target_path) if item.target_path else None,
                    "fix_action": item.fix_action,
                    "fix_field": item.fix_field,
                    "fix_value": item.fix_value,
                }
                for item in report.items
            ],
        }

        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(json_report, f, indent=2)
        print(f"\nJSON report written to: {args.json_output}")

    # Determine exit code
    if args.fail_on_error and report.error_count > 0:
        return 2
    if args.fail_on_warning and report.warning_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
