"""
LocalFolderProvider — reads/writes markdown files to a local folder.

Wraps the existing MarkdownParser and reuses its parsing logic.
Writing builds YAML-frontmatter markdown from plain dicts so the
storage layer stays decoupled from SQLAlchemy ORM models.
"""

import hashlib
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import frontmatter

from app.storage.base import Change, ChangeType, StorageProvider
from app.sync.markdown_parser import MarkdownParser

logger = logging.getLogger(__name__)

# Entity types this provider knows how to handle
SUPPORTED_ENTITY_TYPES = {"project"}


class LocalFolderProvider(StorageProvider):
    """
    Storage provider backed by a local folder of markdown files.

    Entity IDs are *relative* POSIX paths from ``root_path``
    (e.g. ``"10_Projects/01_Active/My_Project.md"``).

    The provider delegates markdown parsing to
    :class:`~app.sync.markdown_parser.MarkdownParser` and produces
    the same frontmatter format consumed by the existing sync engine.
    """

    def __init__(
        self,
        root_path: Path,
        watch_directories: Optional[list[str]] = None,
    ) -> None:
        self.root_path = Path(root_path)
        self.watch_directories = watch_directories or ["10_Projects", "20_Areas"]
        # snapshot: {relative_posix_path: sha256_hex} — built on first watch call
        self._hash_snapshot: dict[str, str] = {}
        self._snapshot_initialized = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _validate_entity_type(self, entity_type: str) -> None:
        if entity_type not in SUPPORTED_ENTITY_TYPES:
            raise ValueError(
                f"Unsupported entity type '{entity_type}'. "
                f"Supported: {SUPPORTED_ENTITY_TYPES}"
            )

    def _resolve_path(self, entity_id: str) -> Path:
        """Turn a relative entity_id into an absolute Path."""
        return self.root_path / entity_id

    def _relative_id(self, abs_path: Path) -> str:
        """Turn an absolute path into a relative POSIX entity_id."""
        return abs_path.relative_to(self.root_path).as_posix()

    @staticmethod
    def _file_hash(path: Path) -> str:
        """SHA-256 hex digest of a file's contents."""
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _sanitize_filename(title: str) -> str:
        """Sanitize a title for use as a filename (mirrors MarkdownWriter)."""
        invalid_chars = '<>:"/\\|?*'
        safe = title
        for ch in invalid_chars:
            safe = safe.replace(ch, "_")
        safe = re.sub(r"[_\s]+", "_", safe).strip("_")[:100]
        return safe

    # ------------------------------------------------------------------
    # StorageProvider interface — read
    # ------------------------------------------------------------------

    def read_entity(self, entity_type: str, entity_id: str) -> dict:
        self._validate_entity_type(entity_type)
        abs_path = self._resolve_path(entity_id)

        if not abs_path.exists():
            raise FileNotFoundError(
                f"{entity_type} not found: {entity_id}"
            )

        parsed = MarkdownParser.parse_file(abs_path)
        parsed["entity_id"] = entity_id
        parsed["file_hash"] = self._file_hash(abs_path)
        return parsed

    def exists(self, entity_type: str, entity_id: str) -> bool:
        self._validate_entity_type(entity_type)
        return self._resolve_path(entity_id).exists()

    def list_entities(self, entity_type: str) -> list[dict]:
        self._validate_entity_type(entity_type)
        results: list[dict] = []

        for watch_dir in self.watch_directories:
            dir_path = self.root_path / watch_dir
            if not dir_path.exists():
                continue
            for md_file in sorted(dir_path.rglob("*.md")):
                rel_id = self._relative_id(md_file)
                try:
                    parsed = MarkdownParser.parse_file(md_file)
                    results.append({
                        "entity_id": rel_id,
                        "metadata": parsed["metadata"],
                        "file_hash": self._file_hash(md_file),
                    })
                except Exception as exc:
                    logger.warning("Skipping %s: %s", md_file, exc)
        return results

    # ------------------------------------------------------------------
    # StorageProvider interface — write
    # ------------------------------------------------------------------

    def write_entity(
        self, entity_type: str, entity_id: str, data: dict
    ) -> str:
        self._validate_entity_type(entity_type)

        # Determine file path
        if entity_id:
            abs_path = self._resolve_path(entity_id)
        else:
            # Auto-generate from title
            title = data.get("title") or data.get("metadata", {}).get("title", "Untitled")
            safe_name = self._sanitize_filename(title)
            # Default to first watch directory
            folder = self.root_path / self.watch_directories[0]
            abs_path = folder / f"{safe_name}.md"
            entity_id = self._relative_id(abs_path)

        # Build frontmatter metadata
        metadata = self._build_write_metadata(data)

        # Build or preserve content body
        content = self._build_write_content(data, abs_path)

        # Write file
        post = frontmatter.Post(content, **metadata)
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        with abs_path.open("w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(post))

        logger.info("Wrote %s to %s", entity_type, abs_path.name)
        return entity_id

    def _build_write_metadata(self, data: dict) -> dict:
        """
        Build YAML frontmatter dict from entity data.

        Accepts the same keys the MarkdownParser emits (tracker_id,
        project_status, priority, …) as well as top-level convenience
        keys (title, status, etc.).
        """
        meta = dict(data.get("metadata", {}))

        # Convenience: top-level keys override nested metadata
        DIRECT_KEYS = [
            "tracker_id", "project_status", "status", "priority",
            "momentum_score", "area", "title", "description",
            "target_completion_date", "last_activity_at",
        ]
        for key in DIRECT_KEYS:
            if key in data and data[key] is not None:
                meta[key] = data[key]

        # Normalise: callers may pass "status" but frontmatter uses
        # "project_status"
        if "status" in meta and "project_status" not in meta:
            meta["project_status"] = meta.pop("status")

        # Always stamp last_synced
        meta["last_synced"] = datetime.now(timezone.utc).isoformat()

        return meta

    def _build_write_content(self, data: dict, abs_path: Path) -> str:
        """
        Build the markdown body.

        If the file already exists, preserve its body (updating task
        checkboxes from ``data['tasks']`` when present).  Otherwise
        generate a fresh body from the supplied data.
        """
        # Preserve existing content when file exists
        if abs_path.exists():
            with abs_path.open("r", encoding="utf-8") as f:
                post = frontmatter.load(f)
            content = post.content
        else:
            content = self._generate_fresh_content(data)

        # Update task checkboxes if tasks provided
        tasks = data.get("tasks")
        if tasks:
            content = self._update_task_lines(content, tasks)

        return content

    @staticmethod
    def _generate_fresh_content(data: dict) -> str:
        """Generate markdown body for a brand-new entity file."""
        lines: list[str] = []
        title = (
            data.get("title")
            or data.get("metadata", {}).get("title", "Untitled")
        )
        lines.append(f"# {title}")
        lines.append("")

        description = (
            data.get("description")
            or data.get("metadata", {}).get("description")
        )
        if description:
            lines.append(description)
            lines.append("")

        # Render tasks grouped by section
        tasks = data.get("tasks", [])
        if tasks:
            pending = [t for t in tasks if not t.get("checked")]
            completed = [t for t in tasks if t.get("checked")]

            if pending:
                lines.append("## Next Actions")
                lines.append("")
                for t in pending:
                    lines.append(LocalFolderProvider._format_task_line(t))
                lines.append("")

            if completed:
                lines.append("## Completed")
                lines.append("")
                for t in completed:
                    lines.append(LocalFolderProvider._format_task_line(t))
                lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _format_task_line(task: dict) -> str:
        """Format a task dict as a markdown checkbox line."""
        checkbox = "[x]" if task.get("checked") else "[ ]"
        title = task.get("title", "")
        marker = task.get("marker") or task.get("file_marker")
        suffix = ""
        if marker:
            task_type = task.get("task_type") or task.get("type")
            type_suffix = f":{task_type}" if task_type else ""
            suffix = f" <!-- {marker}{type_suffix} -->"
        return f"- {checkbox} {title}{suffix}"

    @staticmethod
    def _update_task_lines(content: str, tasks: list[dict]) -> str:
        """Update checkbox states in existing content using marker matching."""
        # Build marker -> task map
        task_map: dict[str, dict] = {}
        for t in tasks:
            marker = t.get("marker") or t.get("file_marker")
            if marker:
                task_map[marker] = t

        if not task_map:
            return content

        lines = content.split("\n")
        for i, line in enumerate(lines):
            if MarkdownParser.is_task_line(line):
                marker = MarkdownParser.extract_task_marker(line)
                if marker and marker in task_map:
                    task = task_map[marker]
                    checkbox = "[x]" if task.get("checked") else "[ ]"
                    lines[i] = re.sub(
                        r"-\s*\[[xX ]\]", f"- {checkbox}", line, count=1
                    )
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # StorageProvider interface — delete
    # ------------------------------------------------------------------

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        self._validate_entity_type(entity_type)
        abs_path = self._resolve_path(entity_id)
        if abs_path.exists():
            abs_path.unlink()
            logger.info("Deleted %s: %s", entity_type, entity_id)
            return True
        return False

    # ------------------------------------------------------------------
    # StorageProvider interface — watch
    # ------------------------------------------------------------------

    def watch_for_changes(self) -> list[Change]:
        """
        Compare current file hashes against the last snapshot.

        On first call, builds the initial snapshot and returns an empty
        list (no baseline to diff against).  Subsequent calls return
        created / modified / deleted changes.
        """
        current: dict[str, str] = {}
        for watch_dir in self.watch_directories:
            dir_path = self.root_path / watch_dir
            if not dir_path.exists():
                continue
            for md_file in dir_path.rglob("*.md"):
                rel_id = self._relative_id(md_file)
                current[rel_id] = self._file_hash(md_file)

        if not self._snapshot_initialized:
            self._hash_snapshot = current
            self._snapshot_initialized = True
            return []

        changes: list[Change] = []

        # New or modified
        for rel_id, new_hash in current.items():
            old_hash = self._hash_snapshot.get(rel_id)
            if old_hash is None:
                changes.append(Change(
                    change_type=ChangeType.CREATED,
                    entity_type="project",
                    entity_id=rel_id,
                ))
            elif old_hash != new_hash:
                changes.append(Change(
                    change_type=ChangeType.MODIFIED,
                    entity_type="project",
                    entity_id=rel_id,
                ))

        # Deleted
        for rel_id in self._hash_snapshot:
            if rel_id not in current:
                changes.append(Change(
                    change_type=ChangeType.DELETED,
                    entity_type="project",
                    entity_id=rel_id,
                ))

        # Update snapshot
        self._hash_snapshot = current
        return changes
