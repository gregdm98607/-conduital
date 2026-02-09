"""
Inbox Module

The Inbox module provides workflow features:
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
    Inbox module - optional workflow features.
    """

    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="gtd_inbox",
            display_name="Inbox",
            description="Workflow features: inbox, weekly review, waiting-for",
            category=ModuleCategory.FEATURE,
            version="1.0.0",
            dependencies=["core", "projects"],
        )

    @property
    def router(self) -> Optional[APIRouter]:
        """
        Inbox module provides:
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
        """Initialize inbox module"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Inbox module initialized")

    async def shutdown(self) -> None:
        """Cleanup inbox module"""
        pass
