#!/usr/bin/env python3
"""
Project Discovery Script

Run this script to scan your Second Brain and discover all projects.

Usage:
    python scripts/discover_projects.py

    or with Poetry:
    poetry run python scripts/discover_projects.py
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.discovery_service import ProjectDiscoveryService
from app.core.config import settings


def main():
    """Main discovery script"""
    print("=" * 60)
    print("🔍 Project Discovery Tool")
    print("=" * 60)
    print()
    print(f"📁 Second Brain Root: {settings.SECOND_BRAIN_ROOT}")
    print(f"🗂️  Scanning directory: 10_Projects")
    print()

    # Check if directory exists
    projects_dir = settings.SECOND_BRAIN_PATH / "10_Projects"
    if not projects_dir.exists():
        print(f"❌ Error: Directory not found: {projects_dir}")
        print()
        print("Please check your SECOND_BRAIN_ROOT setting in .env file")
        sys.exit(1)

    print("📊 Current Area Mappings:")
    for prefix, area in settings.AREA_PREFIX_MAP.items():
        print(f"   {prefix} → {area}")
    print()

    # Check for unmapped prefixes
    db = SessionLocal()
    service = ProjectDiscoveryService(db)

    print("🔎 Checking for unmapped prefixes...")
    suggestions = service.suggest_area_mappings()

    if suggestions:
        print()
        print("⚠️  Found unmapped prefixes:")
        for prefix, info in suggestions.items():
            print(f"\n   Prefix: {prefix}")
            print(f"   Projects: {info['project_count']}")
            print(f"   Examples: {', '.join(info['sample_projects'][:2])}")

        print()
        print("💡 To add mappings, update AREA_PREFIX_MAP in your .env file or")
        print("   use the API: POST /api/v1/discovery/mappings")
        print()

        response = input("Continue with discovery anyway? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    else:
        print("✅ All prefixes are mapped")

    print()
    print("🚀 Starting discovery...")
    print()

    # Run discovery
    stats = service.discover_all_projects()

    # Print results
    print()
    print("=" * 60)
    print("📈 Discovery Results")
    print("=" * 60)
    print()
    print(f"✅ Success: {stats['success']}")
    print(f"📊 Folders discovered: {stats['discovered']}")
    print(f"✨ Projects imported: {stats['imported']}")
    print(f"⏭️  Projects skipped: {stats['skipped']}")
    print(f"❌ Errors: {len(stats['errors'])}")

    if stats['errors']:
        print()
        print("Error details:")
        for error in stats['errors']:
            print(f"   • {error['folder']}: {error['error']}")

    print()
    print("=" * 60)
    print("✅ Discovery complete!")
    print()
    print("Next steps:")
    print("   1. Review imported projects in the database")
    print("   2. Run momentum calculation: POST /api/v1/intelligence/momentum/update")
    print("   3. Check for stalled projects: GET /api/v1/intelligence/stalled")
    print()

    db.close()


if __name__ == "__main__":
    main()
