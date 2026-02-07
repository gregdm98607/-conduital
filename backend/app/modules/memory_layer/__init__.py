"""
Memory Layer Module

The memory layer module provides persistent context for AI assistants,
ported from the proactive-assistant project.

Key features:
- Structured memory objects with priority scores
- Namespace-based organization
- Effective date management
- Priority-based retrieval
- JSON file or database storage

This module is part of the "proactive_assistant" commercial configuration.

Dependencies:
- core: For user context
- projects: For project data integration
"""

from typing import Optional, Any

from fastapi import APIRouter

from app.modules.base import ModuleBase, ModuleInfo, ModuleCategory


class MemoryLayerModule(ModuleBase):
    """
    Memory Layer module - persistent AI context.
    """

    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="memory_layer",
            display_name="Memory Layer",
            description="Persistent memory for AI assistants with priority-based retrieval",
            category=ModuleCategory.FEATURE,
            version="1.0.0",
            dependencies=["core", "projects"],
            optional_dependencies=["ai_context"],
        )

    @property
    def router(self) -> Optional[APIRouter]:
        """
        Memory Layer module provides:
        - /memory - Memory object CRUD
        - /memory/hydrate - Context hydration endpoints
        - /memory/namespaces - Namespace management
        """
        from app.modules.memory_layer.routes import router
        return router

    @property
    def prefix(self) -> str:
        return "memory"

    async def initialize(self, app_context: dict[str, Any]) -> None:
        """Initialize memory layer module"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Memory Layer module initialized")

        # Ensure memory tables exist
        # The models will be created via alembic migrations

    async def shutdown(self) -> None:
        """Cleanup memory layer module"""
        pass
