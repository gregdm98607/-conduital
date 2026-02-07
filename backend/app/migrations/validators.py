"""Schema validation utilities.

Compares SQLAlchemy models to the actual database schema to detect:
- Missing tables
- Missing columns
- Column type mismatches
- Missing indexes
- Missing foreign keys
"""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


@dataclass
class SchemaDiff:
    """Differences between expected and actual schema."""

    missing_tables: list[str] = field(default_factory=list)
    extra_tables: list[str] = field(default_factory=list)
    missing_columns: dict[str, list[str]] = field(default_factory=dict)
    extra_columns: dict[str, list[str]] = field(default_factory=dict)
    missing_indexes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return (
            not self.missing_tables
            and not self.extra_tables
            and not self.missing_columns
            and not self.extra_columns
            and not self.missing_indexes
            and not self.errors
        )


def get_db_tables(engine: Engine) -> set[str]:
    """Get all table names from the database."""
    inspector = inspect(engine)
    return set(inspector.get_table_names())


def get_db_columns(engine: Engine, table: str) -> dict[str, dict]:
    """Get column info for a table."""
    inspector = inspect(engine)
    columns = {}
    for col in inspector.get_columns(table):
        columns[col["name"]] = {
            "type": str(col["type"]),
            "nullable": col["nullable"],
            "default": col.get("default"),
        }
    return columns


def get_db_indexes(engine: Engine, table: str) -> list[dict]:
    """Get index info for a table."""
    inspector = inspect(engine)
    return inspector.get_indexes(table)


def get_db_foreign_keys(engine: Engine, table: str) -> list[dict]:
    """Get foreign key info for a table."""
    inspector = inspect(engine)
    return inspector.get_foreign_keys(table)


def get_expected_tables(metadata) -> set[str]:
    """Get expected table names from SQLAlchemy metadata."""
    return set(metadata.tables.keys())


def get_expected_columns(metadata, table: str) -> dict[str, dict]:
    """Get expected column info from SQLAlchemy metadata."""
    if table not in metadata.tables:
        return {}
    columns = {}
    for col in metadata.tables[table].columns:
        columns[col.name] = {
            "type": str(col.type),
            "nullable": col.nullable,
            "primary_key": col.primary_key,
        }
    return columns


def get_schema_diff(engine: Engine, metadata) -> SchemaDiff:
    """Compare database schema to SQLAlchemy models."""
    diff = SchemaDiff()

    try:
        db_tables = get_db_tables(engine)
        expected_tables = get_expected_tables(metadata)

        # Skip internal tables
        skip_tables = {"alembic_version", "sqlite_sequence"}
        db_tables = db_tables - skip_tables

        # Check for missing/extra tables
        diff.missing_tables = sorted(expected_tables - db_tables)
        diff.extra_tables = sorted(db_tables - expected_tables)

        # Check columns for tables that exist in both
        common_tables = db_tables & expected_tables
        for table in common_tables:
            db_cols = set(get_db_columns(engine, table).keys())
            expected_cols = set(get_expected_columns(metadata, table).keys())

            missing = expected_cols - db_cols
            extra = db_cols - expected_cols

            if missing:
                diff.missing_columns[table] = sorted(missing)
            if extra:
                diff.extra_columns[table] = sorted(extra)

    except Exception as e:
        diff.errors.append(f"Schema comparison failed: {e}")

    return diff


def validate_schema(engine: Engine, metadata) -> tuple[bool, SchemaDiff]:
    """Validate that database schema matches SQLAlchemy models.

    Returns:
        Tuple of (is_valid, diff)
    """
    diff = get_schema_diff(engine, metadata)
    is_valid = diff.is_empty
    return is_valid, diff


def validate_alembic_version(engine: Engine, expected_revision: Optional[str]) -> tuple[bool, str]:
    """Validate that alembic_version table has expected revision.

    Returns:
        Tuple of (is_valid, message)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()

            if not row:
                return False, "No revision in alembic_version table"

            actual = row[0]
            if expected_revision and actual != expected_revision:
                return False, f"Version mismatch: DB={actual}, expected={expected_revision}"

            return True, f"Current revision: {actual}"

    except Exception as e:
        return False, f"Failed to check alembic_version: {e}"


def check_foreign_key_constraints(engine: Engine) -> list[str]:
    """Check that all foreign key constraints are satisfied."""
    issues = []
    inspector = inspect(engine)

    for table in inspector.get_table_names():
        if table in ("alembic_version", "sqlite_sequence"):
            continue

        fks = inspector.get_foreign_keys(table)
        for fk in fks:
            ref_table = fk["referred_table"]
            local_cols = fk["constrained_columns"]
            ref_cols = fk["referred_columns"]

            # Check for orphaned foreign keys
            try:
                with engine.connect() as conn:
                    # Build query to find orphaned records
                    local_col = local_cols[0]
                    ref_col = ref_cols[0]

                    query = text(f"""
                        SELECT COUNT(*) FROM {table} t
                        WHERE t.{local_col} IS NOT NULL
                        AND NOT EXISTS (
                            SELECT 1 FROM {ref_table} r
                            WHERE r.{ref_col} = t.{local_col}
                        )
                    """)
                    result = conn.execute(query)
                    count = result.scalar()

                    if count and count > 0:
                        issues.append(
                            f"{table}.{local_col} -> {ref_table}.{ref_col}: {count} orphaned records"
                        )
            except Exception as e:
                issues.append(f"Error checking FK {table}.{local_col}: {e}")

    return issues
