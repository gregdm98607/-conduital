"""
Pydantic schemas for starter templates (BACKLOG-087).

These are response models for the read-only template gallery and the apply
result. Template definitions themselves live in
``app.services.template_data``.
"""

from pydantic import BaseModel


class TemplateSummary(BaseModel):
    """Card-level metadata for a starter template."""

    id: str
    name: str
    tagline: str
    icon: str
    description: str
    area_count: int
    project_count: int
    task_count: int


class TemplateList(BaseModel):
    templates: list[TemplateSummary]


class TemplateAreaPreview(BaseModel):
    title: str
    description: str | None = None


class TemplateTaskPreview(BaseModel):
    title: str
    is_next_action: bool


class TemplateProjectPreview(BaseModel):
    title: str
    area_title: str
    outcome_statement: str | None = None
    phase_template: str | None = None
    phases: list[str] = []
    tasks: list[TemplateTaskPreview] = []


class TemplateDetail(TemplateSummary):
    """Full preview of everything a template will create."""

    areas: list[TemplateAreaPreview]
    projects: list[TemplateProjectPreview]


class TemplateApplyResult(BaseModel):
    """Summary returned after applying a template."""

    template_id: str
    areas_created: int
    projects_created: int
    tasks_created: int
    first_project_id: int | None = None
