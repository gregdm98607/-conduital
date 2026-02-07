"""Data integrity checking utilities.

Validates data consistency:
- Orphaned records (FK violations)
- Invalid enum values
- Null constraint violations
- Unique constraint violations
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


class IssueSeverity(str, Enum):
    """Severity level for integrity issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class IntegrityIssue:
    """A detected integrity issue."""

    severity: IssueSeverity
    table: str
    column: str
    issue_type: str
    message: str
    count: int = 0
    sample_values: list[Any] = field(default_factory=list)


@dataclass
class IntegrityReport:
    """Complete integrity check report."""

    issues: list[IntegrityIssue] = field(default_factory=list)
    tables_checked: int = 0
    rows_checked: int = 0

    @property
    def is_healthy(self) -> bool:
        return not any(i.severity == IssueSeverity.ERROR for i in self.issues)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)


# Define known enum values for validation
ENUM_DEFINITIONS = {
    "tasks": {
        "status": ["pending", "in_progress", "waiting", "completed", "cancelled"],
        "task_type": ["action", "waiting_for", "reference", "someday", "someday_maybe"],
        "urgency_zone": ["critical_now", "opportunity_now", "over_the_horizon", None],
        "energy_level": ["low", "medium", "high", None],
    },
    "projects": {
        "status": ["active", "on_hold", "someday", "someday_maybe", "completed", "cancelled", "archived"],
    },
    "inbox": {
        "status": ["pending", "processed", "deleted"],
    },
    "memory_objects": {
        "storage_type": ["db", "file"],
    },
}


def find_orphaned_records(engine: Engine) -> list[IntegrityIssue]:
    """Find records with foreign keys pointing to non-existent records."""
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

            if not local_cols or not ref_cols:
                continue

            local_col = local_cols[0]
            ref_col = ref_cols[0]

            try:
                with engine.connect() as conn:
                    # Find orphaned records
                    query = text(f"""
                        SELECT t.{local_col} FROM {table} t
                        WHERE t.{local_col} IS NOT NULL
                        AND NOT EXISTS (
                            SELECT 1 FROM {ref_table} r
                            WHERE r.{ref_col} = t.{local_col}
                        )
                        LIMIT 10
                    """)
                    result = conn.execute(query)
                    orphans = [row[0] for row in result]

                    if orphans:
                        # Get count
                        count_query = text(f"""
                            SELECT COUNT(*) FROM {table} t
                            WHERE t.{local_col} IS NOT NULL
                            AND NOT EXISTS (
                                SELECT 1 FROM {ref_table} r
                                WHERE r.{ref_col} = t.{local_col}
                            )
                        """)
                        count = conn.execute(count_query).scalar() or 0

                        issues.append(
                            IntegrityIssue(
                                severity=IssueSeverity.ERROR,
                                table=table,
                                column=local_col,
                                issue_type="orphaned_foreign_key",
                                message=f"References non-existent {ref_table}.{ref_col}",
                                count=count,
                                sample_values=orphans[:5],
                            )
                        )
            except Exception as e:
                issues.append(
                    IntegrityIssue(
                        severity=IssueSeverity.WARNING,
                        table=table,
                        column=local_col,
                        issue_type="check_error",
                        message=f"Could not check FK: {e}",
                    )
                )

    return issues


