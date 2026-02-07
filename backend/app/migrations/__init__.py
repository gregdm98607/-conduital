"""Migration integrity checking utilities.

This package provides tools for validating database migrations:
- Chain analysis: Detect orphaned migrations, branches, gaps
- Schema validation: Compare SQLAlchemy models to actual database
- Data integrity: Check FK violations, enum values, orphaned records
- CLI commands: Typer-based interface for running checks
"""

from app.migrations.chain import (
    MigrationInfo,
    get_migration_chain,
    get_current_head,
    find_orphaned_migrations,
    validate_chain,
)
from app.migrations.validators import (
    validate_schema,
    validate_alembic_version,
    get_schema_diff,
)
from app.migrations.integrity import (
    IntegrityIssue,
    find_orphaned_records,
    validate_enum_values,
    check_foreign_keys,
    run_all_checks,
)

__all__ = [
    # Chain analysis
    "MigrationInfo",
    "get_migration_chain",
    "get_current_head",
    "find_orphaned_migrations",
    "validate_chain",
    # Schema validation
    "validate_schema",
    "validate_alembic_version",
    "get_schema_diff",
    # Integrity checks
    "IntegrityIssue",
    "find_orphaned_records",
    "validate_enum_values",
    "check_foreign_keys",
    "run_all_checks",
]
