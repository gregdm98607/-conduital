"""
Area Discovery Service

Scans 20_Areas folder structure and discovers areas based on
numbered prefix conventions (xx.xx Area_Name).
"""

import re
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.area import Area
from app.sync.sync_engine import SyncEngine

logger = logging.getLogger(__name__)


class AreaDiscoveryService:
    """
    Service for discovering and importing areas from synced notes folder structure.
    """

    def __init__(self, db: Session):
        self.db = db
        self.sync_engine = SyncEngine(db)
        # Use same pattern as projects: xx.xx Area_Name
        self.area_pattern = re.compile(settings.PROJECT_FOLDER_PATTERN)

    def discover_all_areas(self) -> dict:
        """
        Scan 20_Areas directory and discover all areas.

        Returns:
            dict: Statistics about discovered areas
        """
        areas_dir = settings.SECOND_BRAIN_PATH / "20_Areas"

        if not areas_dir.exists():
            logger.error(f"Areas directory not found: {areas_dir}")
            return {
                "success": False,
                "error": f"Directory not found: {areas_dir}",
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
        for folder in areas_dir.iterdir():
            if not folder.is_dir():
                continue

            stats["discovered"] += 1

            try:
                result = self._process_area_folder(folder)
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

    def _process_area_folder(self, folder: Path) -> dict:
        """
        Process a single area folder.

        Args:
            folder: Path to area folder

        Returns:
            dict: Processing result
        """
        folder_name = folder.name
        match = self.area_pattern.match(folder_name)

        if not match:
            logger.debug(f"Folder '{folder_name}' doesn't match pattern, skipping")
            return {"imported": False, "reason": "no_pattern_match"}

        area_prefix = match.group(1)  # First two digits (e.g., "01")
        area_number = match.group(2)  # Second two digits (e.g., "05")
        area_title = match.group(3).replace("_", " ")  # Area name

        logger.info(f"Processing: {folder_name} -> Area: {area_prefix}.{area_number} {area_title}")

        # Check if area already exists by folder_path (try multiple formats to handle legacy data)
        relative_folder_path = f"20_Areas/{folder_name}"
        absolute_folder_path = str(folder)

        # Check by relative path first (preferred format)
        existing_area = self.db.query(Area).filter(
            Area.folder_path == relative_folder_path
        ).first()

        # Check by absolute path (legacy or inconsistent data)
        if not existing_area:
            existing_area = self.db.query(Area).filter(
                Area.folder_path == absolute_folder_path
            ).first()

        # Check by folder_path containing the folder name (catch any path format)
        if not existing_area:
            existing_area = self.db.query(Area).filter(
                Area.folder_path.contains(folder_name)
            ).first()

        # Also check by title to avoid duplicates
        if not existing_area:
            existing_area = self.db.query(Area).filter(
                Area.title == area_title
            ).first()

        # Look for markdown file in folder
        markdown_files = list(folder.glob("*.md"))

        if markdown_files:
            # Use first markdown file (or look for one matching folder name)
            md_file = self._select_primary_markdown(markdown_files, folder_name)

            # Try to sync markdown file to get area metadata
            try:
                area_data = self._parse_area_markdown(md_file)
            except Exception as e:
                logger.warning(f"Error parsing area markdown {md_file}: {e}")
                area_data = {}
        else:
            logger.debug(f"No markdown files found in {folder_name}")
            area_data = {}

        # Create or update area
        if existing_area:
            # Update existing area
            existing_area.title = area_title
            existing_area.folder_path = relative_folder_path

            # Update from parsed markdown if available
            if "description" in area_data:
                existing_area.description = area_data["description"]
            if "standard_of_excellence" in area_data:
                existing_area.standard_of_excellence = area_data["standard_of_excellence"]
            if "review_frequency" in area_data:
                existing_area.review_frequency = area_data["review_frequency"]

            self.db.commit()

            logger.info(f"Updated existing area: {existing_area.title} (ID: {existing_area.id})")
            return {
                "imported": True,
                "area_id": existing_area.id,
                "title": existing_area.title,
                "updated": True
            }
        else:
            # Create new area
            new_area = Area(
                title=area_title,
                description=area_data.get("description", f"Auto-discovered from folder: {folder_name}"),
                folder_path=relative_folder_path,
                standard_of_excellence=area_data.get("standard_of_excellence"),
                review_frequency=area_data.get("review_frequency", "weekly"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )

            self.db.add(new_area)
            self.db.commit()

            logger.info(f"Created new area: {new_area.title} (ID: {new_area.id})")
            return {
                "imported": True,
                "area_id": new_area.id,
                "title": new_area.title,
                "updated": False
            }

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

        # Look for common area file names
        common_names = ["area.md", "README.md", "index.md"]
        for common_name in common_names:
            for md_file in markdown_files:
                if md_file.name.lower() == common_name.lower():
                    return md_file

        # Default to first file
        return markdown_files[0]

    def _parse_area_markdown(self, md_file: Path) -> dict:
        """
        Parse area markdown file for metadata.

        Looks for frontmatter or structured content to extract:
        - description
        - standard_of_excellence
        - review_frequency

        Args:
            md_file: Path to markdown file

        Returns:
            dict: Parsed area metadata
        """
        area_data = {}

        try:
            content = md_file.read_text(encoding='utf-8')

            # Try to parse frontmatter
            if content.startswith('---'):
                # Simple frontmatter parsing
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].strip()

                    # Parse frontmatter fields
                    for line in frontmatter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip().lower()
                            value = value.strip()

                            if key == 'description':
                                area_data['description'] = value
                            elif key == 'standard_of_excellence' or key == 'standard':
                                area_data['standard_of_excellence'] = value
                            elif key == 'review_frequency' or key == 'review':
                                # Normalize to daily/weekly/monthly
                                value_lower = value.lower()
                                if 'daily' in value_lower:
                                    area_data['review_frequency'] = 'daily'
                                elif 'weekly' in value_lower:
                                    area_data['review_frequency'] = 'weekly'
                                elif 'monthly' in value_lower:
                                    area_data['review_frequency'] = 'monthly'

                    # Use body as description if not in frontmatter
                    if 'description' not in area_data and body:
                        # Take first paragraph
                        first_para = body.split('\n\n')[0].strip()
                        if first_para and not first_para.startswith('#'):
                            area_data['description'] = first_para
            else:
                # No frontmatter, use first paragraph as description
                first_para = content.strip().split('\n\n')[0].strip()
                if first_para and not first_para.startswith('#'):
                    area_data['description'] = first_para

        except Exception as e:
            logger.warning(f"Error parsing markdown file {md_file}: {e}")

        return area_data

    def suggest_area_mappings(self) -> dict:
        """
        Analyze area folders and suggest prefix mappings for areas
        that aren't yet discovered.

        Returns:
            dict: Suggested mappings and statistics
        """
        areas_dir = settings.SECOND_BRAIN_PATH / "20_Areas"

        if not areas_dir.exists():
            return {"error": "Areas directory not found"}

        suggestions = {}
        stats = {
            "total_folders": 0,
            "matched_folders": 0,
            "unmatched_folders": 0
        }

        for folder in areas_dir.iterdir():
            if not folder.is_dir():
                continue

            stats["total_folders"] += 1
            match = self.area_pattern.match(folder.name)

            if match:
                stats["matched_folders"] += 1
                area_prefix = match.group(1)
                area_number = match.group(2)
                area_title = match.group(3).replace("_", " ")

                # Check if already discovered
                existing = self.db.query(Area).filter(
                    Area.title == area_title
                ).first()

                if not existing:
                    suggestions[f"{area_prefix}.{area_number}"] = {
                        "title": area_title,
                        "folder": folder.name,
                        "prefix": area_prefix,
                        "number": area_number
                    }
            else:
                stats["unmatched_folders"] += 1

        return {
            "suggestions": suggestions,
            "stats": stats
        }
