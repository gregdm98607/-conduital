"""
Project Discovery Service

Scans synced notes folder structure and discovers projects based on
numbered prefix conventions (xx.xx Project_Name).
"""

import re
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.project import Project
from app.models.area import Area
from app.sync.sync_engine import SyncEngine

logger = logging.getLogger(__name__)


class ProjectDiscoveryService:
    """
    Service for discovering and importing projects from synced notes folder structure.
    """

    def __init__(self, db: Session):
        self.db = db
        self.sync_engine = SyncEngine(db)
        self.area_prefix_map = settings.area_prefix_map
        self.project_pattern = re.compile(settings.PROJECT_FOLDER_PATTERN)

    def discover_all_projects(self) -> dict:
        """
        Scan 10_Projects directory and discover all projects.

        Returns:
            dict: Statistics about discovered projects
        """
        projects_dir = settings.SECOND_BRAIN_PATH / "10_Projects"

        if not projects_dir.exists():
            logger.error(f"Projects directory not found: {projects_dir}")
            return {
                "success": False,
                "error": f"Directory not found: {projects_dir}",
                "discovered": 0,
                "imported": 0,
                "skipped": 0,
                "errors": []
            }

        stats = {
            "success": True,
            "discovered": 0,
            "imported": 0,
            "skipped": 0,
            "errors": []
        }

        # Scan all subdirectories
        for folder in projects_dir.iterdir():
            if not folder.is_dir():
                continue

            stats["discovered"] += 1

            try:
                result = self._process_project_folder(folder)
                if result["imported"]:
                    stats["imported"] += 1
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Error processing {folder.name}: {e}")
                stats["errors"].append({
                    "folder": folder.name,
                    "error": str(e)
                })

        return stats

    def _process_project_folder(self, folder: Path) -> dict:
        """
        Process a single project folder.

        Args:
            folder: Path to project folder

        Returns:
            dict: Processing result
        """
        folder_name = folder.name
        match = self.project_pattern.match(folder_name)

        if not match:
            logger.debug(f"Folder '{folder_name}' doesn't match pattern, skipping")
            return {"imported": False, "reason": "no_pattern_match"}

        area_prefix = match.group(1)  # First two digits (e.g., "01")
        project_number = match.group(2)  # Second two digits (e.g., "01")
        project_title = match.group(3).replace("_", " ")  # Project name

        logger.info(f"Processing: {folder_name} -> Area: {area_prefix}, Project: {project_title}")

        # Find or create area
        area = self._get_or_create_area(area_prefix)

        # Look for markdown file in folder
        markdown_files = list(folder.glob("*.md"))
        if not markdown_files:
            logger.warning(f"No markdown files found in {folder_name}")
            # Create project anyway with minimal info
            return self._create_project_from_folder(
                folder=folder,
                title=project_title,
                area=area,
                area_prefix=area_prefix,
                project_number=project_number
            )

        # Use first markdown file (or look for one matching folder name)
        md_file = self._select_primary_markdown(markdown_files, folder_name)

        # Sync markdown file to database (this creates/updates the project)
        try:
            project = self.sync_engine.sync_file_to_database(md_file)

            # Update project with discovered metadata
            if project:
                if not project.area_id and area:
                    project.area_id = area.id

                # Store folder metadata for future reference
                if not project.description or project.description == "":
                    project.description = f"Auto-discovered from folder: {folder_name}"

                self.db.commit()

                logger.info(f"Successfully imported project: {project.title} (ID: {project.id})")
                return {
                    "imported": True,
                    "project_id": project.id,
                    "title": project.title,
                    "area": area.title if area else None
                }

        except Exception as e:
            logger.error(f"Error syncing file {md_file}: {e}")
            raise

        return {"imported": False, "reason": "sync_failed"}

    def _select_primary_markdown(self, markdown_files: list[Path], folder_name: str) -> Path:
        """
        Select the primary markdown file from a list.
        Prefers files matching the folder name, otherwise takes the first.

        Args:
            markdown_files: List of markdown file paths
            folder_name: Name of the containing folder

        Returns:
            Path to primary markdown file
        """
        # Try to find file matching folder name
        folder_base = folder_name.replace(" ", "_")
        for md_file in markdown_files:
            if md_file.stem == folder_base or md_file.stem in folder_name:
                return md_file

        # Default to first file
        return markdown_files[0]

    def _get_or_create_area(self, area_prefix: str) -> Optional[Area]:
        """
        Get or create an Area based on prefix mapping.

        Args:
            area_prefix: Two-digit prefix (e.g., "01")

        Returns:
            Area object or None if no mapping exists
        """
        area_name = self.area_prefix_map.get(area_prefix)

        if not area_name:
            logger.warning(f"No area mapping for prefix '{area_prefix}' - configure in settings")
            return None

        # Check if area exists
        area = self.db.query(Area).filter(Area.title == area_name).first()

        if not area:
            # Create new area
            folder_path = f"20_Areas/{area_prefix}_" + area_name.replace(" ", "_")
            area = Area(
                title=area_name,
                description=f"Auto-created from project prefix {area_prefix}",
                folder_path=folder_path
            )
            self.db.add(area)
            self.db.commit()
            logger.info(f"Created new area: {area_name} (ID: {area.id})")

        return area

    def _create_project_from_folder(
        self,
        folder: Path,
        title: str,
        area: Optional[Area],
        area_prefix: str,
        project_number: str
    ) -> dict:
        """
        Create a minimal project when no markdown file exists.

        Args:
            folder: Project folder path
            title: Project title
            area: Area object
            area_prefix: Two-digit area prefix
            project_number: Two-digit project number

        Returns:
            dict: Creation result
        """
        # Check if project already exists with this folder path
        existing = self.db.query(Project).filter(
            Project.file_path == str(folder / f"{folder.name}.md")
        ).first()

        if existing:
            logger.info(f"Project already exists: {title}")
            return {"imported": False, "reason": "already_exists", "project_id": existing.id}

        # Create minimal project
        project = Project(
            title=title,
            description=f"Discovered from folder: {folder.name}\nNo markdown file found.",
            status="active",
            area_id=area.id if area else None,
            file_path=str(folder / f"{folder.name}.md"),  # Expected file path
            last_activity_at=datetime.now(timezone.utc)
        )

        self.db.add(project)
        self.db.commit()

        logger.info(f"Created minimal project: {title} (ID: {project.id})")

        return {
            "imported": True,
            "project_id": project.id,
            "title": title,
            "area": area.title if area else None,
            "note": "Created without markdown file"
        }

    def get_area_mappings(self) -> dict[str, str]:
        """
        Get current area prefix mappings.

        Returns:
            dict: Prefix to area name mapping
        """
        return self.area_prefix_map.copy()

    def suggest_area_mappings(self) -> dict[str, list[str]]:
        """
        Analyze project folders and suggest area mappings for unmapped prefixes.

        Returns:
            dict: Suggestions with prefixes and discovered folder names
        """
        projects_dir = settings.SECOND_BRAIN_PATH / "10_Projects"

        if not projects_dir.exists():
            return {}

        # Collect all prefixes
        prefix_folders = {}

        for folder in projects_dir.iterdir():
            if not folder.is_dir():
                continue

            match = self.project_pattern.match(folder.name)
            if match:
                prefix = match.group(1)
                project_name = match.group(3).replace("_", " ")

                if prefix not in prefix_folders:
                    prefix_folders[prefix] = []

                prefix_folders[prefix].append(project_name)

        # Filter to unmapped prefixes
        unmapped = {}
        for prefix, projects in prefix_folders.items():
            if prefix not in self.area_prefix_map:
                unmapped[prefix] = {
                    "project_count": len(projects),
                    "sample_projects": projects[:3],  # First 3 as examples
                    "suggested_area": f"Area {prefix}"  # Generic suggestion
                }

        return unmapped
