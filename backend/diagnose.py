"""
Diagnostic script to check backend setup
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_database():
    """Check if database exists and has tables"""
    from app.core.config import settings
    from sqlalchemy import create_engine, inspect

    print("=" * 50)
    print("DATABASE CHECK")
    print("=" * 50)

    db_path = settings.DATABASE_URL.replace("sqlite:///", "")
    print(f"Database path: {db_path}")

    if not Path(db_path).exists():
        print("❌ Database file does not exist!")
        print(f"   Expected at: {db_path}")
        print("\nRun: poetry run alembic upgrade head")
        return False

    print("✅ Database file exists")

    # Check tables
    engine = create_engine(settings.DATABASE_URL)
    inspector = inspect(engine)
    tables = inspector.get_table_names()

    print(f"\nTables found: {len(tables)}")
    for table in tables:
        print(f"  - {table}")

    expected_tables = [
        'projects', 'tasks', 'areas', 'goals', 'visions',
        'project_phases', 'phase_templates', 'contexts',
        'activity_logs', 'sync_state', 'inbox_items'
    ]

    missing = [t for t in expected_tables if t not in tables]
    if missing:
        print(f"\n❌ Missing tables: {missing}")
        print("\nRun: poetry run alembic upgrade head")
        return False

    print("\n✅ All expected tables exist")
    return True

def test_project_creation():
    """Test creating a project"""
    from app.core.database import SessionLocal
    from app.models.project import Project

    print("\n" + "=" * 50)
    print("PROJECT CREATION TEST")
    print("=" * 50)

    db = SessionLocal()
    try:
        # Try to create a simple project
        project = Project(
            title="Test Project",
            description="Diagnostic test",
            status="active",
            priority=2
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        print(f"✅ Successfully created project ID: {project.id}")
        print(f"   Title: {project.title}")
        print(f"   Status: {project.status}")

        # Clean up
        db.delete(project)
        db.commit()
        print("✅ Cleanup successful")

        return True

    except Exception as e:
        print(f"❌ Error creating project:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def test_api_schema():
    """Test API schema validation"""
    from app.schemas.project import ProjectCreate

    print("\n" + "=" * 50)
    print("API SCHEMA TEST")
    print("=" * 50)

    try:
        # Test valid data
        project_data = {
            "title": "Test Project",
            "description": "Test description",
            "status": "active",
            "priority": 2
        }

        project = ProjectCreate(**project_data)
        print("✅ Schema validation passed")
        print(f"   Title: {project.title}")
        print(f"   Status: {project.status}")
        print(f"   Priority: {project.priority}")

        return True

    except Exception as e:
        print(f"❌ Schema validation failed:")
        print(f"   {type(e).__name__}: {e}")
        return False

def main():
    print("\nRunning Conduital Diagnostics\n")

    results = []

    # Check database
    results.append(("Database", check_database()))

    # Test project creation
    results.append(("Project Creation", test_project_creation()))

    # Test API schema
    results.append(("API Schema", test_api_schema()))

    # Summary
    print("\n" + "=" * 50)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 50)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name:.<30} {status}")

    all_passed = all(r[1] for r in results)

    if all_passed:
        print("\n✅ All checks passed! Backend should work.")
    else:
        print("\n❌ Some checks failed. See errors above.")
        print("\nCommon fixes:")
        print("  1. Run migrations: poetry run alembic upgrade head")
        print("  2. Check .env file configuration")
        print("  3. Restart backend server")

    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
