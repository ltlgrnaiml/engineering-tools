#!/usr/bin/env python
"""Check for reference drift between ADRs, SPECs, Contracts, and Docs.

Per ADR-0010: Type Safety & Contract Discipline.
Per ADR-0016: 3-Tier Document Model.

This script validates cross-references between:
- ADRs (Architecture Decision Records)
- SPECs (Specifications)
- Contracts (Pydantic models in shared/contracts/)
- Docs (SPEC_INDEX.md, ADR_INDEX.md)

Usage:
    python tools/check_reference_drift.py [--fail-on-error] [--json-output report.json]

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
    """Single drift detection result."""

    source_type: str  # ADR, SPEC, INDEX
    source_id: str
    target_type: str  # ADR, SPEC, CONTRACT
    target_id: str
    severity: DriftSeverity
    message: str


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
            # Skip non-SPEC references (shadcn/ui, shared.contracts, docs/, etc.)
            if not spec_ref.startswith("SPEC-"):
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


def print_report(report: DriftReport) -> None:
    """Print drift report to console."""
    print("\n" + "=" * 60)
    print("Reference Drift Detection Report")
    print("=" * 60)

    print(f"\nScanned:")
    print(f"  - {report.adr_count} ADRs")
    print(f"  - {report.spec_count} SPECs")
    print(f"  - {report.contract_modules_checked} contract modules")

    if not report.items:
        print("\n✓ No reference drift detected - all cross-references are valid")
        return

    print(f"\nFound {len(report.items)} issues:")
    print(f"  - {report.error_count} errors (broken references)")
    print(f"  - {report.warning_count} warnings (potential issues)")

    # Group by source
    by_source: dict[str, list[DriftItem]] = {}
    for item in report.items:
        key = f"{item.source_type}:{item.source_id}"
        if key not in by_source:
            by_source[key] = []
        by_source[key].append(item)

    print("\nDetails:")
    for source, items in sorted(by_source.items()):
        print(f"\n  [{source}]")
        for item in items:
            icon = "✗" if item.severity == DriftSeverity.ERROR else "⚠"
            print(f"    {icon} {item.message}")


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
