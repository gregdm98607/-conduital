"""
Round-trip tests for all 6 new entity markdown formats.

Each test writes entity data to a markdown file, reads it back,
and verifies all fields survive the round trip losslessly.
"""

import textwrap
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.sync.entity_markdown import (
    AreaMarkdown,
    ContextMarkdown,
    GoalMarkdown,
    InboxMarkdown,
    VisionMarkdown,
    WeeklyReviewMarkdown,
    ENTITY_HANDLERS,
)
from app.storage.local_folder import LocalFolderProvider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def tmp(tmp_path: Path) -> Path:
    return tmp_path


# ===================================================================
# AREA round-trip
# ===================================================================

class TestAreaMarkdown:
    def test_round_trip_full(self, tmp: Path):
        fp = tmp / "area.md"
        data = {
            "title": "Health & Fitness",
            "description": "Physical and mental well-being.",
            "standard_of_excellence": "Exercise 4x/week, sleep 7+ hours.",
            "health_score": 0.85,
            "review_frequency": "weekly",
            "is_archived": False,
            "last_reviewed_at": "2026-03-28T10:00:00+00:00",
            "folder_path": "20_Areas/Health",
        }
        AreaMarkdown.write(data, fp)
        parsed = AreaMarkdown.parse(fp)

        assert parsed["title"] == "Health & Fitness"
        assert parsed["description"] == "Physical and mental well-being."
        assert parsed["standard_of_excellence"] == "Exercise 4x/week, sleep 7+ hours."
        assert parsed["health_score"] == 0.85
        assert parsed["review_frequency"] == "weekly"
        assert parsed["is_archived"] is False
        assert parsed["folder_path"] == "20_Areas/Health"

    def test_round_trip_minimal(self, tmp: Path):
        fp = tmp / "area_min.md"
        data = {"title": "Work"}
        AreaMarkdown.write(data, fp)
        parsed = AreaMarkdown.parse(fp)

        assert parsed["title"] == "Work"
        assert parsed["health_score"] == 0.0
        assert parsed["review_frequency"] == "weekly"
        assert parsed["is_archived"] is False

    def test_filename_generation(self):
        name = AreaMarkdown.make_filename({"title": "Health & Fitness"})
        assert name == "health-&-fitness.md"

    def test_human_readable_file(self, tmp: Path):
        """The written file should be valid markdown parseable by hand."""
        fp = tmp / "area.md"
        AreaMarkdown.write({
            "title": "Finance",
            "description": "Track budgets.",
            "standard_of_excellence": "Review monthly.",
        }, fp)
        text = fp.read_text(encoding="utf-8")
        assert "---" in text  # frontmatter delimiters
        assert "title: Finance" in text
        assert "## Standard of Excellence" in text
        assert "Review monthly." in text


# ===================================================================
# GOAL round-trip
# ===================================================================

class TestGoalMarkdown:
    def test_round_trip_full(self, tmp: Path):
        fp = tmp / "goal.md"
        data = {
            "title": "Launch SaaS product",
            "description": "Build and ship the MVP by Q3 2026.",
            "timeframe": "1_year",
            "target_date": "2026-12-31",
            "status": "active",
        }
        GoalMarkdown.write(data, fp)
        parsed = GoalMarkdown.parse(fp)

        assert parsed["title"] == "Launch SaaS product"
        assert parsed["description"] == "Build and ship the MVP by Q3 2026."
        assert parsed["timeframe"] == "1_year"
        assert parsed["target_date"] == date(2026, 12, 31)
        assert parsed["status"] == "active"

    def test_round_trip_minimal(self, tmp: Path):
        fp = tmp / "goal_min.md"
        data = {"title": "Learn Rust"}
        GoalMarkdown.write(data, fp)
        parsed = GoalMarkdown.parse(fp)

        assert parsed["title"] == "Learn Rust"
        assert parsed["status"] == "active"
        assert parsed["timeframe"] is None

    def test_completed_goal(self, tmp: Path):
        fp = tmp / "goal_done.md"
        data = {
            "title": "Read 50 books",
            "status": "completed",
            "completed_at": "2026-03-15T14:30:00+00:00",
        }
        GoalMarkdown.write(data, fp)
        parsed = GoalMarkdown.parse(fp)

        assert parsed["status"] == "completed"
        assert parsed["completed_at"] is not None


# ===================================================================
# VISION round-trip
# ===================================================================

class TestVisionMarkdown:
    def test_round_trip_full(self, tmp: Path):
        fp = tmp / "vision.md"
        data = {
            "title": "Sustainable Living",
            "description": "In 5 years I want to live off-grid with a thriving homestead.",
            "timeframe": "5_year",
        }
        VisionMarkdown.write(data, fp)
        parsed = VisionMarkdown.parse(fp)

        assert parsed["title"] == "Sustainable Living"
        assert parsed["description"] == "In 5 years I want to live off-grid with a thriving homestead."
        assert parsed["timeframe"] == "5_year"

    def test_round_trip_minimal(self, tmp: Path):
        fp = tmp / "vision_min.md"
        data = {"title": "Life Purpose"}
        VisionMarkdown.write(data, fp)
        parsed = VisionMarkdown.parse(fp)

        assert parsed["title"] == "Life Purpose"
        assert parsed["description"] is None


