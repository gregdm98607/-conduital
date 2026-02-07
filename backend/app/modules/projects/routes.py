"""
Projects module routes

Aggregates routes for project and task management:
- Projects
- Tasks
- Next Actions
- Sync
- Discovery
- Intelligence
"""

from fastapi import APIRouter

# Import existing routers from app.api
from app.api import projects, tasks, next_actions, sync, discovery, intelligence

# Create a parent router (primarily for module introspection)
router = APIRouter()


def get_project_routers() -> list[tuple[APIRouter, str, list[str]]]:
    """
    Returns list of (router, prefix, tags) tuples for projects module.

    This is used by the module system to understand what routes belong to projects.
    """
    return [
        (projects.router, "/projects", ["Projects"]),
        (tasks.router, "/tasks", ["Tasks"]),
        (next_actions.router, "/next-actions", ["Next Actions"]),
        (sync.router, "/sync", ["Sync"]),
        (discovery.router, "/discovery", ["Discovery"]),
        (intelligence.router, "/intelligence", ["Intelligence"]),
    ]
