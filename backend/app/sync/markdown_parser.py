"""
Markdown parser for extracting project and task data from Second Brain files
"""

import re
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import frontmatter


class MarkdownParser:
    """Parse markdown files with YAML frontmatter and task checkboxes"""

    # Regex patterns
    TASK_CHECKBOX_PATTERN = re.compile(
        r"^(?P<indent>\s*)-\s*\[(?P<checked>[ xX])\]\s*(?P<title>.+?)(?:\s*<!--\s*(?P<marker>tracker:task:\w+)(?::(?P<type>\w+))?\s*-->)?$"
    )

    HEADING_PATTERN = re.compile(r"^#{1,6}\s+(.+)$")

    @staticmethod
    def parse_file(file_path: Path) -> dict:
        """
        Parse a markdown file and extract project metadata and tasks

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary with 'metadata', 'content', and 'tasks'
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Parse frontmatter
        with file_path.open("r", encoding="utf-8") as f:
            post = frontmatter.load(f)

        metadata = dict(post.metadata)
        content = post.content

        # Extract title from first heading if not in metadata
        if "title" not in metadata:
            for line in content.split("\n"):
                match = MarkdownParser.HEADING_PATTERN.match(line.strip())
                if match:
                    metadata["title"] = match.group(1)
                    break

        # Parse tasks from content
        tasks = MarkdownParser.parse_tasks(content)

        return {
            "metadata": metadata,
            "content": content,
            "tasks": tasks,
            "file_path": str(file_path),
        }

    @staticmethod
    def parse_tasks(content: str) -> list[dict]:
        """
        Parse task checkboxes from markdown content

        Supports format:
        - [ ] Task title <!-- tracker:task:abc123 -->
        - [x] Completed task <!-- tracker:task:def456 -->
        - [ ] Waiting task <!-- tracker:task:ghi789:waiting -->

        Args:
            content: Markdown content

        Returns:
            List of task dictionaries
        """
        tasks = []
        lines = content.split("\n")

        for line_number, line in enumerate(lines, start=1):
            match = MarkdownParser.TASK_CHECKBOX_PATTERN.match(line)
            if match:
                task_data = {
                    "title": match.group("title").strip(),
                    "checked": match.group("checked").lower() == "x",
                    "marker": match.group("marker"),
                    "task_type": match.group("type"),  # waiting, someday_maybe, etc.
                    "line_number": line_number,
                    "indent_level": len(match.group("indent")),
                }
                tasks.append(task_data)

        return tasks

    @staticmethod
    def parse_project_metadata(metadata: dict) -> dict:
        """
        Parse project metadata from frontmatter

        Expected fields:
        - tracker_id: int
        - project_status: str
        - priority: int
        - momentum_score: float
        - area: str
        - phases: list

        Args:
            metadata: YAML frontmatter dict

        Returns:
            Cleaned project data dict
        """
        project_data = {}

        # Simple field mappings
        field_map = {
            "tracker_id": "id",
            "project_status": "status",
            "priority": "priority",
            "momentum_score": "momentum_score",
            "area": "area_name",
            "title": "title",
            "description": "description",
        }

        for yaml_key, db_key in field_map.items():
            if yaml_key in metadata:
                project_data[db_key] = metadata[yaml_key]

        # Parse dates
        if "target_completion_date" in metadata:
            project_data["target_completion_date"] = MarkdownParser.parse_date(
                metadata["target_completion_date"]
            )

        if "last_synced" in metadata:
            project_data["last_synced"] = MarkdownParser.parse_datetime(
                metadata["last_synced"]
            )

        # Parse phases
        if "phases" in metadata and isinstance(metadata["phases"], list):
            project_data["phases"] = metadata["phases"]

        return project_data

    @staticmethod
    def parse_date(value) -> Optional[date]:
        """Parse a date from various formats"""
        if value is None:
            return None
        if isinstance(value, date):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                return None
        return None

    @staticmethod
    def parse_datetime(value) -> Optional[datetime]:
        """Parse a datetime from various formats"""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    @staticmethod
    def extract_task_marker(line: str) -> Optional[str]:
        """
        Extract task marker from a line

        Args:
            line: Markdown line

        Returns:
            Task marker (e.g., 'tracker:task:abc123') or None
        """
        match = MarkdownParser.TASK_CHECKBOX_PATTERN.match(line)
        if match:
            return match.group("marker")
        return None

    @staticmethod
    def is_task_line(line: str) -> bool:
        """Check if a line is a task checkbox"""
        return bool(MarkdownParser.TASK_CHECKBOX_PATTERN.match(line))

    @staticmethod
    def get_section_tasks(content: str, section_heading: str) -> list[dict]:
        """
        Get tasks under a specific heading

        Args:
            content: Markdown content
            section_heading: Heading to look for (e.g., "Next Actions", "Waiting For")

        Returns:
            List of tasks under that heading
        """
        lines = content.split("\n")
        in_section = False
        section_tasks = []

        for line_number, line in enumerate(lines, start=1):
            # Check if we've entered the target section
            if MarkdownParser.HEADING_PATTERN.match(line.strip()):
                heading_text = MarkdownParser.HEADING_PATTERN.match(line.strip()).group(1)
                if section_heading.lower() in heading_text.lower():
                    in_section = True
                    continue
                elif in_section:
                    # Reached a new section, stop
                    break

            # If we're in the target section, collect tasks
            if in_section:
                match = MarkdownParser.TASK_CHECKBOX_PATTERN.match(line)
                if match:
                    task_data = {
                        "title": match.group("title").strip(),
                        "checked": match.group("checked").lower() == "x",
                        "marker": match.group("marker"),
                        "task_type": match.group("type"),
                        "line_number": line_number,
                    }
                    section_tasks.append(task_data)

        return section_tasks
