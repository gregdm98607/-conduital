"""
AI Context Module

The AI Context module provides AI-specific context management:
- Context aggregation from multiple sources
- Macro execution (Good Morning Board, Weekly Review, etc.)
- Persona-based routing
- Project-memory integration

This module enhances the memory layer with AI-specific features.

Dependencies:
- core: For user context
- projects: For project data
- memory_layer: For memory objects (optional but recommended)
"""

from typing import Optional, Any

from fastapi import APIRouter

from app.modules.base import ModuleBase, ModuleInfo, ModuleCategory


class AIContextModule(ModuleBase):
    """
    AI Context module - AI-specific context features.
    """

    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="ai_context",
            display_name="AI Context",
            description="AI-specific context aggregation, macros, and persona routing",
            category=ModuleCategory.INTEGRATION,
            version="1.0.0",
            dependencies=["core", "projects"],
            optional_dependencies=["memory_layer"],
        )

    @property
    def router(self) -> Optional[APIRouter]:
        """
        AI Context module provides:
        - /ai/context - Aggregated context for AI
        - /ai/macros - Macro execution
        - /ai/personas - Persona configuration
        """
        from app.modules.ai_context.routes import router
        return router

    @property
    def prefix(self) -> str:
        return "ai"

    async def initialize(self, app_context: dict[str, Any]) -> None:
        """Initialize AI context module"""
        import logging
        logger = logging.getLogger(__name__)

        settings = app_context.get("settings")
        if settings and settings.AI_FEATURES_ENABLED:
            logger.info("AI Context module initialized (AI features enabled)")
        else:
            logger.info("AI Context module initialized (AI features disabled - limited functionality)")

    async def shutdown(self) -> None:
        """Cleanup AI context module"""
        pass
