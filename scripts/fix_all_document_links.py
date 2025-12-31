"""Comprehensive Document Link Fixer.

This script applies ALL identified fixes to ADR↔SPEC connections based on:
1. Semantic audit findings from semantic_adr_spec_audit.py
2. User decisions from SESSION_024 review

Actions:
- ADD: Add missing bi-directional references
- REMOVE: Remove invalid/wrong connections
- IMPLEMENT: Add newly identified connections

Per SOLO-DEV ETHOS: Deterministic, automated fixes with verification.
"""

import json
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).parent.parent


def load_json_file(path: Path) -> dict[str, Any] | None:
    """Load JSON file safely."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  ERROR: Could not load {path}: {e}")
        return None


def save_json_file(path: Path, data: dict[str, Any]) -> bool:
    """Save JSON file with proper formatting."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"  ERROR: Could not save {path}: {e}")
        return False


def normalize_id(ref: str) -> str:
    """Extract normalized ID from reference string."""
    if isinstance(ref, dict):
        ref = ref.get("id", "")
    if not isinstance(ref, str):
        return ""
    ref = ref.split("_")[0].split("#")[0].split(":")[0].strip()
    return ref


def find_file_by_id(doc_id: str, doc_type: str) -> Path | None:
    """Find file path for a document ID."""
    if doc_type == "adr":
        search_dirs = [
            PROJECT_ROOT / ".adrs" / "core",
            PROJECT_ROOT / ".adrs" / "dat",
            PROJECT_ROOT / ".adrs" / "pptx",
            PROJECT_ROOT / ".adrs" / "sov",
            PROJECT_ROOT / ".adrs" / "devtools",
        ]
        prefix = "ADR-"
    else:  # spec
        search_dirs = [
            PROJECT_ROOT / "docs" / "specs" / "core",
            PROJECT_ROOT / "docs" / "specs" / "dat",
            PROJECT_ROOT / "docs" / "specs" / "pptx",
            PROJECT_ROOT / "docs" / "specs" / "sov",
            PROJECT_ROOT / "docs" / "specs" / "devtools",
        ]
        prefix = "SPEC-"

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for json_file in search_dir.glob("*.json"):
            if json_file.stem.startswith(doc_id.replace(prefix, f"{prefix}")):
                return json_file
            # Also check if file starts with the ID
            if json_file.stem.split("_")[0] == doc_id:
                return json_file

    return None


def add_to_list_field(data: dict, field_path: str, value: str) -> bool:
    """Add value to a list field in nested dict structure."""
    parts = field_path.split(".")
    current = data

    # Navigate to parent
    for part in parts[:-1]:
        if part not in current:
            current[part] = {}
        current = current[part]

    final_key = parts[-1]

    # Initialize if needed
    if final_key not in current:
        current[final_key] = []

    existing = current[final_key]

    if isinstance(existing, list):
        if value not in existing:
            existing.append(value)
            return True
    elif isinstance(existing, str):
        if existing != value:
            current[final_key] = [existing, value]
            return True

    return False


def remove_from_list_field(data: dict, field_path: str, value: str) -> bool:
    """Remove value from a list field in nested dict structure."""
    parts = field_path.split(".")
    current = data

    # Navigate to parent
    for part in parts[:-1]:
        if part not in current:
            return False
        current = current[part]

    final_key = parts[-1]

    if final_key not in current:
        return False

    existing = current[final_key]

    if isinstance(existing, list):
        # Normalize and check each item
        for i, item in enumerate(existing):
            item_id = normalize_id(item)
            if item_id == value or item == value:
                existing.pop(i)
                return True

    return False


