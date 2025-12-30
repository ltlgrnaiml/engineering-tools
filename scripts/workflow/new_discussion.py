#!/usr/bin/env python3
"""Create a new Discussion artifact.

Usage:
    python scripts/workflow/new_discussion.py "Title of Discussion"

This script:
1. Finds the next available DISC-XXX number
2. Creates a new discussion file from template
3. Updates INDEX.md with the new discussion

Per ADR-0041: AI Development Workflow Orchestration.
"""

import re
import sys
from datetime import datetime
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
DISCUSSIONS_DIR = PROJECT_ROOT / ".discussions"
TEMPLATE_PATH = DISCUSSIONS_DIR / ".templates" / "DISC_TEMPLATE.md"
INDEX_PATH = DISCUSSIONS_DIR / "INDEX.md"


def get_next_disc_number() -> int:
    """Find the next available DISC number.

    Returns:
        Next available DISC number (1 if none exist).
    """
    pattern = re.compile(r"DISC-(\d{3})")
    max_num = 0

    for file in DISCUSSIONS_DIR.glob("DISC-*.md"):
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


def create_discussion(title: str) -> Path:
    """Create a new discussion file.

    Args:
        title: Title for the discussion.

    Returns:
        Path to the created discussion file.
    """
    disc_num = get_next_disc_number()
    disc_id = f"DISC-{disc_num:03d}"
    slug = slugify(title)
    filename = f"{disc_id}_{slug}.md"
    filepath = DISCUSSIONS_DIR / filename

    # Read template
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    # Replace placeholders
    today = datetime.now().strftime("%Y-%m-%d")
    content = template.replace("{NNN}", f"{disc_num:03d}")
    content = content.replace("{Title}", title)
    content = content.replace("{YYYY-MM-DD}", today)
    content = content.replace("{Name}", "USER")
    content = content.replace("{XXX}", "XXX")  # Session to be filled

    # Write file
    filepath.write_text(content, encoding="utf-8")

    return filepath


def update_index(disc_id: str, title: str, filepath: Path) -> None:
    """Update INDEX.md with new discussion.

    Args:
        disc_id: Discussion ID (e.g., DISC-001).
        title: Discussion title.
        filepath: Path to the discussion file.
    """
    index_content = INDEX_PATH.read_text(encoding="utf-8")
    today = datetime.now().strftime("%Y-%m-%d")

    # Find the "Active Discussions" table and add entry
    new_row = f"| {disc_id} | {title} | `draft` | {today} | - | - |"

    # Replace the "No active discussions" placeholder or add to table
    if "*No active discussions*" in index_content:
        index_content = index_content.replace(
            "| *No active discussions* | | | | | |",
            new_row,
        )
    else:
        # Find end of Active Discussions header row and insert
        lines = index_content.split("\n")
        for i, line in enumerate(lines):
            if "| ID | Title | Status |" in line:
                # Skip header and separator, insert after
                insert_idx = i + 2
                lines.insert(insert_idx, new_row)
                break
        index_content = "\n".join(lines)

    # Update statistics
    # Simple increment of Total and Active counts
    index_content = re.sub(
        r"\*\*Total Discussions\*\*: (\d+)",
        lambda m: f"**Total Discussions**: {int(m.group(1)) + 1}",
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
        print("Usage: python new_discussion.py \"Title of Discussion\"")
        print("\nExample:")
        print("  python scripts/workflow/new_discussion.py \"WebSocket Real-Time Updates\"")
        sys.exit(1)

    title = sys.argv[1]

    # Validate directories exist
    if not DISCUSSIONS_DIR.exists():
        print(f"Error: Discussions directory not found: {DISCUSSIONS_DIR}")
        sys.exit(1)

    if not TEMPLATE_PATH.exists():
        print(f"Error: Template not found: {TEMPLATE_PATH}")
        sys.exit(1)

    # Create discussion
    filepath = create_discussion(title)
    disc_id = filepath.stem.split("_")[0]

    # Update index
    update_index(disc_id, title, filepath)

    print(f"✓ Created: {filepath.relative_to(PROJECT_ROOT)}")
    print(f"✓ Updated: {INDEX_PATH.relative_to(PROJECT_ROOT)}")
    print(f"\nNext steps:")
    print(f"  1. Open {filepath.name}")
    print(f"  2. Fill in Context and Requirements sections")
    print(f"  3. Update session ID in metadata")


if __name__ == "__main__":
    main()
