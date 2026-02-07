"""
Core module routes

Aggregates routes for core functionality:
- Authentication (auth)
- Areas
- Contexts
- Goals
- Visions
"""

from fastapi import APIRouter

# Import existing routers from app.api
from app.api import auth, areas, contexts, goals, visions

# Create a parent router that includes all core sub-routers
router = APIRouter()

# Note: These routers are also mounted directly in main.py for backwards compatibility.
# This aggregation is for the module system to track what belongs to core.

# The actual mounting with prefixes happens in main.py
# This router exists primarily for module introspection and future refactoring


def get_core_routers() -> list[tuple[APIRouter, str, list[str]]]:
    """
    Returns list of (router, prefix, tags) tuples for core module.

    This is used by the module system to understand what routes belong to core.
    """
    return [
        (auth.router, "/auth", ["Authentication"]),
        (areas.router, "/areas", ["Areas"]),
        (contexts.router, "/contexts", ["Contexts"]),
        (goals.router, "/goals", ["Goals"]),
        (visions.router, "/visions", ["Visions"]),
    ]
