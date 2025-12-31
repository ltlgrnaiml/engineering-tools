#!/usr/bin/env python
"""Generate JSON Schema from Pydantic contracts.

Per ADR-0010: Type Safety & Contract Discipline.
Per ADR-0016: 3-Tier Document Model (Contracts are Tier 0).

This script generates JSON Schema files from all Pydantic contracts
in shared/contracts/ for external validation and documentation.

Usage:
    python tools/gen_json_schema.py [--output-dir schemas/] [--validate]

Output:
    schemas/
    ├── core/
    │   ├── dataset.json
    │   ├── pipeline.json
    │   └── ...
    ├── dat/
    │   ├── stage.json
    │   └── ...
    └── index.json  (schema index with all refs)
"""

import argparse
import importlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Contract modules to process
CONTRACT_MODULES = {
    "core": [
        "shared.contracts.core.artifact_registry",
        "shared.contracts.core.audit",
        "shared.contracts.core.concurrency",
        "shared.contracts.core.dataset",
        "shared.contracts.core.error_response",
        "shared.contracts.core.id_generator",
        "shared.contracts.core.idempotency",
        "shared.contracts.core.logging",
        "shared.contracts.core.frontend_logging",
        "shared.contracts.core.path_safety",
        "shared.contracts.core.pipeline",
        "shared.contracts.core.rendering",
    ],
    "dat": [
        "shared.contracts.dat.adapter",
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
        "shared.contracts.devtools.workflow",
    ],
    "workflow": [
        "shared.contracts.adr_schema",
        "shared.contracts.spec_schema",
        "shared.contracts.plan_schema",
    ],
}


def get_pydantic_models(module_name: str) -> list[tuple[str, type]]:
    """Extract all Pydantic BaseModel classes from a module.

    Args:
        module_name: Full module path (e.g., 'shared.contracts.core.dataset')

    Returns:
        List of (class_name, class) tuples for Pydantic models.
    """
    from pydantic import BaseModel

    try:
        module = importlib.import_module(module_name)
    except ImportError as e:
        print(f"Warning: Could not import {module_name}: {e}")
        return []

    models = []
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj is not BaseModel
            and obj.__module__ == module_name  # Only models defined in this module
        ):
            models.append((name, obj))

    return models


def generate_schema(model_class: type) -> dict[str, Any]:
    """Generate JSON Schema from a Pydantic model.

    Args:
        model_class: Pydantic BaseModel class.

    Returns:
        JSON Schema dictionary.
    """
    return model_class.model_json_schema()


def write_schema_file(
    schema: dict[str, Any],
    output_path: Path,
    model_name: str,
    module_name: str,
) -> None:
    """Write schema to JSON file with metadata.

    Args:
        schema: JSON Schema dictionary.
        output_path: Path to write file.
        model_name: Name of the Pydantic model.
        module_name: Source module path.
    """
    # Add metadata
    schema["$comment"] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "source_module": module_name,
        "model_name": model_name,
        "generator": "tools/gen_json_schema.py",
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, sort_keys=False)

    print(f"  ✓ {model_name} → {output_path}")


def generate_index(
    schemas: dict[str, list[dict[str, str]]],
    output_dir: Path,
) -> None:
    """Generate index.json with all schema references.

    Args:
        schemas: Dict of {category: [{name, path, module}]}
        output_dir: Output directory for index file.
    """
    index = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "Engineering Tools Contract Schemas",
        "description": "Index of all Pydantic contract JSON Schemas",
        "generated_at": datetime.now(UTC).isoformat(),
        "categories": {},
    }

    for category, schema_list in schemas.items():
        index["categories"][category] = {
            "description": f"Schemas from shared.contracts.{category}",
            "schemas": schema_list,
        }

    index_path = output_dir / "index.json"
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

    print(f"\n✓ Generated index: {index_path}")


def validate_schemas(output_dir: Path) -> bool:
    """Validate all generated schemas are valid JSON Schema.

    Args:
        output_dir: Directory containing generated schemas.

    Returns:
        True if all schemas are valid.
    """
    try:
        import jsonschema
    except ImportError:
        print("Warning: jsonschema not installed, skipping validation")
        return True

    valid = True
    for schema_file in output_dir.rglob("*.json"):
        if schema_file.name == "index.json":
            continue

        try:
            with open(schema_file, encoding="utf-8") as f:
                schema = json.load(f)

            # Validate schema structure
            jsonschema.Draft7Validator.check_schema(schema)
            print(f"  ✓ {schema_file.name} valid")

        except json.JSONDecodeError as e:
            print(f"  ✗ {schema_file.name}: Invalid JSON - {e}")
            valid = False
        except jsonschema.SchemaError as e:
            print(f"  ✗ {schema_file.name}: Invalid schema - {e.message}")
            valid = False

    return valid


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate JSON Schema from Pydantic contracts"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "schemas",
        help="Output directory for schemas (default: schemas/)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate generated schemas",
    )
    parser.add_argument(
        "--category",
        type=str,
        choices=list(CONTRACT_MODULES.keys()),
        help="Generate only for specific category",
    )

    args = parser.parse_args()

    print("=" * 60)
    print("Generating JSON Schemas from Pydantic Contracts")
    print("=" * 60)

    output_dir = args.output_dir
    all_schemas: dict[str, list[dict[str, str]]] = {}

    # Process each category
    categories = [args.category] if args.category else CONTRACT_MODULES.keys()

    for category in categories:
        if category not in CONTRACT_MODULES:
            continue

        print(f"\n[{category}]")
        all_schemas[category] = []

        for module_name in CONTRACT_MODULES[category]:
            models = get_pydantic_models(module_name)

            for model_name, model_class in models:
                try:
                    schema = generate_schema(model_class)

                    # Determine output path
                    module_short = module_name.split(".")[-1]
                    schema_path = output_dir / category / f"{module_short}_{model_name}.json"

                    write_schema_file(schema, schema_path, model_name, module_name)

                    all_schemas[category].append({
                        "name": model_name,
                        "path": str(schema_path.relative_to(output_dir)),
                        "module": module_name,
                    })

                except Exception as e:
                    print(f"  ✗ {model_name}: {e}")

    # Generate index
    generate_index(all_schemas, output_dir)

    # Validate if requested
    if args.validate:
        print("\n" + "=" * 60)
        print("Validating Schemas")
        print("=" * 60)
        if not validate_schemas(output_dir):
            return 1

    print("\n" + "=" * 60)
    total = sum(len(s) for s in all_schemas.values())
    print(f"Generated {total} schemas in {output_dir}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
