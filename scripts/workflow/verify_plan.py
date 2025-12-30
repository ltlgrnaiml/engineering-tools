"""Plan validation script for AI Development Workflow.

Per ADR-0043 and SPEC-0040: Validates Plan artifacts against Pydantic schemas
and checks granularity-level requirements (L1/L2/L3).

Usage:
    python scripts/workflow/verify_plan.py .plans/PLAN-001_example.json
    python scripts/workflow/verify_plan.py .plans/L3/PLAN-001/INDEX.json
    python scripts/workflow/verify_plan.py --all  # Validate all plans
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.contracts.plan_schema import (
    GranularityLevel,
    L3ChunkIndex,
    PlanSchema,
    Task,
)

__version__ = "2025.12.01"


class ValidationResult:
    """Result of plan validation."""

    def __init__(self, plan_path: Path) -> None:
        self.plan_path = plan_path
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.info: list[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def add_error(self, msg: str) -> None:
        self.errors.append(f"❌ ERROR: {msg}")

    def add_warning(self, msg: str) -> None:
        self.warnings.append(f"⚠️ WARNING: {msg}")

    def add_info(self, msg: str) -> None:
        self.info.append(f"ℹ️ INFO: {msg}")

    def print_report(self) -> None:
        """Print validation report."""
        print(f"\n{'='*60}")
        print(f"Plan: {self.plan_path}")
        print(f"{'='*60}")

        if self.info:
            for msg in self.info:
                print(msg)

        if self.warnings:
            print()
            for msg in self.warnings:
                print(msg)

        if self.errors:
            print()
            for msg in self.errors:
                print(msg)

        print()
        if self.is_valid:
            print("✅ VALID: Plan passes all checks")
        else:
            print(f"❌ INVALID: {len(self.errors)} error(s) found")


def validate_l1_task(task: Task, result: ValidationResult) -> None:
    """Validate L1 (Standard) task requirements."""
    # L1 requires: id, description, verification_command, status
    if not task.description or len(task.description) < 10:
        result.add_error(f"Task {task.id}: description too short (min 10 chars)")

    if not task.verification_command or len(task.verification_command) < 5:
        result.add_error(f"Task {task.id}: verification_command missing or too short")


def validate_l2_task(task: Task, result: ValidationResult) -> None:
    """Validate L2 (Enhanced) task requirements."""
    # L2 requires: L1 + context[] non-empty
    validate_l1_task(task, result)

    if not task.context or len(task.context) == 0:
        result.add_error(f"Task {task.id}: L2 requires non-empty context[]")

    # L2 should have at least one of: hints, constraints, references
    has_l2_content = (
        (task.hints and len(task.hints) > 0)
        or (task.constraints and len(task.constraints) > 0)
        or (task.references and len(task.references) > 0)
        or (task.existing_patterns and len(task.existing_patterns) > 0)
    )
    if not has_l2_content:
        result.add_warning(
            f"Task {task.id}: L2 should have hints[], constraints[], references[], "
            "or existing_patterns[] for mid-tier models"
        )


def validate_l3_task(task: Task, result: ValidationResult) -> None:
    """Validate L3 (Procedural) task requirements."""
    # L3 requires: L2 + steps[] non-empty
    validate_l2_task(task, result)

    if not task.steps or len(task.steps) == 0:
        result.add_error(f"Task {task.id}: L3 requires non-empty steps[]")
    else:
        # Validate each step
        for step in task.steps:
            if not step.instruction or len(step.instruction) < 10:
                result.add_error(
                    f"Task {task.id}, Step {step.step_number}: "
                    "instruction too short (min 10 chars)"
                )
            if not step.verification_hint:
                result.add_warning(
                    f"Task {task.id}, Step {step.step_number}: "
                    "missing verification_hint"
                )


def validate_plan_schema(plan_path: Path) -> ValidationResult:
    """Validate a plan file against the PlanSchema."""
    result = ValidationResult(plan_path)

    # Load JSON
    try:
        with open(plan_path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON: {e}")
        return result
    except FileNotFoundError:
        result.add_error(f"File not found: {plan_path}")
        return result

    # Detect schema type
    schema_type = data.get("schema_type", "plan")

    if schema_type == "l3_chunk_index":
        return validate_l3_index(plan_path, data, result)

    # Validate against PlanSchema
    try:
        plan = PlanSchema.model_validate(data)
    except ValidationError as e:
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            result.add_error(f"Schema error at {loc}: {error['msg']}")
        return result

    result.add_info(f"Granularity: {plan.granularity.value}")
    result.add_info(f"Status: {plan.status.value}")
    result.add_info(f"Milestones: {len(plan.milestones)}")

    total_tasks = sum(len(m.tasks) for m in plan.milestones)
    result.add_info(f"Total tasks: {total_tasks}")

    # Validate tasks based on granularity level
    for milestone in plan.milestones:
        for task in milestone.tasks:
            if plan.granularity == GranularityLevel.L1_STANDARD:
                validate_l1_task(task, result)
            elif plan.granularity == GranularityLevel.L2_ENHANCED:
                validate_l2_task(task, result)
            elif plan.granularity == GranularityLevel.L3_PROCEDURAL:
                validate_l3_task(task, result)

    # Check for missing verification evidence on "passed" tasks
    for milestone in plan.milestones:
        for task in milestone.tasks:
            if task.status.value == "passed" and not task.evidence:
                result.add_warning(
                    f"Task {task.id}: marked 'passed' but no evidence recorded"
                )

    return result


def validate_l3_index(
    plan_path: Path, data: dict[str, Any], result: ValidationResult
) -> ValidationResult:
    """Validate an L3 chunk index file."""
    try:
        index = L3ChunkIndex.model_validate(data)
    except ValidationError as e:
        for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            result.add_error(f"Schema error at {loc}: {error['msg']}")
        return result

    result.add_info(f"Plan ID: {index.plan_id}")
    result.add_info(f"Total chunks: {index.total_chunks}")
    result.add_info(f"Current chunk: {index.current_chunk or 'None'}")

    # Validate chunk count matches
    if len(index.chunks) != index.total_chunks:
        result.add_error(
            f"Chunk count mismatch: total_chunks={index.total_chunks}, "
            f"actual chunks={len(index.chunks)}"
        )

    # Validate each chunk metadata
    chunk_dir = plan_path.parent
    for chunk in index.chunks:
        chunk_file = chunk_dir / chunk.chunk_file
        if not chunk_file.exists():
            if chunk.line_count == 0:
                result.add_warning(f"Chunk {chunk.chunk_id}: file not yet authored")
            else:
                result.add_error(f"Chunk {chunk.chunk_id}: file not found: {chunk_file}")

        # Check line limits
        if chunk.line_count > chunk.soft_limit:
            if not chunk.warning_note:
                result.add_error(
                    f"Chunk {chunk.chunk_id}: exceeds soft limit "
                    f"({chunk.line_count} > {chunk.soft_limit}) without warning_note"
                )
            else:
                result.add_warning(
                    f"Chunk {chunk.chunk_id}: exceeds soft limit "
                    f"({chunk.line_count} > {chunk.soft_limit})"
                )

    # Validate continuation context
    ctx = index.continuation_context
    if index.current_chunk and index.current_chunk != index.chunks[0].chunk_id:
        # Not on first chunk - should have context
        if not ctx.previous_chunk:
            result.add_warning("Continuation context missing previous_chunk")

    return result


def find_all_plans(root: Path) -> list[Path]:
    """Find all plan files in the repository."""
    plans = []

    # Standard plans
    plans_dir = root / ".plans"
    if plans_dir.exists():
        for f in plans_dir.glob("PLAN-*.json"):
            plans.append(f)

    # L3 chunk indexes
    l3_dir = plans_dir / "L3"
    if l3_dir.exists():
        for f in l3_dir.glob("*/INDEX.json"):
            plans.append(f)

    return sorted(plans)


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate Plan artifacts against ADR-0043 schemas"
    )
    parser.add_argument(
        "plan_path",
        nargs="?",
        help="Path to plan JSON file to validate",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate all plans in .plans/ directory",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Only show errors, not info/warnings",
    )

    args = parser.parse_args()

    if not args.plan_path and not args.all:
        parser.print_help()
        return 1

    plans_to_validate: list[Path] = []

    if args.all:
        plans_to_validate = find_all_plans(PROJECT_ROOT)
        if not plans_to_validate:
            print("No plans found in .plans/ directory")
            return 0
        print(f"Found {len(plans_to_validate)} plan(s) to validate")
    else:
        plans_to_validate = [Path(args.plan_path)]

    all_valid = True
    for plan_path in plans_to_validate:
        result = validate_plan_schema(plan_path)

        if not args.quiet or not result.is_valid:
            result.print_report()

        if not result.is_valid:
            all_valid = False

    print()
    if all_valid:
        print(f"✅ All {len(plans_to_validate)} plan(s) valid")
        return 0
    else:
        print("❌ Validation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
