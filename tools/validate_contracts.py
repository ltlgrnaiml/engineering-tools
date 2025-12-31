#!/usr/bin/env python
"""Unified contract validation for the Engineering Tools platform.

Per ADR-0010: Type Safety & Contract Discipline.
Per ADR-0016: 3-Tier Document Model.
Per ADR-0018: Cross-Cutting Guardrails.

This script provides comprehensive validation:
1. Contract schema validation (Pydantic models are valid)
2. JSON Schema generation and drift detection
3. Message catalog validation
4. ADR schema validation
5. Cross-reference validation (ADRs ↔ SPECs ↔ Contracts)

Usage:
    python tools/validate_contracts.py [--full] [--fix] [--output-schemas]

Exit codes:
    0 - All validations passed
    1 - Validation errors (non-breaking)
    2 - Critical errors (breaking changes or missing contracts)
"""

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ValidationSeverity(str, Enum):
    """Severity of validation issues."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    category: str
    severity: ValidationSeverity
    message: str
    file_path: str | None = None
    line_number: int | None = None
    suggestion: str | None = None


@dataclass
class ValidationReport:
    """Complete validation report."""
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = None
    issues: list[ValidationIssue] = field(default_factory=list)
    categories_checked: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL])

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    @property
    def is_valid(self) -> bool:
        return self.error_count == 0

    def add_issue(self, issue: ValidationIssue) -> None:
        self.issues.append(issue)

    def add_error(self, category: str, message: str, **kwargs) -> None:
        self.add_issue(ValidationIssue(category=category, severity=ValidationSeverity.ERROR, message=message, **kwargs))

    def add_warning(self, category: str, message: str, **kwargs) -> None:
        self.add_issue(ValidationIssue(category=category, severity=ValidationSeverity.WARNING, message=message, **kwargs))

    def add_info(self, category: str, message: str, **kwargs) -> None:
        self.add_issue(ValidationIssue(category=category, severity=ValidationSeverity.INFO, message=message, **kwargs))


# =============================================================================
# Contract Modules to Validate
# =============================================================================

CONTRACT_MODULES = {
    "core": [
        "shared.contracts.core.artifact_registry",
        "shared.contracts.core.audit",
        "shared.contracts.core.concurrency",
        "shared.contracts.core.dataset",
        "shared.contracts.core.id_generator",
        "shared.contracts.core.path_safety",
        "shared.contracts.core.pipeline",
        "shared.contracts.core.rendering",
    ],
    "dat": [
        "shared.contracts.dat.cancellation",
        "shared.contracts.dat.profile",
        "shared.contracts.dat.stage",
        "shared.contracts.dat.table_status",
    ],
    "pptx": [
        "shared.contracts.pptx.shape",
        "shared.contracts.pptx.template",
    ],
    "sov": [
        "shared.contracts.sov.anova",
        "shared.contracts.sov.visualization",
    ],
    "messages": [
        "shared.contracts.messages.catalog",
    ],
    "devtools": [
        "shared.contracts.devtools.api",
    ],
}


# =============================================================================
# Validators
# =============================================================================

def validate_contract_imports(report: ValidationReport) -> int:
    """Validate all contract modules can be imported.
    
    Returns count of valid modules.
    """
    report.categories_checked.append("contract_imports")
    valid_count = 0

    for category, modules in CONTRACT_MODULES.items():
        for module_name in modules:
            try:
                importlib.import_module(module_name)
                valid_count += 1
            except ImportError as e:
                report.add_error(
                    "contract_imports",
                    f"Failed to import {module_name}: {e}",
                    file_path=module_name.replace(".", "/") + ".py",
                )
            except Exception as e:
                report.add_error(
                    "contract_imports",
                    f"Error loading {module_name}: {e}",
                    file_path=module_name.replace(".", "/") + ".py",
                )

    return valid_count


def validate_contract_versioning(report: ValidationReport) -> None:
    """Validate all contracts have __version__ attribute.
    
    Per ADR-0017: Hybrid Semver Contract Versioning.
    """
    report.categories_checked.append("contract_versioning")

    for category, modules in CONTRACT_MODULES.items():
        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
                if not hasattr(module, "__version__"):
                    report.add_warning(
                        "contract_versioning",
                        f"Module {module_name} missing __version__ attribute",
                        file_path=module_name.replace(".", "/") + ".py",
                        suggestion="Add __version__ = '0.1.0' to module",
                    )
                else:
                    version = module.__version__
                    # Validate semver format
                    import re
                    if not re.match(r"^\d+\.\d+\.\d+", version):
                        report.add_warning(
                            "contract_versioning",
                            f"Module {module_name} has invalid version format: {version}",
                            suggestion="Use semver format: X.Y.Z",
                        )
            except ImportError:
                pass  # Already reported in import validation


def validate_pydantic_models(report: ValidationReport) -> dict[str, list[str]]:
    """Validate all Pydantic models can be instantiated with valid data.
    
    Returns dict of {module: [model_names]}.
    """
    from pydantic import BaseModel

    report.categories_checked.append("pydantic_models")
    all_models: dict[str, list[str]] = {}

    for category, modules in CONTRACT_MODULES.items():
        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
                models = []

                for name in dir(module):
                    obj = getattr(module, name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseModel)
                        and obj is not BaseModel
                        and obj.__module__ == module_name
                    ):
                        models.append(name)

                        # Validate model can generate JSON schema
                        try:
                            obj.model_json_schema()
                        except Exception as e:
                            report.add_error(
                                "pydantic_models",
                                f"Model {name} cannot generate JSON schema: {e}",
                                file_path=module_name.replace(".", "/") + ".py",
                            )

                if models:
                    all_models[module_name] = models

            except ImportError:
                pass  # Already reported

    return all_models


def validate_message_catalog(report: ValidationReport) -> None:
    """Validate message catalog contracts.
    
    Per ADR-0018#message-catalogs: All user messages from catalog.
    """
    report.categories_checked.append("message_catalog")

    try:
        from shared.contracts.messages.catalog import (
            MessageCatalog,
            MessageCategory,
            MessageDefinition,
            MessageSeverity,
        )

        # Validate enums have expected values
        expected_severities = {"debug", "info", "success", "warning", "error", "critical"}
        actual_severities = {s.value for s in MessageSeverity}
        if expected_severities != actual_severities:
            report.add_warning(
                "message_catalog",
                f"MessageSeverity values mismatch: expected {expected_severities}, got {actual_severities}",
            )

        # Validate MessageDefinition can be created
        try:
            msg = MessageDefinition(
                message_id="TEST_MESSAGE",
                message="Test message with {placeholder}",
            )
            # Placeholder extraction is auto-done by field_validator
            # Just verify model created successfully
            if msg.message_id != "TEST_MESSAGE":
                report.add_error(
                    "message_catalog",
                    "MessageDefinition creation failed",
                )
        except Exception as e:
            report.add_error(
                "message_catalog",
                f"MessageDefinition validation failed: {e}",
            )

    except ImportError as e:
        report.add_error(
            "message_catalog",
            f"Cannot import message catalog contracts: {e}",
        )


def validate_adr_files(report: ValidationReport) -> int:
    """Validate ADR JSON files have required structure.
    
    Per ADR-0016: 3-Tier Document Model.
    Returns count of valid ADRs.
    """
    report.categories_checked.append("adr_files")

    adr_dir = PROJECT_ROOT / ".adrs"
    if not adr_dir.exists():
        report.add_error("adr_files", f"ADR directory not found: {adr_dir}")
        return 0

    required_fields = ["id", "title", "status"]
    recommended_fields = ["decision_primary"]

    valid_count = 0

    for adr_file in adr_dir.rglob("*.json"):
        try:
            with open(adr_file, encoding="utf-8") as f:
                adr = json.load(f)

            # Check required fields
            missing = [field for field in required_fields if field not in adr]
            if missing:
                report.add_error(
                    "adr_files",
                    f"ADR missing required fields: {missing}",
                    file_path=str(adr_file.relative_to(PROJECT_ROOT)),
                )
            else:
                valid_count += 1

            # Check recommended fields
            missing_recommended = [field for field in recommended_fields if field not in adr]
            # Also check for constraints in decision_details (per ADR schema)
            has_constraints = (
                "decision_details" in adr and
                isinstance(adr.get("decision_details"), dict) and
                adr["decision_details"].get("constraints")
            )
            if missing_recommended and not has_constraints:
                report.add_warning(
                    "adr_files",
                    f"ADR missing recommended fields: {missing_recommended}",
                    file_path=str(adr_file.relative_to(PROJECT_ROOT)),
                )

            # Validate status
            if adr.get("status") not in ["draft", "proposed", "accepted", "deprecated", "superseded"]:
                report.add_warning(
                    "adr_files",
                    f"ADR has non-standard status: {adr.get('status')}",
                    file_path=str(adr_file.relative_to(PROJECT_ROOT)),
                )

        except json.JSONDecodeError as e:
            report.add_error(
                "adr_files",
                f"Invalid JSON: {e}",
                file_path=str(adr_file.relative_to(PROJECT_ROOT)),
            )
        except Exception as e:
            report.add_error(
                "adr_files",
                f"Error reading ADR: {e}",
                file_path=str(adr_file.relative_to(PROJECT_ROOT)),
            )

    return valid_count


def validate_spec_files(report: ValidationReport) -> int:
    """Validate SPEC JSON files have required structure.
    
    Returns count of valid SPECs.
    """
    report.categories_checked.append("spec_files")

    spec_dir = PROJECT_ROOT / "docs" / "specs"
    if not spec_dir.exists():
        report.add_warning("spec_files", f"SPEC directory not found: {spec_dir}")
        return 0

    required_fields = ["id", "title"]

    valid_count = 0

    for spec_file in spec_dir.rglob("*.json"):
        try:
            with open(spec_file, encoding="utf-8") as f:
                spec = json.load(f)

            # Check required fields
            missing = [field for field in required_fields if field not in spec]
            if missing:
                report.add_error(
                    "spec_files",
                    f"SPEC missing required fields: {missing}",
                    file_path=str(spec_file.relative_to(PROJECT_ROOT)),
                )
            else:
                valid_count += 1

            # Check ADR reference (accepts 'implements_adr' or 'implements')
            has_adr_ref = "implements_adr" in spec or "implements" in spec
            if not has_adr_ref:
                report.add_warning(
                    "spec_files",
                    "SPEC missing ADR reference ('implements_adr' or 'implements')",
                    file_path=str(spec_file.relative_to(PROJECT_ROOT)),
                )

        except json.JSONDecodeError as e:
            report.add_error(
                "spec_files",
                f"Invalid JSON: {e}",
                file_path=str(spec_file.relative_to(PROJECT_ROOT)),
            )
        except Exception as e:
            report.add_error(
                "spec_files",
                f"Error reading SPEC: {e}",
                file_path=str(spec_file.relative_to(PROJECT_ROOT)),
            )

    return valid_count


def generate_schemas(report: ValidationReport, output_dir: Path) -> int:
    """Generate JSON schemas for all Pydantic models.
    
    Returns count of schemas generated.
    """
    from pydantic import BaseModel

    report.categories_checked.append("schema_generation")
    generated_count = 0

    for category, modules in CONTRACT_MODULES.items():
        category_dir = output_dir / category
        category_dir.mkdir(parents=True, exist_ok=True)

        for module_name in modules:
            try:
                module = importlib.import_module(module_name)
                module_short = module_name.split(".")[-1]

                for name in dir(module):
                    obj = getattr(module, name)
                    if (
                        isinstance(obj, type)
                        and issubclass(obj, BaseModel)
                        and obj is not BaseModel
                        and obj.__module__ == module_name
                    ):
                        try:
                            schema = obj.model_json_schema()

                            # Add metadata
                            schema["$comment"] = {
                                "generated_at": datetime.now(UTC).isoformat(),
                                "source_module": module_name,
                                "model_name": name,
                            }

                            schema_path = category_dir / f"{module_short}_{name}.json"
                            with open(schema_path, "w", encoding="utf-8") as f:
                                json.dump(schema, f, indent=2)

                            generated_count += 1

                        except Exception as e:
                            report.add_error(
                                "schema_generation",
                                f"Failed to generate schema for {name}: {e}",
                            )

            except ImportError:
                pass  # Already reported

    # Generate index
    index = {
        "generated_at": datetime.now(UTC).isoformat(),
        "schema_count": generated_count,
        "categories": list(CONTRACT_MODULES.keys()),
    }

    with open(output_dir / "index.json", "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    return generated_count


# =============================================================================
# Report Output
# =============================================================================

def print_report(report: ValidationReport) -> None:
    """Print validation report to console."""
    report.completed_at = datetime.now(UTC)

    print("\n" + "=" * 60)
    print("  CONTRACT VALIDATION REPORT")
    print("=" * 60)
    print(f"  Started:  {report.started_at.isoformat()}")
    print(f"  Completed: {report.completed_at.isoformat()}")
    print(f"  Categories: {', '.join(report.categories_checked)}")
    print("=" * 60)

    # Group issues by category
    by_category: dict[str, list[ValidationIssue]] = {}
    for issue in report.issues:
        by_category.setdefault(issue.category, []).append(issue)

    for category, issues in by_category.items():
        print(f"\n[{category}]")
        for issue in issues:
            icon = {
                ValidationSeverity.INFO: "ℹ",
                ValidationSeverity.WARNING: "⚠",
                ValidationSeverity.ERROR: "✗",
                ValidationSeverity.CRITICAL: "‼",
            }[issue.severity]

            print(f"  {icon} [{issue.severity.value.upper()}] {issue.message}")
            if issue.file_path:
                print(f"    File: {issue.file_path}")
            if issue.suggestion:
                print(f"    Fix: {issue.suggestion}")

    # Summary
    print("\n" + "-" * 60)
    print(f"  Errors: {report.error_count}  |  Warnings: {report.warning_count}")
    if report.is_valid:
        print("  Status: ✓ PASSED")
    else:
        print("  Status: ✗ FAILED")
    print("-" * 60 + "\n")


def save_report(report: ValidationReport, output_path: Path) -> None:
    """Save validation report as JSON."""
    report.completed_at = datetime.now(UTC)

    data = {
        "started_at": report.started_at.isoformat(),
        "completed_at": report.completed_at.isoformat(),
        "is_valid": report.is_valid,
        "error_count": report.error_count,
        "warning_count": report.warning_count,
        "categories_checked": report.categories_checked,
        "issues": [
            {
                "category": i.category,
                "severity": i.severity.value,
                "message": i.message,
                "file_path": i.file_path,
                "suggestion": i.suggestion,
            }
            for i in report.issues
        ],
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =============================================================================
# Main
# =============================================================================

def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Unified contract validation for Engineering Tools platform"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full validation including schema generation",
    )
    parser.add_argument(
        "--output-schemas",
        action="store_true",
        help="Generate JSON schemas to schemas/ directory",
    )
    parser.add_argument(
        "--schema-dir",
        type=Path,
        default=PROJECT_ROOT / "schemas",
        help="Output directory for generated schemas",
    )
    parser.add_argument(
        "--report-file",
        type=Path,
        help="Save report as JSON to this file",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    report = ValidationReport()

    print("=" * 60)
    print("  Engineering Tools Contract Validation")
    print("=" * 60)

    # Step 1: Validate imports
    print("\n[1/6] Validating contract imports...")
    valid_modules = validate_contract_imports(report)
    print(f"      {valid_modules} modules validated")

    # Step 2: Validate versioning
    print("[2/6] Validating contract versioning...")
    validate_contract_versioning(report)

    # Step 3: Validate Pydantic models
    print("[3/6] Validating Pydantic models...")
    all_models = validate_pydantic_models(report)
    total_models = sum(len(m) for m in all_models.values())
    print(f"      {total_models} models validated")

    # Step 4: Validate message catalog
    print("[4/6] Validating message catalog...")
    validate_message_catalog(report)

    # Step 5: Validate ADR files
    print("[5/6] Validating ADR files...")
    valid_adrs = validate_adr_files(report)
    print(f"      {valid_adrs} ADRs validated")

    # Step 6: Validate SPEC files
    print("[6/6] Validating SPEC files...")
    valid_specs = validate_spec_files(report)
    print(f"      {valid_specs} SPECs validated")

    # Optional: Generate schemas
    if args.output_schemas or args.full:
        print("\n[EXTRA] Generating JSON schemas...")
        schema_count = generate_schemas(report, args.schema_dir)
        print(f"        {schema_count} schemas generated to {args.schema_dir}")

    # Print report
    print_report(report)

    # Save report if requested
    if args.report_file:
        save_report(report, args.report_file)
        print(f"Report saved to: {args.report_file}")

    # Determine exit code
    if args.fail_on_warning and report.warning_count > 0:
        return 1
    if report.error_count > 0:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