def main():
    print("=" * 80)
    print("Comprehensive Document Link Fixer")
    print("SESSION_024 - User-Approved Fixes")
    print("=" * 80)

    stats = {
        "added": 0,
        "removed": 0,
        "skipped": 0,
        "errors": 0,
    }

    # =========================================================================
    # PHASE 1: Remove invalid connections (User Decision: DISCARD)
    # =========================================================================
    print("\n[PHASE 1] Removing invalid connections...")

    removals = [
        # SPEC-0003 → ADR-0008 is WRONG (0% semantic similarity)
        {
            "file_type": "spec",
            "file_id": "SPEC-0003",
            "field": "implements_adr",
            "value": "ADR-0008",
            "reason": "Wrong link - 0% semantic similarity",
        },
    ]

    for removal in removals:
        file_path = find_file_by_id(removal["file_id"], removal["file_type"])
        if not file_path:
            print(f"  ERROR: Could not find {removal['file_id']}")
            stats["errors"] += 1
            continue

        data = load_json_file(file_path)
        if not data:
            stats["errors"] += 1
            continue

        if remove_from_list_field(data, removal["field"], removal["value"]):
            if save_json_file(file_path, data):
                print(f"  ✓ REMOVED: {removal['file_id']}.{removal['field']} -= {removal['value']}")
                print(f"    Reason: {removal['reason']}")
                stats["removed"] += 1
            else:
                stats["errors"] += 1
        else:
            print(f"  - SKIP: {removal['value']} not found in {removal['file_id']}.{removal['field']}")
            stats["skipped"] += 1

    # =========================================================================
    # PHASE 2: Add missing connections identified by semantic analysis
    # =========================================================================
    print("\n[PHASE 2] Adding missing semantic connections...")

    new_connections = [
        # SPEC-0007 should implement ADR-0026 (16.48% similarity - Dataset Lineage)
        {
            "file_type": "spec",
            "file_id": "SPEC-0007",
            "field": "implements_adr",
            "value": "ADR-0026",
            "reason": "High semantic similarity (16.48%) - Dataset Lineage",
        },
        # SPEC-0029 should implement ADR-0008 (17.65% similarity - Table Availability)
        {
            "file_type": "spec",
            "file_id": "SPEC-0029",
            "field": "implements_adr",
            "value": "ADR-0008",
            "reason": "High semantic similarity (17.65%) - Table Availability",
        },
    ]

    for conn in new_connections:
        file_path = find_file_by_id(conn["file_id"], conn["file_type"])
        if not file_path:
            print(f"  ERROR: Could not find {conn['file_id']}")
            stats["errors"] += 1
            continue

        data = load_json_file(file_path)
        if not data:
            stats["errors"] += 1
            continue

        if add_to_list_field(data, conn["field"], conn["value"]):
            if save_json_file(file_path, data):
                print(f"  ✓ ADDED: {conn['file_id']}.{conn['field']} += {conn['value']}")
                print(f"    Reason: {conn['reason']}")
                stats["added"] += 1
            else:
                stats["errors"] += 1
        else:
            print(f"  - SKIP: {conn['value']} already in {conn['file_id']}.{conn['field']}")
            stats["skipped"] += 1

    # =========================================================================
    # PHASE 3: Run the existing autofix for all bi-directional gaps
    # =========================================================================
    print("\n[PHASE 3] Running comprehensive bi-directional autofix...")
    print("  (Using check_reference_drift.py --autofix)")

    # Import and run the existing autofix
    import subprocess
    result = subprocess.run(
        ["python", "tools/check_reference_drift.py", "--autofix"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

    # Parse autofix output for stats
    for line in result.stdout.split("\n"):
        if "Fixed:" in line:
            try:
                fixed_count = int(line.split("Fixed:")[1].strip().split()[0])
                stats["added"] += fixed_count
            except (IndexError, ValueError):
                pass

    # =========================================================================
    # PHASE 4: Verification
    # =========================================================================
    print("\n[PHASE 4] Verification run...")

    result = subprocess.run(
        ["python", "tools/check_reference_drift.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("FIX SUMMARY")
    print("=" * 80)
    print(f"  References added:   {stats['added']}")
    print(f"  References removed: {stats['removed']}")
    print(f"  Skipped (already):  {stats['skipped']}")
    print(f"  Errors:             {stats['errors']}")

    return stats


if __name__ == "__main__":
    main()
