#!/usr/bin/env python3
"""
Create Project Markdown Files

Creates minimal markdown files for project folders that don't have them.
This ensures all projects can be properly synced bidirectionally.

Usage:
    python scripts/create_project_files.py [--dry-run]

    or with Poetry:
    poetry run python scripts/create_project_files.py [--dry-run]

Options:
    --dry-run    Show what would be created without actually creating files
"""

import sys
import re
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


def create_markdown_template(project_title: str, folder_name: str) -> str:
    """
    Create a markdown template for a project.

    Args:
        project_title: Clean project title
        folder_name: Original folder name

    Returns:
        str: Markdown content with frontmatter
    """
    current_date = datetime.utcnow().isoformat() + "Z"

    template = f"""---
project_status: active
priority: 3
created_at: {current_date}
---

# {project_title}

Project folder: `{folder_name}`

## Overview

<!-- Add project description here -->

## Next Actions

- [ ] Define project goals and objectives
- [ ] Break down into concrete tasks
- [ ] Identify first next action

## Notes

<!-- Add project notes, context, and resources here -->

## Reference

- Project discovered and initialized: {current_date}
"""
    return template


def find_projects_without_markdown():
    """
    Scan 10_Projects directory and find folders without markdown files.

    Returns:
        list: Tuples of (folder_path, project_title, needs_file)
    """
    projects_dir = settings.SECOND_BRAIN_PATH / "10_Projects"

    if not projects_dir.exists():
        print(f"❌ Error: Projects directory not found: {projects_dir}")
        return []

    pattern = re.compile(settings.PROJECT_FOLDER_PATTERN)
    results = []

    for folder in sorted(projects_dir.iterdir()):
        if not folder.is_dir():
            continue

        # Check if folder matches pattern
        match = pattern.match(folder.name)
        if not match:
            continue

        # Extract project title
        project_title = match.group(3).replace("_", " ")

        # Check for existing markdown files
        markdown_files = list(folder.glob("*.md"))

        results.append({
            "folder": folder,
            "folder_name": folder.name,
            "title": project_title,
            "has_markdown": len(markdown_files) > 0,
            "markdown_count": len(markdown_files),
            "markdown_files": [f.name for f in markdown_files]
        })

    return results


def create_missing_files(dry_run=False):
    """
    Create markdown files for projects that don't have them.

    Args:
        dry_run: If True, only show what would be created
    """
    print("=" * 60)
    print("📝 Create Project Markdown Files")
    print("=" * 60)
    print()

    projects_dir = settings.SECOND_BRAIN_PATH / "10_Projects"
    print(f"📁 Scanning: {projects_dir}")
    print()

    if dry_run:
        print("🔍 DRY RUN MODE - No files will be created")
        print()

    # Find all projects
    projects = find_projects_without_markdown()

    if not projects:
        print("❌ No project folders found")
        return

    # Separate into categories
    with_markdown = [p for p in projects if p["has_markdown"]]
    without_markdown = [p for p in projects if not p["has_markdown"]]

    print(f"📊 Summary:")
    print(f"   Total project folders: {len(projects)}")
    print(f"   ✅ With markdown: {len(with_markdown)}")
    print(f"   ⚠️  Without markdown: {len(without_markdown)}")
    print()

    if with_markdown:
        print("✅ Projects with markdown files:")
        for project in with_markdown:
            files_str = ", ".join(project["markdown_files"])
            print(f"   • {project['folder_name']}")
            print(f"     Files: {files_str}")
        print()

    if not without_markdown:
        print("🎉 All projects already have markdown files!")
        return

    print("⚠️  Projects missing markdown files:")
    for project in without_markdown:
        print(f"   • {project['folder_name']}")
        print(f"     Title: {project['title']}")
    print()

    if dry_run:
        print("Would create files:")
        for project in without_markdown:
            filename = project["folder_name"] + ".md"
            file_path = project["folder"] / filename
            print(f"   📄 {file_path}")
        print()
        print("Run without --dry-run to create files")
        return

    # Confirm before creating
    print("=" * 60)
    response = input(f"Create {len(without_markdown)} markdown files? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled.")
        return

    print()
    print("📝 Creating files...")
    print()

    # Create files
    created = 0
    errors = []

    for project in without_markdown:
        try:
            # Generate filename: same as folder name
            filename = project["folder_name"] + ".md"
            file_path = project["folder"] / filename

            # Create content
            content = create_markdown_template(project["title"], project["folder_name"])

            # Write file
            file_path.write_text(content, encoding="utf-8")

            print(f"✅ Created: {filename}")
            print(f"   Path: {file_path}")
            created += 1

        except Exception as e:
            error_msg = f"Error creating {project['folder_name']}: {str(e)}"
            print(f"❌ {error_msg}")
            errors.append(error_msg)

    print()
    print("=" * 60)
    print("📈 Results")
    print("=" * 60)
    print()
    print(f"✅ Files created: {created}")
    print(f"❌ Errors: {len(errors)}")

    if errors:
        print()
        print("Error details:")
        for error in errors:
            print(f"   • {error}")

    print()
    print("✅ Done!")
    print()
    print("Next steps:")
    print("   1. Review created files in your synced notes folder")
    print("   2. Add project details, tasks, and notes")
    print("   3. Run discovery: poetry run python scripts/discover_projects.py")
    print()


def main():
    """Main script entry point"""
    parser = argparse.ArgumentParser(
        description="Create markdown files for projects without them"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be created without creating files"
    )
    args = parser.parse_args()

    create_missing_files(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