# ===================================================================
# INBOX round-trip
# ===================================================================

class TestInboxMarkdown:
    def test_round_trip_full(self, tmp: Path):
        fp = tmp / "inbox.md"
        data = {
            "body_content": "Look into new project management tools for the team.",
            "captured_at": "2026-04-01T09:15:00+00:00",
            "source": "voice",
            "processed_at": "2026-04-01T18:00:00+00:00",
            "result_type": "task",
            "result_id": 42,
        }
        InboxMarkdown.write(data, fp)
        parsed = InboxMarkdown.parse(fp)

        assert parsed["body_content"] == "Look into new project management tools for the team."
        assert parsed["source"] == "voice"
        assert parsed["result_type"] == "task"
        assert parsed["result_id"] == 42

    def test_round_trip_unprocessed(self, tmp: Path):
        fp = tmp / "inbox2.md"
        data = {
            "body_content": "Quick thought about the garden.",
            "captured_at": "2026-04-01T08:00:00+00:00",
            "source": "web_ui",
        }
        InboxMarkdown.write(data, fp)
        parsed = InboxMarkdown.parse(fp)

        assert parsed["body_content"] == "Quick thought about the garden."
        assert parsed["processed_at"] is None
        assert parsed["result_type"] is None

    def test_filename_includes_date(self):
        name = InboxMarkdown.make_filename({
            "captured_at": datetime(2026, 4, 1, tzinfo=timezone.utc),
            "body_content": "Quick thought",
        })
        assert name.startswith("2026-04-01-")
        assert name.endswith(".md")


# ===================================================================
# CONTEXT round-trip
# ===================================================================

class TestContextMarkdown:
    def test_round_trip_full(self, tmp: Path):
        fp = tmp / "context.md"
        data = {
            "name": "@computer",
            "context_type": "tool",
            "description": "Tasks requiring a computer.",
            "icon": "laptop",
        }
        ContextMarkdown.write(data, fp)
        parsed = ContextMarkdown.parse(fp)

        assert parsed["name"] == "@computer"
        assert parsed["context_type"] == "tool"
        assert parsed["description"] == "Tasks requiring a computer."
        assert parsed["icon"] == "laptop"

    def test_round_trip_minimal(self, tmp: Path):
        fp = tmp / "ctx_min.md"
        data = {"name": "@errands"}
        ContextMarkdown.write(data, fp)
        parsed = ContextMarkdown.parse(fp)

        assert parsed["name"] == "@errands"
        assert parsed["context_type"] is None
        assert parsed["description"] is None

    def test_filename(self):
        name = ContextMarkdown.make_filename({"name": "@phone"})
        assert name == "@phone.md"


# ===================================================================
# WEEKLY REVIEW round-trip
# ===================================================================

class TestWeeklyReviewMarkdown:
    def test_round_trip_full(self, tmp: Path):
        fp = tmp / "review.md"
        data = {
            "completed_at": "2026-03-28T17:00:00+00:00",
            "notes": "Reviewed all projects. Cleared inbox. Feeling good.",
            "ai_summary": "Productive week. 3 projects advanced, inbox at zero.",
        }
        WeeklyReviewMarkdown.write(data, fp)
        parsed = WeeklyReviewMarkdown.parse(fp)

        assert parsed["notes"] == "Reviewed all projects. Cleared inbox. Feeling good."
        assert parsed["ai_summary"] == "Productive week. 3 projects advanced, inbox at zero."
        assert parsed["completed_at"] is not None

    def test_round_trip_notes_only(self, tmp: Path):
        fp = tmp / "review2.md"
        data = {
            "completed_at": "2026-03-21T16:00:00+00:00",
            "notes": "Quick review this week.",
        }
        WeeklyReviewMarkdown.write(data, fp)
        parsed = WeeklyReviewMarkdown.parse(fp)

        assert parsed["notes"] == "Quick review this week."
        assert parsed["ai_summary"] is None

    def test_filename_includes_date(self):
        name = WeeklyReviewMarkdown.make_filename({
            "completed_at": datetime(2026, 3, 28, tzinfo=timezone.utc),
        })
        assert name == "2026-03-28-weekly-review.md"

    def test_human_readable_file(self, tmp: Path):
        fp = tmp / "review.md"
        WeeklyReviewMarkdown.write({
            "completed_at": "2026-03-28T17:00:00+00:00",
            "notes": "All good.",
            "ai_summary": "Solid week.",
        }, fp)
        text = fp.read_text(encoding="utf-8")
        assert "## AI Summary" in text
        assert "Solid week." in text


