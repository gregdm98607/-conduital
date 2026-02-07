"""
Markdown writer for generating Second Brain files from database data
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import frontmatter

from app.models.project import Project
from app.models.task import Task


class MarkdownWriter:
    """Write project and task data to markdown files with YAML frontmatter"""

    @staticmethod
    def write_project_file(project: Project, file_path: Path, preserve_content: bool = True) -> None:
        """
        Write project data to markdown file

        Args:
            project: Project model instance
            file_path: Path to write to
            preserve_content: If True, preserve existing content body
        """
        # Read existing content if preserving
        existing_content = ""
        if preserve_content and file_path.exists():
            with file_path.open("r", encoding="utf-8") as f:
                post = frontmatter.load(f)
                existing_content = post.content

        # Build metadata
        metadata = MarkdownWriter.build_project_metadata(project)

        # Build content if not preserving
        if not existing_content:
            existing_content = MarkdownWriter.build_project_content(project)

        # Update task checkboxes in content
        content = MarkdownWriter.update_task_checkboxes(existing_content, project.tasks)

        # Create frontmatter post
        post = frontmatter.Post(content, **metadata)

        # Write to file
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

    @staticmethod
    def build_project_metadata(project: Project) -> dict:
        """
        Build YAML frontmatter metadata from project

        Args:
            project: Project model instance

        Returns:
            Metadata dictionary
        """
        metadata = {
            "tracker_id": project.id,
            "project_status": project.status,
            "priority": project.priority,
            "momentum_score": round(project.momentum_score, 2),
            "last_synced": datetime.utcnow().isoformat(),
        }

        # Add optional fields
        if project.area:
            metadata["area"] = project.area.title

        if project.target_completion_date:
            metadata["target_completion_date"] = project.target_completion_date.isoformat()

        if project.last_activity_at:
            metadata["last_activity_at"] = project.last_activity_at.isoformat()

        # Add phases if any
        if project.phases:
            metadata["phases"] = [
                {
                    "name": phase.phase_name,
                    "status": phase.status,
                    "order": phase.phase_order,
                }
                for phase in sorted(project.phases, key=lambda p: p.phase_order)
            ]

        return metadata

    @staticmethod
    def build_project_content(project: Project) -> str:
        """
        Build markdown content body for new project file

        Args:
            project: Project model instance

        Returns:
            Markdown content string
        """
        lines = []

        # Title
        lines.append(f"# {project.title}")
        lines.append("")

        # Description
        if project.description:
            lines.append(project.description)
            lines.append("")

        # Next Actions section
        next_actions = [t for t in project.tasks if t.is_next_action and t.status != "completed"]
        if next_actions:
            lines.append("## Next Actions")
            lines.append("")
            for task in next_actions:
                lines.append(MarkdownWriter.format_task_line(task))
            lines.append("")

        # Pending Tasks section
        pending = [
            t
            for t in project.tasks
            if not t.is_next_action and t.status == "pending"
        ]
        if pending:
            lines.append("## Tasks")
            lines.append("")
            for task in pending:
                lines.append(MarkdownWriter.format_task_line(task))
            lines.append("")

        # Waiting For section
        waiting = [t for t in project.tasks if t.status == "waiting"]
        if waiting:
            lines.append("## Waiting For")
            lines.append("")
            for task in waiting:
                lines.append(MarkdownWriter.format_task_line(task))
            lines.append("")

        # Completed section
        completed = [t for t in project.tasks if t.status == "completed"]
        if completed:
            lines.append("## Completed")
            lines.append("")
            for task in completed[:10]:  # Show last 10
                lines.append(MarkdownWriter.format_task_line(task))
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def format_task_line(task: Task) -> str:
        """
        Format a task as a markdown checkbox line

        Args:
            task: Task model instance

        Returns:
            Formatted line with checkbox and marker
        """
        checkbox = "[x]" if task.status == "completed" else "[ ]"
        marker = f"<!-- {task.file_marker} -->" if task.file_marker else ""

        # Add type suffix if special type
        if task.task_type == "waiting_for":
            marker = marker.replace("-->", ":waiting -->")
        elif task.task_type == "someday_maybe":
            marker = marker.replace("-->", ":someday -->")

        line = f"- {checkbox} {task.title}"
        if marker:
            line += f" {marker}"

        return line

    @staticmethod
    def update_task_checkboxes(content: str, tasks: list[Task]) -> str:
        """
        Update task checkboxes in existing content

        Args:
            content: Existing markdown content
            tasks: List of tasks from database

        Returns:
            Updated content
        """
        lines = content.split("\n")

        # Build marker-to-task mapping
        task_map = {}
        for task in tasks:
            if task.file_marker:
                task_map[task.file_marker] = task

        # Update lines
        from app.sync.markdown_parser import MarkdownParser

        for i, line in enumerate(lines):
            if MarkdownParser.is_task_line(line):
                marker = MarkdownParser.extract_task_marker(line)
                if marker and marker in task_map:
                    task = task_map[marker]
                    # Update the checkbox status
                    checkbox = "[x]" if task.status == "completed" else "[ ]"
                    # Preserve indent and replace checkbox
                    import re
                    lines[i] = re.sub(r"-\s*\[[xX ]?\]", f"- {checkbox}", line, count=1)

        return "\n".join(lines)

    @staticmethod
    def create_project_file_path(project: Project, root_path: Path) -> Path:
        """
        Generate file path for a project

        Args:
            project: Project model instance
            root_path: Second Brain root path

        Returns:
            Path object for project file
        """
        # If project already has a file_path, use it
        if project.file_path:
            return Path(project.file_path)

        # Otherwise, generate path based on area
        if project.area and project.area.folder_path:
            folder = root_path / project.area.folder_path
        else:
            folder = root_path / "10_Projects" / "01_Active"

        # Sanitize title for filename
        safe_title = MarkdownWriter.sanitize_filename(project.title)
        filename = f"{safe_title}.md"

        return folder / filename

    @staticmethod
    def sanitize_filename(title: str) -> str:
        """
        Sanitize a title for use as a filename

        Args:
            title: Project title

        Returns:
            Safe filename string
        """
        # Replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_title = title
        for char in invalid_chars:
            safe_title = safe_title.replace(char, "_")

        # Replace multiple spaces/underscores with single
        import re
        safe_title = re.sub(r"[_\s]+", "_", safe_title)

        # Trim and limit length
        safe_title = safe_title.strip("_")[:100]

        return safe_title
