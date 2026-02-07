#!/usr/bin/env python3
"""
Initialize database and create initial migration

This script will:
1. Create the database directory if it doesn't exist
2. Generate the initial Alembic migration
3. Apply the migration
4. Enable WAL mode for better performance
"""

import subprocess
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.database import enable_wal_mode, engine


def main():
    print("🚀 Initializing Project Tracker Database...\n")

    # 1. Create database directory
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"✓ Database directory created: {db_path.parent}\n")

    # 2. Generate initial migration
    print("📝 Generating initial migration...")
    try:
        result = subprocess.run(
            [
                "alembic",
                "revision",
                "--autogenerate",
                "-m",
                "Initial database schema",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        print("✓ Migration generated successfully")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to generate migration: {e}")
        if e.stderr:
            print(e.stderr)
        sys.exit(1)

    print()

    # 3. Apply migration
    print("🔄 Applying migration...")
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
        )
        print("✓ Migration applied successfully")
        if result.stdout:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to apply migration: {e}")
        if e.stderr:
            print(e.stderr)
        sys.exit(1)

    print()

    # 4. Enable WAL mode
    print("⚡ Enabling WAL mode for better performance...")
    try:
        enable_wal_mode()
        print("✓ WAL mode enabled")
    except Exception as e:
        print(f"⚠️  Warning: Could not enable WAL mode: {e}")

    print()
    print("=" * 60)
    print("✅ Database initialization complete!")
    print(f"📍 Database location: {settings.DATABASE_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