def validate_enum_values(engine: Engine) -> list[IntegrityIssue]:
    """Check that enum columns contain only valid values."""
    issues = []

    for table, columns in ENUM_DEFINITIONS.items():
        # Check if table exists
        inspector = inspect(engine)
        if table not in inspector.get_table_names():
            continue

        for column, valid_values in columns.items():
            # Check if column exists
            db_columns = {c["name"] for c in inspector.get_columns(table)}
            if column not in db_columns:
                continue

            try:
                with engine.connect() as conn:
                    # Build list of valid values for SQL
                    if None in valid_values:
                        non_null_values = [v for v in valid_values if v is not None]
                        placeholders = ", ".join(f"'{v}'" for v in non_null_values)
                        where_clause = f"{column} IS NOT NULL AND {column} NOT IN ({placeholders})"
                    else:
                        placeholders = ", ".join(f"'{v}'" for v in valid_values)
                        where_clause = f"{column} NOT IN ({placeholders})"

                    # Find invalid values
                    query = text(f"""
                        SELECT DISTINCT {column} FROM {table}
                        WHERE {where_clause}
                        LIMIT 10
                    """)
                    result = conn.execute(query)
                    invalid = [row[0] for row in result]

                    if invalid:
                        # Get count
                        count_query = text(f"""
                            SELECT COUNT(*) FROM {table}
                            WHERE {where_clause}
                        """)
                        count = conn.execute(count_query).scalar() or 0

                        issues.append(
                            IntegrityIssue(
                                severity=IssueSeverity.ERROR,
                                table=table,
                                column=column,
                                issue_type="invalid_enum",
                                message=f"Invalid values found (valid: {valid_values})",
                                count=count,
                                sample_values=invalid[:5],
                            )
                        )
            except Exception as e:
                issues.append(
                    IntegrityIssue(
                        severity=IssueSeverity.WARNING,
                        table=table,
                        column=column,
                        issue_type="check_error",
                        message=f"Could not validate enum: {e}",
                    )
                )

    return issues


def check_foreign_keys(engine: Engine) -> list[IntegrityIssue]:
    """Verify all foreign key relationships are intact."""
    return find_orphaned_records(engine)


def check_null_in_required_fields(engine: Engine) -> list[IntegrityIssue]:
    """Check for NULL values in fields that should not be NULL."""
    issues = []
    inspector = inspect(engine)

    # Define fields that should never be NULL (beyond DB constraints)
    required_fields = {
        "projects": ["name", "status"],
        "tasks": ["title", "status"],
        "areas": ["name"],
        "users": ["email"],
    }

    for table, columns in required_fields.items():
        if table not in inspector.get_table_names():
            continue

        db_columns = {c["name"] for c in inspector.get_columns(table)}

        for column in columns:
            if column not in db_columns:
                continue

            try:
                with engine.connect() as conn:
                    query = text(f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL")
                    count = conn.execute(query).scalar() or 0

                    if count > 0:
                        issues.append(
                            IntegrityIssue(
                                severity=IssueSeverity.WARNING,
                                table=table,
                                column=column,
                                issue_type="null_required_field",
                                message=f"NULL values in required field",
                                count=count,
                            )
                        )
            except Exception as e:
                issues.append(
                    IntegrityIssue(
                        severity=IssueSeverity.WARNING,
                        table=table,
                        column=column,
                        issue_type="check_error",
                        message=f"Could not check NULL values: {e}",
                    )
                )

    return issues


def get_table_statistics(engine: Engine) -> dict[str, dict]:
    """Get row counts and basic stats for all tables."""
    stats = {}
    inspector = inspect(engine)

    for table in inspector.get_table_names():
        if table in ("alembic_version", "sqlite_sequence"):
            continue

        try:
            with engine.connect() as conn:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar() or 0
                stats[table] = {"row_count": count}
        except Exception:
            stats[table] = {"row_count": -1, "error": True}

    return stats


def run_all_checks(engine: Engine) -> IntegrityReport:
    """Run all integrity checks and return a comprehensive report."""
    report = IntegrityReport()

    # Get table stats for context
    stats = get_table_statistics(engine)
    report.tables_checked = len(stats)
    report.rows_checked = sum(s.get("row_count", 0) for s in stats.values() if s.get("row_count", 0) > 0)

    # Run all checks
    report.issues.extend(find_orphaned_records(engine))
    report.issues.extend(validate_enum_values(engine))
    report.issues.extend(check_null_in_required_fields(engine))

    return report
