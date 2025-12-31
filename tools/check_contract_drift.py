#!/usr/bin/env python
"""Check for contract drift between Pydantic models and existing schemas.

Per ADR-0010: Type Safety & Contract Discipline.
Per ADR-0017: Hybrid Semver Contract Versioning.

This script compares current Pydantic contracts against previously
generated JSON schemas to detect breaking changes and drift.

Usage:
    python tools/check_contract_drift.py [--schemas-dir schemas/] [--fail-on-breaking]

Exit codes:
    0 - No drift detected
    1 - Non-breaking drift detected (fields added)
    2 - Breaking drift detected (fields removed, types changed)
"""

import argparse
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class DriftSeverity(str, Enum):
    """Severity levels for contract drift."""

    NONE = "none"
    INFO = "info"  # Cosmetic changes (descriptions, etc.)
    MINOR = "minor"  # Non-breaking additions
    MAJOR = "major"  # Breaking changes


@dataclass
class DriftItem:
    """Single drift detection result."""

    model_name: str
    field_path: str
    change_type: str
    severity: DriftSeverity
    old_value: Any
    new_value: Any
    message: str


@dataclass
class DriftReport:
    """Full drift report for a contract."""

    model_name: str
    module_name: str
    schema_path: Path
    items: list[DriftItem]

    @property
    def has_breaking_changes(self) -> bool:
        """Check if report contains breaking changes."""
        return any(item.severity == DriftSeverity.MAJOR for item in self.items)

    @property
    def has_changes(self) -> bool:
        """Check if report contains any changes."""
        return len(self.items) > 0


def load_existing_schema(schema_path: Path) -> dict[str, Any] | None:
    """Load existing JSON schema from file.

    Args:
        schema_path: Path to schema JSON file.

    Returns:
        Schema dict or None if file doesn't exist.
    """
    if not schema_path.exists():
        return None

    with open(schema_path, encoding="utf-8") as f:
        return json.load(f)


def get_current_schema(model_class: type) -> dict[str, Any]:
    """Generate current JSON schema from Pydantic model.

    Args:
        model_class: Pydantic BaseModel class.

    Returns:
        JSON Schema dictionary.
    """
    return model_class.model_json_schema()


def compare_schemas(
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
    model_name: str,
    path_prefix: str = "",
) -> list[DriftItem]:
    """Compare two JSON schemas and detect drift.

    Args:
        old_schema: Previous schema version.
        new_schema: Current schema version.
        model_name: Name of the model being compared.
        path_prefix: Current path in schema (for nested comparisons).

    Returns:
        List of DriftItem objects describing changes.
    """
    drift_items = []

    # Compare properties
    old_props = old_schema.get("properties", {})
    new_props = new_schema.get("properties", {})

    old_required = set(old_schema.get("required", []))
    new_required = set(new_schema.get("required", []))

    # Check for removed properties (breaking)
    for prop_name in old_props:
        if prop_name not in new_props:
            drift_items.append(DriftItem(
                model_name=model_name,
                field_path=f"{path_prefix}.{prop_name}" if path_prefix else prop_name,
                change_type="field_removed",
                severity=DriftSeverity.MAJOR,
                old_value=old_props[prop_name],
                new_value=None,
                message=f"Field '{prop_name}' was removed (BREAKING)",
            ))

    # Check for added properties
    for prop_name in new_props:
        if prop_name not in old_props:
            # New required field is breaking
            severity = DriftSeverity.MAJOR if prop_name in new_required else DriftSeverity.MINOR
            drift_items.append(DriftItem(
                model_name=model_name,
                field_path=f"{path_prefix}.{prop_name}" if path_prefix else prop_name,
                change_type="field_added",
                severity=severity,
                old_value=None,
                new_value=new_props[prop_name],
                message=f"Field '{prop_name}' was added" + (
                    " as REQUIRED (BREAKING)" if prop_name in new_required else " (optional)"
                ),
            ))

    # Check for type changes in existing properties
    for prop_name in old_props:
        if prop_name not in new_props:
            continue

        old_prop = old_props[prop_name]
        new_prop = new_props[prop_name]

        # Compare types
        old_type = old_prop.get("type") or old_prop.get("anyOf") or old_prop.get("$ref")
        new_type = new_prop.get("type") or new_prop.get("anyOf") or new_prop.get("$ref")

        if old_type != new_type:
            drift_items.append(DriftItem(
                model_name=model_name,
                field_path=f"{path_prefix}.{prop_name}" if path_prefix else prop_name,
                change_type="type_changed",
                severity=DriftSeverity.MAJOR,
                old_value=old_type,
                new_value=new_type,
                message=f"Field '{prop_name}' type changed from {old_type} to {new_type} (BREAKING)",
            ))

        # Recurse into nested objects
        if old_prop.get("type") == "object" and new_prop.get("type") == "object":
            nested_path = f"{path_prefix}.{prop_name}" if path_prefix else prop_name
            drift_items.extend(compare_schemas(
                old_prop, new_prop, model_name, nested_path
            ))

    # Check required field changes
    removed_required = old_required - new_required
    added_required = new_required - old_required

    for field in removed_required:
        if field in new_props:  # Only if field still exists
            drift_items.append(DriftItem(
                model_name=model_name,
                field_path=f"{path_prefix}.{field}" if path_prefix else field,
                change_type="required_removed",
                severity=DriftSeverity.MINOR,
                old_value=True,
                new_value=False,
                message=f"Field '{field}' is no longer required",
            ))

    for field in added_required:
        if field in old_props:  # Only for existing fields becoming required
            drift_items.append(DriftItem(
                model_name=model_name,
                field_path=f"{path_prefix}.{field}" if path_prefix else field,
                change_type="required_added",
                severity=DriftSeverity.MAJOR,
                old_value=False,
                new_value=True,
                message=f"Field '{field}' is now required (BREAKING)",
            ))

    return drift_items


