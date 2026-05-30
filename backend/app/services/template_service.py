"""
Template service — read and apply persona starter templates (BACKLOG-087).

``apply_template`` turns a hardcoded template definition (see
``template_data.py``) into real Areas, Projects, ProjectPhases and Tasks in a
single transaction. PhaseTemplate rows are get-or-created by their unique name,
which both activates the previously-dormant PhaseTemplate model and keeps
re-applies idempotent.
"""

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db_utils import log_activity
from app.models.area import Area
from app.models.phase_template import PhaseTemplate
from app.models.project import Project
from app.models.project_phase import ProjectPhase
from app.models.task import Task
from app.services.intelligence_service import IntelligenceService
from app.services.project_service import _calculate_next_review_date
from app.services.template_data import STARTER_TEMPLATES, get_template_definition


class TemplateService:
    """Read and apply persona starter templates."""

    @staticmethod
    def list_templates() -> list[dict[str, Any]]:
        """Return template summaries with preview counts (no DB access)."""
        summaries: list[dict[str, Any]] = []
        for t in STARTER_TEMPLATES:
            summaries.append(
                {
                    "id": t["id"],
                    "name": t["name"],
                    "tagline": t["tagline"],
                    "icon": t["icon"],
                    "description": t["description"],
                    "area_count": len(t["areas"]),
                    "project_count": len(t["projects"]),
                    "task_count": sum(len(p["tasks"]) for p in t["projects"]),
                }
            )
        return summaries

    @staticmethod
    def get_template(template_id: str) -> Optional[dict[str, Any]]:
        """Return a full template detail (areas/projects/phases/tasks) or None."""
        t = get_template_definition(template_id)
        if t is None:
            return None

        phase_by_name = {pt["name"]: pt for pt in t["phase_templates"]}
        area_title_by_key = {a["key"]: a["title"] for a in t["areas"]}

        projects: list[dict[str, Any]] = []
        for p in t["projects"]:
            phases: list[str] = []
            if p.get("phase_template"):
                pt = phase_by_name.get(p["phase_template"])
                if pt:
                    phases = list(pt["phases"])
            projects.append(
                {
                    "title": p["title"],
                    "area_title": area_title_by_key.get(p["area_key"], ""),
                    "outcome_statement": p["outcome_statement"],
                    "phase_template": p.get("phase_template"),
                    "phases": phases,
                    "tasks": [
                        {"title": tk["title"], "is_next_action": tk["is_next_action"]}
                        for tk in p["tasks"]
                    ],
                }
            )

        return {
            "id": t["id"],
            "name": t["name"],
            "tagline": t["tagline"],
            "icon": t["icon"],
            "description": t["description"],
            "area_count": len(t["areas"]),
            "project_count": len(t["projects"]),
            "task_count": sum(len(p["tasks"]) for p in t["projects"]),
            "areas": [
                {"title": a["title"], "description": a["description"]} for a in t["areas"]
            ],
            "projects": projects,
        }

    @staticmethod
    def apply_template(
        db: Session, template_id: str, user_id: Optional[int] = None
    ) -> Optional[dict[str, Any]]:
        """
        Apply a template: create Areas, Projects (with phases), and Tasks.

        Returns a summary dict, or ``None`` if the template id is unknown.
        Areas (by title) and PhaseTemplates (by unique name) are
        get-or-created so re-applying is safe; Projects and Tasks are always
        created fresh (applying is a deliberate user action).
        """
        t = get_template_definition(template_id)
        if t is None:
            return None

        now = datetime.now(timezone.utc)

        # 1. get-or-create PhaseTemplate rows (activates the dormant model)
        phase_templates: dict[str, PhaseTemplate] = {}
        for pt in t["phase_templates"]:
            existing = db.execute(
                select(PhaseTemplate).where(PhaseTemplate.name == pt["name"])
            ).scalar_one_or_none()
            if existing is None:
                existing = PhaseTemplate(
                    name=pt["name"],
                    description=pt.get("description"),
                    phases_json=json.dumps(
                        [
                            {"name": name, "order": i + 1}
                            for i, name in enumerate(pt["phases"])
                        ]
                    ),
                )
                db.add(existing)
                db.flush()
            phase_templates[pt["name"]] = existing

        # 2. get-or-create Areas by (user_id, title)
        areas_by_key: dict[str, Area] = {}
        areas_created = 0
        for a in t["areas"]:
            existing = db.execute(
                select(Area).where(
                    Area.title == a["title"],
                    Area.user_id == user_id,
                    Area.deleted_at.is_(None),
                )
            ).scalar_one_or_none()
            if existing is None:
                existing = Area(
                    user_id=user_id,
                    title=a["title"],
                    description=a.get("description"),
                    standard_of_excellence=a.get("standard_of_excellence"),
                )
                db.add(existing)
                db.flush()
                areas_created += 1
            areas_by_key[a["key"]] = existing

        # 3-5. Projects, their phases, and starter tasks
        created_projects: list[Project] = []
        tasks_created = 0
        for p in t["projects"]:
            area = areas_by_key.get(p["area_key"])
            phase_template = (
                phase_templates.get(p["phase_template"])
                if p.get("phase_template")
                else None
            )

            project = Project(
                user_id=user_id,
                title=p["title"],
                outcome_statement=p.get("outcome_statement"),
                purpose=p.get("purpose"),
                status="active",
                priority=p.get("priority", 5),
                area_id=area.id if area else None,
                phase_template_id=phase_template.id if phase_template else None,
                last_activity_at=now,
                next_review_date=_calculate_next_review_date("weekly"),
            )
            db.add(project)
            db.flush()
            log_activity(
                db,
                entity_type="project",
                entity_id=project.id,
                action_type="created",
                details={
                    "title": project.title,
                    "source": "template",
                    "template_id": template_id,
                },
            )

            # Phases from the referenced phase template (first phase is active)
            first_phase: Optional[ProjectPhase] = None
            if phase_template is not None:
                pt_def = next(
                    (x for x in t["phase_templates"] if x["name"] == p["phase_template"]),
                    None,
                )
                if pt_def:
                    for i, phase_name in enumerate(pt_def["phases"]):
                        phase = ProjectPhase(
                            project_id=project.id,
                            phase_name=phase_name,
                            phase_order=i + 1,
                            status="active" if i == 0 else "pending",
                            started_at=now if i == 0 else None,
                        )
                        db.add(phase)
                        if i == 0:
                            first_phase = phase
                    db.flush()

            # Starter tasks (attached to the active phase when present)
            for tk in p["tasks"]:
                db.add(
                    Task(
                        title=tk["title"],
                        project_id=project.id,
                        phase_id=first_phase.id if first_phase else None,
                        status="pending",
                        task_type="action",
                        context=tk.get("context"),
                        energy_level=tk.get("energy_level"),
                        is_next_action=tk.get("is_next_action", False),
                        urgency_zone="opportunity_now",
                        priority=p.get("priority", 5),
                    )
                )
                tasks_created += 1
            db.flush()

            created_projects.append(project)

        # 6. Live momentum now that tasks + activity exist
        for project in created_projects:
            project.momentum_score = IntelligenceService.calculate_momentum_score(
                db, project
            )

        db.commit()
        for project in created_projects:
            db.refresh(project)

        return {
            "template_id": template_id,
            "areas_created": areas_created,
            "projects_created": len(created_projects),
            "tasks_created": tasks_created,
            "first_project_id": created_projects[0].id if created_projects else None,
        }