# ===================================================================
# ENTITY_HANDLERS registry
# ===================================================================

class TestEntityHandlersRegistry:
    def test_all_six_types_registered(self):
        expected = {"area", "goal", "vision", "inbox", "context", "weekly_review"}
        assert set(ENTITY_HANDLERS.keys()) == expected

    def test_each_handler_has_required_methods(self):
        for name, handler in ENTITY_HANDLERS.items():
            assert hasattr(handler, "parse"), f"{name} missing parse"
            assert hasattr(handler, "write"), f"{name} missing write"
            assert hasattr(handler, "make_filename"), f"{name} missing make_filename"
            assert hasattr(handler, "ENTITY_TYPE"), f"{name} missing ENTITY_TYPE"
            assert hasattr(handler, "DIRECTORY"), f"{name} missing DIRECTORY"


# ===================================================================
# LocalFolderProvider integration tests
# ===================================================================

class TestLocalFolderProviderEntities:
    """Test that LocalFolderProvider correctly dispatches to entity handlers."""

    @pytest.fixture()
    def provider(self, tmp: Path) -> LocalFolderProvider:
        # Create all entity directories
        for handler in ENTITY_HANDLERS.values():
            (tmp / handler.DIRECTORY).mkdir(exist_ok=True)
        (tmp / "10_Projects").mkdir(exist_ok=True)
        return LocalFolderProvider(
            root_path=tmp,
            watch_directories=["10_Projects"],
        )

    def test_write_and_read_area(self, provider: LocalFolderProvider):
        data = {
            "title": "Health",
            "description": "Stay healthy.",
            "health_score": 0.9,
            "review_frequency": "weekly",
        }
        eid = provider.write_entity("area", "", data)
        result = provider.read_entity("area", eid)

        assert result["title"] == "Health"
        assert result["health_score"] == 0.9
        assert "entity_id" in result
        assert "file_hash" in result

    def test_write_and_read_goal(self, provider: LocalFolderProvider):
        data = {"title": "Ship MVP", "status": "active", "timeframe": "1_year"}
        eid = provider.write_entity("goal", "", data)
        result = provider.read_entity("goal", eid)
        assert result["title"] == "Ship MVP"
        assert result["status"] == "active"

    def test_write_and_read_vision(self, provider: LocalFolderProvider):
        data = {"title": "Dream Big", "description": "Long-term vision.", "timeframe": "5_year"}
        eid = provider.write_entity("vision", "", data)
        result = provider.read_entity("vision", eid)
        assert result["title"] == "Dream Big"
        assert result["timeframe"] == "5_year"

    def test_write_and_read_inbox(self, provider: LocalFolderProvider):
        data = {
            "body_content": "Remember to call dentist.",
            "captured_at": "2026-04-01T10:00:00+00:00",
            "source": "web_ui",
        }
        eid = provider.write_entity("inbox", "", data)
        result = provider.read_entity("inbox", eid)
        assert result["body_content"] == "Remember to call dentist."
        assert result["source"] == "web_ui"

    def test_write_and_read_context(self, provider: LocalFolderProvider):
        data = {"name": "@phone", "context_type": "tool", "description": "Phone tasks."}
        eid = provider.write_entity("context", "", data)
        result = provider.read_entity("context", eid)
        assert result["name"] == "@phone"
        assert result["context_type"] == "tool"

    def test_write_and_read_weekly_review(self, provider: LocalFolderProvider):
        data = {
            "completed_at": "2026-03-28T17:00:00+00:00",
            "notes": "Good week.",
            "ai_summary": "All projects green.",
        }
        eid = provider.write_entity("weekly_review", "", data)
        result = provider.read_entity("weekly_review", eid)
        assert result["notes"] == "Good week."
        assert result["ai_summary"] == "All projects green."

    def test_list_entities_area(self, provider: LocalFolderProvider):
        provider.write_entity("area", "", {"title": "Health", "health_score": 0.5})
        provider.write_entity("area", "", {"title": "Work", "health_score": 0.7})
        entities = provider.list_entities("area")
        assert len(entities) == 2

    def test_delete_entity(self, provider: LocalFolderProvider):
        eid = provider.write_entity("context", "", {"name": "@temp"})
        assert provider.exists("context", eid) is True
        assert provider.delete_entity("context", eid) is True
        assert provider.exists("context", eid) is False

    def test_exists_false_for_missing(self, provider: LocalFolderProvider):
        assert provider.exists("goal", "goals/nonexistent.md") is False

    def test_unsupported_type_still_raises(self, provider: LocalFolderProvider):
        with pytest.raises(ValueError, match="Unsupported entity type"):
            provider.read_entity("spaceship", "x.md")
