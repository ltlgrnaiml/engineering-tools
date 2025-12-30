#!/usr/bin/env python3
"""Create a new Plan artifact.

Usage:
    python scripts/workflow/new_plan.py "Title of Plan"

This script:
1. Finds the next available PLAN-XXX number
2. Creates a new plan file from template
3. Updates INDEX.md with the new plan

Per ADR-0043: AI Development Workflow Orchestration.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
PLANS_DIR = PROJECT_ROOT / ".plans"
TEMPLATE_PATH = PLANS_DIR / ".templates" / "PLAN_TEMPLATE.md"
INDEX_PATH = PLANS_DIR / "INDEX.md"


def get_next_plan_number() -> int:
    """Find the next available PLAN number.

    Returns:
        Next available PLAN number (1 if none exist).
    """
    pattern = re.compile(r"PLAN-(\d{3})")
    max_num = 0

    for file in PLANS_DIR.glob("PLAN-*.md"):
        match = pattern.search(file.name)
        if match:
            num = int(match.group(1))
            max_num = max(max_num, num)

    return max_num + 1


def slugify(title: str) -> str:
    """Convert title to URL-safe slug.

    Args:
        title: Human-readable title.

    Returns:
        Slugified version suitable for filename.
    """
    slug = re.sub(r"[^\w\s-]", "", title)
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")[:50]


def create_plan(title: str) -> Path:
    """Create a new plan file.

    Args:
        title: Title for the plan.

    Returns:
        Path to the created plan file.
    """
    plan_num = get_next_plan_number()
    plan_id = f"PLAN-{plan_num:03d}"
    slug = slugify(title)
    filename = f"{plan_id}_{slug}.md"
    filepath = PLANS_DIR / filename

    # Read template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Replace placeholders
    today = datetime.now().strftime("%Y-%m-%d")
    content = template.replace("{NNN}", f"{plan_num:03d}")
    content = content.replace("{Title}", title)
    content = content.replace("{YYYY-MM-DD}", today)
    content = content.replace("{Name}", "USER")
    content = content.replace("{XXX}", "XXX")  # Session/refs to be filled
    content = content.replace("{XXXX}", "XXXX")  # ADR refs to be filled
    content = content.replace("{DATE}", today)
    content = content.replace("{HH:MM}", "00:00")

    # Write file
    filepath.write_text(content, encoding="utf-8")

    return filepath


def update_index(plan_id: str, title: str, filepath: Path) -> None:
    """Update INDEX.md with new plan.

    Args:
        plan_id: Plan ID (e.g., PLAN-001).
        title: Plan title.
        filepath: Path to the plan file.
    """
    index_content = INDEX_PATH.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Find the "Active Plans" table and add entry
    new_row = f"| {plan_id} | {title} | `draft` | 0% | - | {today} |"

    # Replace the "No active plans" placeholder or add to table
    if "*No active plans*" in index_content:
        index_content = index_content.replace(
            "| *No active plans* | | | | | |",
            new_row,
        )
    else:
        # Find end of Active Plans header row and insert
        lines = index_content.split("\n")
        for i, line in enumerate(lines):
            if "| ID | Title | Status |" in line:
                # Skip header and separator, insert after
                insert_idx = i + 2
                lines.insert(insert_idx, new_row)
                break
        index_content = "\n".join(lines)

    # Update statistics
    index_content = re.sub(
        r"\*\*Total Plans\*\*: (\d+)",
        lambda m: f"**Total Plans**: {int(m.group(1)) + 1}",
        index_content,
    )
    index_content = re.sub(
        r"\*\*Active\*\*: (\d+)",
        lambda m: f"**Active**: {int(m.group(1)) + 1}",
        index_content,
    )

    # Update last updated date
    index_content = re.sub(
        r"\*Last updated: .*\*",
        f"*Last updated: {today}*",
        index_content,
    )

    INDEX_PATH.write_text(index_content, encoding="utf-8")


def main() -> None:
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python new_plan.py \"Title of Plan\"")
        print("\nExample:")
        print("  python scripts/workflow/new_plan.py \"DAT Streaming Implementation\"")
        sys.exit(1)

    title = sys.argv[1]

    # Validate directories exist
    if not PLANS_DIR.exists():
        print(f"Error: Plans directory not found: {PLANS_DIR}")
        sys.exit(1)

    if not TEMPLATE_PATH.exists():
        print(f"Error: Template not found: {TEMPLATE_PATH}")
        sys.exit(1)

    # Create plan
    filepath = create_plan(title)
    plan_id = filepath.stem.split("_")[0]

    # Update index
    update_index(plan_id, title, filepath)

    print(f"✓ Created: {filepath.relative_to(PROJECT_ROOT)}")
    print(f"✓ Updated: {INDEX_PATH.relative_to(PROJECT_ROOT)}")
    print(f"\nNext steps:")
    print(f"  1. Open {filepath.name}")
    print(f"  2. Define milestones with acceptance criteria")
    print(f"  3. Break milestones into tasks with verification commands")
    print(f"  4. Link source references (DISC, ADR, SPEC)")


if __name__ == "__main__":
    main()
