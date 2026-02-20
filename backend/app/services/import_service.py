"""
Import service - data import from JSON backup

BACKLOG-090: Data import for round-trip portability.

Strategy: merge import -- skip entities that already exist (matched by title),
insert new ones. Old IDs are remapped so foreign-key chains (area->project->task)
stay consistent regardless of the existing DB state.
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import Area, Context, Goal, InboxItem, Project, Task, Vision

logger = logging.getLogger(__name__)

SUPPORTED_EXPORT_VERSIONS = {"1.0.0"}


@dataclass
class ImportResult:
    """Summary returned to the caller after an import run."""

    areas_imported: int = 0
    goals_imported: int = 0
    visions_imported: int = 0
    contexts_imported: int = 0
    projects_imported: int = 0
    tasks_imported: int = 0
    inbox_items_imported: int = 0
    areas_skipped: int = 0
    goals_skipped: int = 0
    visions_skipped: int = 0
    contexts_skipped: int = 0
    projects_skipped: int = 0
    tasks_skipped: int = 0
    inbox_items_skipped: int = 0
    warnings: list = field(default_factory=list)

    @property
    def total_imported(self) -> int:
        return (
            self.areas_imported
            + self.goals_imported
            + self.visions_imported
            + self.contexts_imported
            + self.projects_imported
            + self.tasks_imported
            + self.inbox_items_imported
        )

    @property
    def total_skipped(self) -> int:
        return (
            self.areas_skipped
            + self.goals_skipped
            + self.visions_skipped
            + self.contexts_skipped
            + self.projects_skipped
            + self.tasks_skipped
            + self.inbox_items_skipped
        )


class ImportService:
    """Service for importing data from a JSON export backup."""

    @classmethod
    def validate_export(cls, data: dict) -> list:
        """
        Validate an export dict before importing.
        Returns a list of error strings. Empty list = valid.
        """
        errors = []

        if not isinstance(data, dict):
            errors.append("Export data must be a JSON object.")
            return errors

        metadata = data.get("metadata")
        if not metadata:
            errors.append("Missing 'metadata' key.")
        else:
            version = metadata.get("export_version")
            if version not in SUPPORTED_EXPORT_VERSIONS:
                errors.append(
                    f"Unsupported export version '{version}'. "
                    f"Supported: {sorted(SUPPORTED_EXPORT_VERSIONS)}"
                )

        for key in ("areas", "goals", "visions", "contexts", "projects", "inbox_items"):
            if key in data and not isinstance(data[key], list):
                errors.append(f"'{key}' must be a list.")

        return errors

    @classmethod
    def import_from_json(cls, data: dict, db: Session) -> ImportResult:
        """
        Import entities from a JSON export dict into the database.

        Merge strategy: match existing by title (case-insensitive), skip
        duplicates, insert new ones. Foreign-key IDs are remapped.
        """
        result = ImportResult()

        area_id_map: dict = {}
        goal_id_map: dict = {}
        vision_id_map: dict = {}
        project_id_map: dict = {}

        cls._import_areas(data.get("areas", []), db, result, area_id_map)
        cls._import_goals(data.get("goals", []), db, result, goal_id_map)
        cls._import_visions(data.get("visions", []), db, result, vision_id_map)
        cls._import_contexts(data.get("contexts", []), db, result)
        cls._import_projects(
            data.get("projects", []),
            db,
            result,
            project_id_map,
            area_id_map,
            goal_id_map,
            vision_id_map,
        )
        cls._import_inbox_items(data.get("inbox_items", []), db, result)

        db.commit()
        logger.info(
            f"Import complete: {result.total_imported} imported, "
            f"{result.total_skipped} skipped, {len(result.warnings)} warnings"
        )
        return result

    @classmethod
    def _import_areas(cls, areas, db, result, id_map):
        existing_titles = {
            a.title.lower()
            for a in db.query(Area).filter(Area.deleted_at.is_(None)).all()
        }
        for raw in areas:
            title = (raw.get("title") or "").strip()
            if not title:
                result.warnings.append("Skipped area with empty title.")
                result.areas_skipped += 1
                continue
            if title.lower() in existing_titles:
                result.areas_skipped += 1
                existing = db.query(Area).filter(Area.title.ilike(title)).first()
                if existing and raw.get("id"):
                    id_map[raw["id"]] = existing.id
                continue
            area = Area(
                title=title,
                description=raw.get("description"),
                folder_path=raw.get("folder_path"),
                standard_of_excellence=raw.get("standard_of_excellence"),
                review_frequency=raw.get("review_frequency"),
                last_reviewed_at=cls._parse_datetime(raw.get("last_reviewed_at")),
            )
            db.add(area)
            db.flush()
            if raw.get("id"):
                id_map[raw["id"]] = area.id
            existing_titles.add(title.lower())
            result.areas_imported += 1

    @classmethod
    def _import_goals(cls, goals, db, result, id_map):
        existing_titles = {g.title.lower() for g in db.query(Goal).all()}
        for raw in goals:
            title = (raw.get("title") or "").strip()
            if not title:
                result.warnings.append("Skipped goal with empty title.")
                result.goals_skipped += 1
                continue
            if title.lower() in existing_titles:
                result.goals_skipped += 1
                existing = db.query(Goal).filter(Goal.title.ilike(title)).first()
                if existing and raw.get("id"):
                    id_map[raw["id"]] = existing.id
                continue
            goal = Goal(
                title=title,
                description=raw.get("description"),
                timeframe=raw.get("timeframe"),
                target_date=cls._parse_date(raw.get("target_date")),
                status=raw.get("status") or "active",
            )
            db.add(goal)
            db.flush()
            if raw.get("id"):
                id_map[raw["id"]] = goal.id
            existing_titles.add(title.lower())
            result.goals_imported += 1

    @classmethod
    def _import_visions(cls, visions, db, result, id_map):
        existing_titles = {v.title.lower() for v in db.query(Vision).all()}
        for raw in visions:
            title = (raw.get("title") or "").strip()
            if not title:
                result.warnings.append("Skipped vision with empty title.")
                result.visions_skipped += 1
                continue
            if title.lower() in existing_titles:
                result.visions_skipped += 1
                existing = db.query(Vision).filter(Vision.title.ilike(title)).first()
                if existing and raw.get("id"):
                    id_map[raw["id"]] = existing.id
                continue
            vision = Vision(
                title=title,
                description=raw.get("description"),
                timeframe=raw.get("timeframe"),
            )
            db.add(vision)
            db.flush()
            if raw.get("id"):
                id_map[raw["id"]] = vision.id
            existing_titles.add(title.lower())
            result.visions_imported += 1

    @classmethod
    def _import_contexts(cls, contexts, db, result):
        existing_names = {c.name.lower() for c in db.query(Context).all()}
        for raw in contexts:
            name = (raw.get("name") or "").strip()
            if not name:
                result.warnings.append("Skipped context with empty name.")
                result.contexts_skipped += 1
                continue
            if name.lower() in existing_names:
                result.contexts_skipped += 1
                continue
            ctx = Context(
                name=name,
                context_type=raw.get("context_type"),
                description=raw.get("description"),
                icon=raw.get("icon"),
            )
            db.add(ctx)
            db.flush()
            existing_names.add(name.lower())
            result.contexts_imported += 1

    @classmethod
    def _import_projects(cls, projects, db, result, project_id_map,
                         area_id_map, goal_id_map, vision_id_map):
        existing_titles = {
            p.title.lower()
            for p in db.query(Project).filter(Project.deleted_at.is_(None)).all()
        }
        for raw in projects:
            title = (raw.get("title") or "").strip()
            if not title:
                result.warnings.append("Skipped project with empty title.")
                result.projects_skipped += 1
                continue
            if title.lower() in existing_titles:
                result.projects_skipped += 1
                result.tasks_skipped += len(raw.get("tasks") or [])
                existing = db.query(Project).filter(Project.title.ilike(title)).first()
                if existing and raw.get("id"):
                    project_id_map[raw["id"]] = existing.id
                continue

            old_area_id = raw.get("area_id")
            old_goal_id = raw.get("goal_id")
            old_vision_id = raw.get("vision_id")

            project = Project(
                title=title,
                description=raw.get("description"),
                outcome_statement=raw.get("outcome_statement"),
                status=raw.get("status") or "active",
                priority=raw.get("priority") or 5,
                area_id=area_id_map.get(old_area_id) if old_area_id else None,
                goal_id=goal_id_map.get(old_goal_id) if old_goal_id else None,
                vision_id=vision_id_map.get(old_vision_id) if old_vision_id else None,
                target_completion_date=cls._parse_date(raw.get("target_completion_date")),
                review_frequency=raw.get("review_frequency"),
                file_path=raw.get("file_path"),
            )
            db.add(project)
            db.flush()
            if raw.get("id"):
                project_id_map[raw["id"]] = project.id
            existing_titles.add(title.lower())
            result.projects_imported += 1

            for task_raw in raw.get("tasks") or []:
                cls._import_task(task_raw, project.id, db, result)

    @classmethod
    def _import_task(cls, raw, project_id, db, result):
        title = (raw.get("title") or "").strip()
        if not title:
            result.warnings.append(f"Skipped task with empty title in project {project_id}.")
            result.tasks_skipped += 1
            return
        task = Task(
            project_id=project_id,
            title=title,
            description=raw.get("description"),
            status=raw.get("status") or "pending",
            task_type=raw.get("task_type") or "action",
            priority=raw.get("priority") or 5,
            context=raw.get("context"),
            energy_level=raw.get("energy_level"),
            location=raw.get("location"),
            estimated_minutes=raw.get("estimated_minutes"),
            actual_minutes=raw.get("actual_minutes"),
            due_date=cls._parse_date(raw.get("due_date")),
            defer_until=cls._parse_date(raw.get("defer_until")),
            is_next_action=bool(raw.get("is_next_action", False)),
            is_two_minute_task=bool(raw.get("is_two_minute_task", False)),
            is_unstuck_task=bool(raw.get("is_unstuck_task", False)),
            urgency_zone=raw.get("urgency_zone"),
            waiting_for=raw.get("waiting_for"),
            sequence_order=raw.get("sequence_order"),
        )
        db.add(task)
        result.tasks_imported += 1

    @classmethod
    def _import_inbox_items(cls, items, db, result):
        for raw in items:
            content = (raw.get("content") or "").strip()
            if not content:
                result.warnings.append("Skipped inbox item with empty content.")
                result.inbox_items_skipped += 1
                continue
            item = InboxItem(
                content=content,
                source=raw.get("source") or "import",
                captured_at=cls._parse_datetime(raw.get("captured_at"))
                or datetime.now(timezone.utc),
            )
            db.add(item)
            result.inbox_items_imported += 1

    @staticmethod
    def _parse_datetime(value) -> datetime | None:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _parse_date(value) -> date | None:
        if not value:
            return None
        try:
            return date.fromisoformat(str(value)[:10])
        except (ValueError, TypeError):
            return None