def check_model_drift(
    model_class: type,
    model_name: str,
    module_name: str,
    schemas_dir: Path,
) -> DriftReport:
    """Check drift for a single Pydantic model.

    Args:
        model_class: Pydantic BaseModel class.
        model_name: Name of the model.
        module_name: Source module path.
        schemas_dir: Directory containing existing schemas.

    Returns:
        DriftReport with any detected changes.
    """
    # Determine schema path
    category = module_name.split(".")[2]  # shared.contracts.<category>
    module_short = module_name.split(".")[-1]
    schema_path = schemas_dir / category / f"{module_short}_{model_name}.json"

    # Load existing schema
    old_schema = load_existing_schema(schema_path)

    if old_schema is None:
        return DriftReport(
            model_name=model_name,
            module_name=module_name,
            schema_path=schema_path,
            items=[DriftItem(
                model_name=model_name,
                field_path="",
                change_type="new_model",
                severity=DriftSeverity.MINOR,
                old_value=None,
                new_value=None,
                message=f"New model (no existing schema at {schema_path})",
            )],
        )

    # Generate current schema
    new_schema = get_current_schema(model_class)

    # Compare schemas
    drift_items = compare_schemas(old_schema, new_schema, model_name)

    return DriftReport(
        model_name=model_name,
        module_name=module_name,
        schema_path=schema_path,
        items=drift_items,
    )


def print_report(report: DriftReport) -> None:
    """Print drift report to console.

    Args:
        report: DriftReport to print.
    """
    if not report.has_changes:
        return

    print(f"\n[{report.model_name}] ({report.module_name})")
    print(f"  Schema: {report.schema_path}")

    for item in report.items:
        icon = {
            DriftSeverity.NONE: "·",
            DriftSeverity.INFO: "ℹ",
            DriftSeverity.MINOR: "⚠",
            DriftSeverity.MAJOR: "✗",
        }[item.severity]

        color_prefix = {
            DriftSeverity.NONE: "",
            DriftSeverity.INFO: "",
            DriftSeverity.MINOR: "",
            DriftSeverity.MAJOR: "",
        }[item.severity]

        print(f"  {icon} {item.message}")
        if item.field_path:
            print(f"    Path: {item.field_path}")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check for contract drift between Pydantic models and schemas"
    )
    parser.add_argument(
        "--schemas-dir",
        type=Path,
        default=PROJECT_ROOT / "schemas",
        help="Directory containing existing schemas (default: schemas/)",
    )
    parser.add_argument(
        "--fail-on-breaking",
        action="store_true",
        help="Exit with error code on breaking changes",
    )
    parser.add_argument(
        "--fail-on-any",
        action="store_true",
        help="Exit with error code on any drift",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Write report as JSON to file",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Contract Drift Detection")
    print("=" * 60)

    if not args.schemas_dir.exists():
        print(f"\nWarning: Schemas directory not found: {args.schemas_dir}")
        print("Run 'python tools/gen_json_schema.py' first to generate baseline schemas.")
        return 0

    # Import contract modules
    from tools.gen_json_schema import CONTRACT_MODULES, get_pydantic_models

    all_reports: list[DriftReport] = []
    breaking_count = 0
    drift_count = 0

    for category, modules in CONTRACT_MODULES.items():
        for module_name in modules:
            models = get_pydantic_models(module_name)

            for model_name, model_class in models:
                report = check_model_drift(
                    model_class,
                    model_name,
                    module_name,
                    args.schemas_dir,
                )

                if report.has_changes:
                    all_reports.append(report)
                    drift_count += len(report.items)
                    if report.has_breaking_changes:
                        breaking_count += 1

                    print_report(report)

    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)

    if drift_count == 0:
        print("✓ No drift detected - contracts match schemas")
    else:
        print(f"Found {drift_count} changes in {len(all_reports)} models")
        if breaking_count > 0:
            print(f"  ✗ {breaking_count} models with BREAKING changes")

    # Write JSON output if requested
    if args.json_output:
        json_report = {
            "drift_count": drift_count,
            "breaking_count": breaking_count,
            "reports": [
                {
                    "model_name": r.model_name,
                    "module_name": r.module_name,
                    "schema_path": str(r.schema_path),
                    "has_breaking_changes": r.has_breaking_changes,
                    "items": [
                        {
                            "field_path": i.field_path,
                            "change_type": i.change_type,
                            "severity": i.severity.value,
                            "message": i.message,
                        }
                        for i in r.items
                    ],
                }
                for r in all_reports
            ],
        }

        with open(args.json_output, "w", encoding="utf-8") as f:
            json.dump(json_report, f, indent=2)
        print(f"\nJSON report written to: {args.json_output}")

    # Determine exit code
    if args.fail_on_breaking and breaking_count > 0:
        return 2
    if args.fail_on_any and drift_count > 0:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
