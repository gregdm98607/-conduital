"""
Auto-Discovery Service

Coordinates automatic project and area discovery triggered by folder changes.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.discovery_service import ProjectDiscoveryService
from app.services.area_discovery_service import AreaDiscoveryService
from app.models.project import Project
from app.models.area import Area

logger = logging.getLogger(__name__)


class AutoDiscoveryService:
    """
    Service for automatic project and area discovery triggered by file system events.
    """

    def __init__(self, db: Optional[Session] = None):
        """
        Initialize auto-discovery service.

        Args:
            db: Database session (creates new if not provided)
        """
        self.db = db or SessionLocal()
        self._owns_session = db is None

    def __del__(self):
        """Close database session if we created it"""
        if self._owns_session and self.db:
            self.db.close()

    # --- Project methods ---

    def discover_folder(self, folder_path: Path) -> dict:
        """
        Discover and import a single project folder.

        Args:
            folder_path: Path to project folder

        Returns:
            dict: Discovery result with project info
        """
        logger.info(f"Auto-discovering folder: {folder_path.name}")

        try:
            discovery = ProjectDiscoveryService(self.db)
            result = discovery._process_project_folder(folder_path)

            if result.get("imported"):
                logger.info(
                    f"Auto-discovered: {result.get('title')} "
                    f"(ID: {result.get('project_id')})"
                )
            else:
                logger.warning(
                    f"Skipped: {folder_path.name} "
                    f"(reason: {result.get('reason', 'unknown')})"
                )

            return {
                "success": True,
                "folder": folder_path.name,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Error auto-discovering {folder_path.name}: {e}")
            return {
                "success": False,
                "folder": folder_path.name,
                "error": str(e),
            }

    def handle_folder_renamed(self, old_path: Path, new_path: Path) -> dict:
        """
        Handle project folder rename.

        Updates project title and file_path in database.

        Args:
            old_path: Old folder path
            new_path: New folder path

        Returns:
            dict: Update result
        """
        logger.info(f"Handling folder rename: {old_path.name} -> {new_path.name}")

        try:
            # Find project by old file path
            old_file_path = str(old_path / f"{old_path.name}.md")
            project = self.db.query(Project).filter(
                Project.file_path == old_file_path
            ).first()

            if not project:
                # Project not in database yet, just discover it
                logger.info(f"Project not found, discovering as new: {new_path.name}")
                return self.discover_folder(new_path)

            # Update project
            pattern = re.compile(ProjectDiscoveryService(self.db).project_pattern.pattern)
            match = pattern.match(new_path.name)

            if match:
                # Extract new title
                new_title = match.group(3).replace("_", " ")

                # Update project
                project.title = new_title
                project.file_path = str(new_path / f"{new_path.name}.md")

                self.db.commit()

                logger.info(f"Updated project: {old_path.name} -> {new_title}")

                return {
                    "success": True,
                    "action": "renamed",
                    "project_id": project.id,
                    "old_title": project.title,
                    "new_title": new_title,
                }
            else:
                logger.warning(f"New folder name doesn't match pattern: {new_path.name}")
                return {
                    "success": False,
                    "action": "renamed",
                    "error": "New folder name doesn't match pattern",
                }

        except Exception as e:
            logger.error(f"Error handling rename: {e}")
            return {
                "success": False,
                "action": "renamed",
                "error": str(e),
            }

    def handle_folder_moved(self, old_path: Path, new_path: Path) -> dict:
        """
        Handle project folder move.

        Args:
            old_path: Old folder path
            new_path: New folder path

        Returns:
            dict: Move result
        """
        logger.info(f"Handling folder move: {old_path} -> {new_path}")

        try:
            return self.discover_folder(new_path)

        except Exception as e:
            logger.error(f"Error handling move: {e}")
            return {
                "success": False,
                "action": "moved",
                "error": str(e),
            }

    # --- Area methods ---

    def discover_area_folder(self, folder_path: Path) -> dict:
        """
        Discover and import a single area folder.

        Args:
            folder_path: Path to area folder

        Returns:
            dict: Discovery result with area info
        """
        logger.info(f"Auto-discovering area folder: {folder_path.name}")

        try:
            service = AreaDiscoveryService(self.db)
            result = service._process_area_folder(folder_path)

            if result.get("imported"):
                logger.info(
                    f"Area imported: {result.get('title')} "
                    f"(ID: {result.get('area_id')})"
                )
            else:
                logger.warning(
                    f"Skipped area: {folder_path.name} "
                    f"(reason: {result.get('reason', 'unknown')})"
                )

            return {
                "success": True,
                "folder": folder_path.name,
                "result": result,
            }

        except Exception as e:
            logger.error(f"Error auto-discovering area {folder_path.name}: {e}")
            return {
                "success": False,
                "folder": folder_path.name,
                "error": str(e),
            }

    def handle_area_renamed(self, old_path: Path, new_path: Path) -> dict:
        """
        Handle area folder rename.

        Updates area title and folder_path in database.

        Args:
            old_path: Old folder path
            new_path: New folder path

        Returns:
            dict: Update result
        """
        logger.info(f"Handling area rename: {old_path.name} -> {new_path.name}")

        try:
            old_folder_name = old_path.name
            old_relative_path = f"20_Areas/{old_folder_name}"
            old_absolute_path = str(old_path)

            # Try relative path first, then absolute, then contains
            area = self.db.query(Area).filter(
                Area.folder_path == old_relative_path
            ).first()

            if not area:
                area = self.db.query(Area).filter(
                    Area.folder_path == old_absolute_path
                ).first()

            if not area:
                area = self.db.query(Area).filter(
                    Area.folder_path.contains(old_folder_name)
                ).first()

            if not area:
                logger.info(f"Area not found, discovering as new: {new_path.name}")
                return self.discover_area_folder(new_path)

            # Extract new title from folder name
            from app.core.config import settings

            pattern = re.compile(settings.AREA_FOLDER_PATTERN)
            match = pattern.match(new_path.name)

            if match:
                new_title = match.group(3).replace("_", " ")
                area.title = new_title
                area.folder_path = f"20_Areas/{new_path.name}"

                self.db.commit()

                logger.info(f"Updated area: {old_path.name} -> {new_title}")

                return {
                    "success": True,
                    "action": "renamed",
                    "area_id": area.id,
                    "new_title": new_title,
                }
            else:
                logger.warning(f"New folder name doesn't match pattern: {new_path.name}")
                return {
                    "success": False,
                    "action": "renamed",
                    "error": "New folder name doesn't match area pattern",
                }

        except Exception as e:
            logger.error(f"Error handling area rename: {e}")
            return {
                "success": False,
                "action": "renamed",
                "error": str(e),
            }

    def handle_area_moved(self, old_path: Path, new_path: Path) -> dict:
        """
        Handle area folder move.

        Args:
            old_path: Old folder path
            new_path: New folder path

        Returns:
            dict: Move result
        """
        logger.info(f"Handling area move: {old_path} -> {new_path}")

        try:
            return self.discover_area_folder(new_path)
        except Exception as e:
            logger.error(f"Error handling area move: {e}")
            return {
                "success": False,
                "action": "moved",
                "error": str(e),
            }


# Callback functions for file watcher integration
# These create their own AutoDiscoveryService (which owns its session)

def on_new_folder_created(folder_path: Path):
    """Callback for new project folder creation."""
    logger.info(f"New project folder detected: {folder_path.name}")
    service = AutoDiscoveryService()
    result = service.discover_folder(folder_path)

    if result["success"] and result["result"].get("imported"):
        project_info = result["result"]
        logger.info(f"Project imported: {project_info.get('title')}")
    else:
        logger.warning(f"Could not import folder: {result.get('error', 'Unknown reason')}")


def on_folder_renamed(old_path: Path, new_path: Path):
    """Callback for project folder rename."""
    logger.info(f"Project folder renamed: {old_path.name} -> {new_path.name}")
    service = AutoDiscoveryService()
    result = service.handle_folder_renamed(old_path, new_path)

    if result["success"]:
        logger.info(f"Project updated: {result.get('new_title', result.get('result', {}).get('title'))}")
    else:
        logger.warning(f"Update failed: {result.get('error')}")


def on_folder_moved(old_path: Path, new_path: Path):
    """Callback for project folder move."""
    logger.info(f"Project folder moved: {old_path.name} -> {new_path.name}")
    service = AutoDiscoveryService()
    result = service.handle_folder_moved(old_path, new_path)

    if result["success"]:
        logger.info("Project re-discovered at new location")
    else:
        logger.warning(f"Re-discovery failed: {result.get('error')}")


def on_area_created(folder_path: Path):
    """Callback for new area folder creation."""
    logger.info(f"New area folder detected: {folder_path.name}")
    service = AutoDiscoveryService()
    result = service.discover_area_folder(folder_path)

    if result["success"] and result["result"].get("imported"):
        area_info = result["result"]
        logger.info(f"Area imported: {area_info.get('title')}")
    else:
        logger.warning(f"Could not import area: {result.get('error', 'Unknown reason')}")


def on_area_renamed(old_path: Path, new_path: Path):
    """Callback for area folder rename."""
    logger.info(f"Area folder renamed: {old_path.name} -> {new_path.name}")
    service = AutoDiscoveryService()
    result = service.handle_area_renamed(old_path, new_path)

    if result["success"]:
        logger.info(f"Area updated: {result.get('new_title')}")
    else:
        logger.warning(f"Area update failed: {result.get('error')}")


def on_area_moved(old_path: Path, new_path: Path):
    """Callback for area folder move."""
    logger.info(f"Area folder moved: {old_path.name} -> {new_path.name}")
    service = AutoDiscoveryService()
    result = service.handle_area_moved(old_path, new_path)

    if result["success"]:
        logger.info("Area re-discovered at new location")
    else:
        logger.warning(f"Area re-discovery failed: {result.get('error')}")
