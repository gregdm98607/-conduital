"""
Projects Module

The projects module provides project and task management:
- Projects with phases and momentum tracking
- Tasks with next action attributes
- Next actions prioritization
- File sync with markdown notes
- Project discovery from folder structure

This module is part of the base configuration and is always enabled.
"""

from typing import Optional, Any

from fastapi import APIRouter

from app.modules.base import ModuleBase, ModuleInfo, ModuleCategory


class ProjectsModule(ModuleBase):
    """
    Projects module - core project and task management.
    """

    @property
    def info(self) -> ModuleInfo:
        return ModuleInfo(
            name="projects",
            display_name="Projects",
            description="Project and task management with momentum tracking",
            category=ModuleCategory.CORE,
            version="1.0.0",
            dependencies=["core"],  # Depends on core for areas, contexts, etc.
        )

    @property
    def router(self) -> Optional[APIRouter]:
        """
        Projects module provides these routers:
        - /projects - Project CRUD and management
        - /tasks - Task CRUD and management
        - /next-actions - Smart next action recommendations
        - /sync - File synchronization
        - /discovery - Project discovery from folders
        - /intelligence - Momentum and AI features
        """
        from app.modules.projects.routes import router
        return router

    @property
    def prefix(self) -> str:
        return ""  # Routes have their own prefixes

    async def initialize(self, app_context: dict[str, Any]) -> None:
        """Initialize projects module"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Projects module initialized")

        # Start folder watcher if auto-discovery is enabled
        settings = app_context.get("settings")
        if settings and settings.AUTO_DISCOVERY_ENABLED:
            from app.sync.folder_watcher import start_folder_watcher
            from app.services.auto_discovery_service import (
                on_new_folder_created,
                on_folder_renamed,
                on_folder_moved,
                on_area_created,
                on_area_renamed,
                on_area_moved,
            )
            start_folder_watcher(
                on_folder_created=on_new_folder_created,
                on_folder_renamed=on_folder_renamed,
                on_folder_moved=on_folder_moved,
                on_area_created=on_area_created,
                on_area_renamed=on_area_renamed,
                on_area_moved=on_area_moved,
            )
            logger.info("Auto-discovery enabled via projects module")

    async def shutdown(self) -> None:
        """Cleanup projects module"""
        from app.sync.file_watcher import stop_file_watcher
        from app.sync.folder_watcher import stop_folder_watcher
        import logging
        logger = logging.getLogger(__name__)

        try:
            stop_file_watcher()
        except Exception as e:
            logger.debug(f"File watcher cleanup: {e}")

        try:
            stop_folder_watcher()
        except Exception as e:
            logger.debug(f"Folder watcher cleanup: {e}")
