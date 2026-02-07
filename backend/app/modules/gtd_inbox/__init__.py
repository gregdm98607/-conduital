"""
GTD Inbox Module

The GTD Inbox module provides GTD-specific workflow features:
- Inbox capture and processing
- Weekly review automation
- Waiting-for tracking
- Someday/Maybe lists

This module is optional and part of the "gtd" commercial configuration.

Dependencies:
- core: For user context
- projects: For project/task integration
"""

from typing import Optional, Any

from fastapi import APIRouter

from app.modules.base import ModuleBase, ModuleInfo, ModuleCategory


class GTDInboxModule(ModuleBase):
    """
    GTD Inbox module - optional GTD workflow features.
    """

    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="gtd_inbox",
            display_name="GTD Inbox",
            description="GTD workflow features: inbox, weekly review, waiting-for",
            category=ModuleCategory.FEATURE,
            version="1.0.0",
            dependencies=["core", "projects"],
        )

    @property
    def router(self) -> Optional[APIRouter]:
        """
        GTD Inbox module provides:
        - /inbox - Inbox capture and processing
        - /reviews - Weekly/daily review endpoints

        Note: The inbox router already exists in app.api.inbox
        This module wraps it with proper feature gating.
        """
        from app.modules.gtd_inbox.routes import router
        return router

    @property
    def prefix(self) -> str:
        return "gtd"  # Routes under /api/v1/gtd/...

    async def initialize(self, app_context: dict[str, Any]) -> None:
        """Initialize GTD inbox module"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("GTD Inbox module initialized")

    async def shutdown(self) -> None:
        """Cleanup GTD inbox module"""
        pass
