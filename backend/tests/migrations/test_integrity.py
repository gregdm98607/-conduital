"""Tests for data integrity checking."""

import pytest
from sqlalchemy import text

from app.migrations.integrity import (
    IntegrityIssue,
    IssueSeverity,
    IntegrityReport,
    find_orphaned_records,
    validate_enum_values,
    check_null_in_required_fields,
    get_table_statistics,
    run_all_checks,
)


class TestIntegrityReport:
    """Tests for IntegrityReport dataclass."""

    def test_empty_report_is_healthy(self):
        """Test that empty report is considered healthy."""
        report = IntegrityReport()
        assert report.is_healthy
        assert report.error_count == 0
        assert report.warning_count == 0

    def test_report_with_errors_not_healthy(self):
        """Test that report with errors is not healthy."""
        report = IntegrityReport(
            issues=[
                IntegrityIssue(
                    severity=IssueSeverity.ERROR,
                    table="test",
                    column="col",
                    issue_type="test_error",
                    message="Test error",
                )
            ]
        )
        assert not report.is_healthy
        assert report.error_count == 1

    def test_report_with_warnings_is_healthy(self):
        """Test that report with only warnings is healthy."""
        report = IntegrityReport(
            issues=[
                IntegrityIssue(
                    severity=IssueSeverity.WARNING,
                    table="test",
                    column="col",
                    issue_type="test_warning",
                    message="Test warning",
                )
            ]
        )
        assert report.is_healthy
        assert report.warning_count == 1


class TestOrphanedRecords:
    """Tests for orphaned record detection."""

    def test_find_orphaned_records_empty_db(self, test_db):
        """Test orphan detection on empty database."""
        issues = find_orphaned_records(test_db)
        # Should not error on empty db
        assert isinstance(issues, list)

    def test_find_orphaned_records_with_valid_fks(self, test_db, session):
        """Test that valid FK relationships don't trigger errors."""
        from app.models import User, Area

        # Create user and area with valid FK
        user = User(email="test@example.com", google_id="google_123")
        session.add(user)
        session.flush()

        area = Area(title="Test Area", user_id=user.id)
        session.add(area)
        session.commit()

        issues = find_orphaned_records(test_db)

        # Should not find orphans for the area we just created
        area_issues = [i for i in issues if i.table == "areas"]
        assert len(area_issues) == 0


class TestEnumValidation:
    """Tests for enum value validation."""

    def test_validate_enum_values_empty_db(self, test_db):
        """Test enum validation on empty database."""
        issues = validate_enum_values(test_db)
        # Should not error on empty db
        assert isinstance(issues, list)

    def test_validate_enum_values_valid_data(self, test_db, session):
        """Test that valid enum values don't trigger errors."""
        from app.models import User, Project

        user = User(email="test@example.com", google_id="google_123")
        session.add(user)
        session.flush()

        project = Project(
            title="Test Project",
            status="active",  # Valid status
            user_id=user.id,
        )
        session.add(project)
        session.commit()

        issues = validate_enum_values(test_db)

        # Should not find issues for valid status
        project_status_issues = [
            i for i in issues if i.table == "projects" and i.column == "status"
        ]
        assert len(project_status_issues) == 0


class TestTableStatistics:
    """Tests for table statistics."""

    def test_get_table_statistics_empty(self, test_db):
        """Test stats on empty database."""
        stats = get_table_statistics(test_db)

        # Should have entries for tables
        assert "projects" in stats
        assert "tasks" in stats

        # All should be empty
        for table, info in stats.items():
            assert info["row_count"] == 0

    def test_get_table_statistics_with_data(self, test_db, session):
        """Test stats with data."""
        from app.models import User

        # Add some users
        for i in range(5):
            session.add(User(email=f"user{i}@example.com", google_id=f"google_{i}"))
        session.commit()

        stats = get_table_statistics(test_db)

        assert stats["users"]["row_count"] == 5


class TestRunAllChecks:
    """Tests for comprehensive integrity checking."""

    def test_run_all_checks_empty_db(self, test_db):
        """Test running all checks on empty database."""
        report = run_all_checks(test_db)

        assert isinstance(report, IntegrityReport)
        assert report.tables_checked > 0
        # Empty db should be healthy
        assert report.is_healthy

    def test_run_all_checks_with_data(self, test_db, session):
        """Test running all checks with valid data."""
        from app.models import User, Project, Task

        user = User(email="test@example.com", google_id="google_123")
        session.add(user)
        session.flush()

        project = Project(title="Test", status="active", user_id=user.id)
        session.add(project)
        session.flush()

        task = Task(title="Task 1", project_id=project.id, status="pending")
        session.add(task)
        session.commit()

        report = run_all_checks(test_db)

        assert report.rows_checked >= 3
        # Valid data should be healthy
        assert report.is_healthy
