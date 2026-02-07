"""
Core Module

The core module provides fundamental functionality that all other modules depend on:
- User model and authentication (when enabled)
- Areas for organizational grouping
- Contexts for GTD context filtering
- Goals and Visions for GTD horizons
- Base database and configuration

This module is ALWAYS enabled - it cannot be disabled.
"""

from typing import Optional, Any

from fastapi import APIRouter

from app.modules.base import ModuleBase, ModuleInfo, ModuleCategory


class CoreModule(ModuleBase):
    """
    Core module - always enabled, provides fundamental functionality.
    """

    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="core",
            display_name="Core",
            description="Core functionality including users, areas, contexts, and GTD horizons",
            category=ModuleCategory.CORE,
            version="1.0.0",
            dependencies=[],  # No dependencies - this is the base
        )

    @property
    def router(self) -> Optional[APIRouter]:
        """
        Core module provides these routers:
        - /auth - Authentication (when AUTH_ENABLED)
        - /areas - Area management
        - /contexts - Context management
        - /goals - Goal management
        - /visions - Vision management
        """
        from app.modules.core.routes import router
        return router

    @property
    def prefix(self) -> str:
        # Core routes are mounted at various prefixes, not a single one
        return ""

    async def initialize(self, app_context: dict[str, Any]) -> None:
        """Initialize core module"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Core module initialized")

    async def shutdown(self) -> None:
        """Cleanup core module"""
        pass
