"""
Markdown parsers and writers for all entity types beyond projects/tasks.

Each entity uses YAML frontmatter for metadata and the markdown body
for rich content (notes, descriptions, standards of excellence, etc.).

Round-trip guarantee: parse(write(data)) == data  (for all supported fields).
"""

from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

import frontmatter

from app.sync.markdown_parser import MarkdownParser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iso_date(value: Any) -> Optional[str]:
    """Serialize a date/datetime to ISO string, or return str as-is."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _parse_date(value: Any) -> Optional[date]:
    """Parse a date from string or date/datetime."""
    return MarkdownParser.parse_date(value)


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse a datetime from string or datetime."""
    return MarkdownParser.parse_datetime(value)


def _sanitize_filename(title: str) -> str:
    """Sanitize a title for use as a filename slug."""
    import re
    invalid_chars = '<>:"/\\|?*'
    safe = title
    for ch in invalid_chars:
        safe = safe.replace(ch, "")
    safe = re.sub(r"[\s]+", "-", safe).strip("-").lower()[:100]
    return safe


def _write_frontmatter_file(file_path: Path, metadata: dict, body: str) -> None:
    """Write a markdown file with YAML frontmatter."""
    post = frontmatter.Post(body, **metadata)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        f.write(frontmatter.dumps(post))


def _read_frontmatter_file(file_path: Path) -> dict:
    """Read a markdown file, returning metadata dict and body string."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        post = frontmatter.load(f)
    return {"metadata": dict(post.metadata), "content": post.content}


# ===================================================================
# AREA OF RESPONSIBILITY
# ===================================================================

class AreaMarkdown:
    """
    Markdown format for Areas of Responsibility.

    Frontmatter: title, health_score, review_frequency, is_archived,
                 last_reviewed_at, folder_path
    Body: description + standard_of_excellence sections
    """

    ENTITY_TYPE = "area"
    DIRECTORY = "areas"

    @staticmethod
    def parse(file_path: Path) -> dict:
        raw = _read_frontmatter_file(file_path)
        meta = raw["metadata"]
        body = raw["content"]

        # Parse body sections
        description, standard = AreaMarkdown._split_body(body)

        return {
            "metadata": meta,
            "content": body,
            "entity_type": "area",
            "title": meta.get("title", ""),
            "description": description,
            "standard_of_excellence": standard,
            "health_score": float(meta.get("health_score", 0.0)),
            "review_frequency": meta.get("review_frequency", "weekly"),
            "is_archived": bool(meta.get("is_archived", False)),
            "last_reviewed_at": _parse_datetime(meta.get("last_reviewed_at")),
            "folder_path": meta.get("folder_path"),
            "file_path": str(file_path),
        }

    @staticmethod
    def _split_body(body: str) -> tuple[str, Optional[str]]:
        """Split body into description and standard_of_excellence."""
        parts = body.split("## Standard of Excellence")
        description = parts[0].strip()
        standard = parts[1].strip() if len(parts) > 1 else None
        return description, standard

    @staticmethod
    def write(data: dict, file_path: Path) -> None:
        meta = {
            "title": data.get("title", "Untitled Area"),
            "health_score": float(data.get("health_score", 0.0)),
            "review_frequency": data.get("review_frequency", "weekly"),
            "is_archived": bool(data.get("is_archived", False)),
        }
        if data.get("last_reviewed_at"):
            meta["last_reviewed_at"] = _iso_date(data["last_reviewed_at"])
        if data.get("folder_path"):
            meta["folder_path"] = data["folder_path"]

        # Build body
        lines = []
        desc = data.get("description", "")
        if desc:
            lines.append(desc)

        soe = data.get("standard_of_excellence")
        if soe:
            if lines:
                lines.append("")
            lines.append("## Standard of Excellence")
            lines.append("")
            lines.append(soe)

        body = "\n".join(lines)
        _write_frontmatter_file(file_path, meta, body)

    @staticmethod
    def make_filename(data: dict) -> str:
        title = data.get("title", "untitled")
        return f"{_sanitize_filename(title)}.md"


# ===================================================================
# GOAL
# ===================================================================

class GoalMarkdown:
    """
    Markdown format for Goals.

    Frontmatter: title, status, timeframe, target_date, completed_at
    Body: description
    """

    ENTITY_TYPE = "goal"
    DIRECTORY = "goals"

    @staticmethod
    def parse(file_path: Path) -> dict:
        raw = _read_frontmatter_file(file_path)
        meta = raw["metadata"]
        body = raw["content"]

        return {
            "metadata": meta,
            "content": body,
            "entity_type": "goal",
            "title": meta.get("title", ""),
            "description": body.strip() or None,
            "timeframe": meta.get("timeframe"),
            "target_date": _parse_date(meta.get("target_date")),
            "status": meta.get("status", "active"),
            "completed_at": _parse_datetime(meta.get("completed_at")),
            "file_path": str(file_path),
        }

    @staticmethod
    def write(data: dict, file_path: Path) -> None:
        meta = {
            "title": data.get("title", "Untitled Goal"),
            "status": data.get("status", "active"),
        }
        if data.get("timeframe"):
            meta["timeframe"] = data["timeframe"]
        if data.get("target_date"):
            meta["target_date"] = _iso_date(data["target_date"])
        if data.get("completed_at"):
            meta["completed_at"] = _iso_date(data["completed_at"])

        body = data.get("description", "") or ""
        _write_frontmatter_file(file_path, meta, body)

    @staticmethod
    def make_filename(data: dict) -> str:
        title = data.get("title", "untitled")
        return f"{_sanitize_filename(title)}.md"


# ===================================================================
# VISION
# ===================================================================

class VisionMarkdown:
    """
    Markdown format for Visions.

    Frontmatter: title, timeframe
    Body: description (long-form vision statement)
    """

    ENTITY_TYPE = "vision"
    DIRECTORY = "visions"

    @staticmethod
    def parse(file_path: Path) -> dict:
        raw = _read_frontmatter_file(file_path)
        meta = raw["metadata"]
        body = raw["content"]

        return {
            "metadata": meta,
            "content": body,
            "entity_type": "vision",
            "title": meta.get("title", ""),
            "description": body.strip() or None,
            "timeframe": meta.get("timeframe"),
            "file_path": str(file_path),
        }

    @staticmethod
    def write(data: dict, file_path: Path) -> None:
        meta = {
            "title": data.get("title", "Untitled Vision"),
        }
        if data.get("timeframe"):
            meta["timeframe"] = data["timeframe"]

        body = data.get("description", "") or ""
        _write_frontmatter_file(file_path, meta, body)

    @staticmethod
    def make_filename(data: dict) -> str:
        title = data.get("title", "untitled")
        return f"{_sanitize_filename(title)}.md"


# ===================================================================
# INBOX ITEM
# ===================================================================

class InboxMarkdown:
    """
    Markdown format for Inbox Items.

    Frontmatter: captured_at, source, processed_at, result_type, result_id
    Body: content (the captured text)
    """

    ENTITY_TYPE = "inbox"
    DIRECTORY = "inbox"

    @staticmethod
    def parse(file_path: Path) -> dict:
        raw = _read_frontmatter_file(file_path)
        meta = raw["metadata"]
        body = raw["content"]

        return {
            "metadata": meta,
            "content": body,
            "entity_type": "inbox",
            "captured_at": _parse_datetime(meta.get("captured_at")),
            "source": meta.get("source", "web_ui"),
            "processed_at": _parse_datetime(meta.get("processed_at")),
            "result_type": meta.get("result_type"),
            "result_id": meta.get("result_id"),
            "body_content": body.strip(),
            "file_path": str(file_path),
        }

    @staticmethod
    def write(data: dict, file_path: Path) -> None:
        meta = {
            "captured_at": _iso_date(data.get("captured_at", datetime.now(timezone.utc))),
            "source": data.get("source", "web_ui"),
        }
        if data.get("processed_at"):
            meta["processed_at"] = _iso_date(data["processed_at"])
        if data.get("result_type"):
            meta["result_type"] = data["result_type"]
        if data.get("result_id") is not None:
            meta["result_id"] = data["result_id"]

        body = data.get("body_content", "") or data.get("content", "") or ""
        _write_frontmatter_file(file_path, meta, body)

    @staticmethod
    def make_filename(data: dict) -> str:
        captured = data.get("captured_at")
        if isinstance(captured, (date, datetime)):
            date_str = captured.strftime("%Y-%m-%d")
        elif isinstance(captured, str):
            date_str = captured[:10]
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Use first few words of content for readability
        content = data.get("body_content", "") or data.get("content", "") or "item"
        slug = _sanitize_filename(content[:50])
        return f"{date_str}-{slug}.md"


# ===================================================================
# CONTEXT
# ===================================================================

class ContextMarkdown:
    """
    Markdown format for Contexts.

    Frontmatter: name, context_type, icon
    Body: description
    """

    ENTITY_TYPE = "context"
    DIRECTORY = "contexts"

    @staticmethod
    def parse(file_path: Path) -> dict:
        raw = _read_frontmatter_file(file_path)
        meta = raw["metadata"]
        body = raw["content"]

        return {
            "metadata": meta,
            "content": body,
            "entity_type": "context",
            "name": meta.get("name", ""),
            "context_type": meta.get("context_type"),
            "description": body.strip() or None,
            "icon": meta.get("icon"),
            "file_path": str(file_path),
        }

    @staticmethod
    def write(data: dict, file_path: Path) -> None:
        meta = {
            "name": data.get("name", "unnamed"),
        }
        if data.get("context_type"):
            meta["context_type"] = data["context_type"]
        if data.get("icon"):
            meta["icon"] = data["icon"]

        body = data.get("description", "") or ""
        _write_frontmatter_file(file_path, meta, body)

    @staticmethod
    def make_filename(data: dict) -> str:
        name = data.get("name", "unnamed")
        return f"{_sanitize_filename(name)}.md"


# ===================================================================
# WEEKLY REVIEW COMPLETION
# ===================================================================

class WeeklyReviewMarkdown:
    """
    Markdown format for Weekly Review Completions.

    Frontmatter: completed_at
    Body: notes + AI summary sections
    """

    ENTITY_TYPE = "weekly_review"
    DIRECTORY = "weekly-reviews"

    @staticmethod
    def parse(file_path: Path) -> dict:
        raw = _read_frontmatter_file(file_path)
        meta = raw["metadata"]
        body = raw["content"]

        notes, ai_summary = WeeklyReviewMarkdown._split_body(body)

        return {
            "metadata": meta,
            "content": body,
            "entity_type": "weekly_review",
            "completed_at": _parse_datetime(meta.get("completed_at")),
            "notes": notes,
            "ai_summary": ai_summary,
            "file_path": str(file_path),
        }

    @staticmethod
    def _split_body(body: str) -> tuple[Optional[str], Optional[str]]:
        """Split body into notes and AI summary."""
        parts = body.split("## AI Summary")
        notes = parts[0].strip() or None
        ai_summary = parts[1].strip() if len(parts) > 1 else None
        return notes, ai_summary

    @staticmethod
    def write(data: dict, file_path: Path) -> None:
        completed = data.get("completed_at", datetime.now(timezone.utc))
        meta = {
            "completed_at": _iso_date(completed),
        }

        lines = []
        notes = data.get("notes")
        if notes:
            lines.append(notes)

        ai_summary = data.get("ai_summary")
        if ai_summary:
            if lines:
                lines.append("")
            lines.append("## AI Summary")
            lines.append("")
            lines.append(ai_summary)

        body = "\n".join(lines)
        _write_frontmatter_file(file_path, meta, body)

    @staticmethod
    def make_filename(data: dict) -> str:
        completed = data.get("completed_at")
        if isinstance(completed, (date, datetime)):
            date_str = completed.strftime("%Y-%m-%d")
        elif isinstance(completed, str):
            date_str = completed[:10]
        else:
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{date_str}-weekly-review.md"


# ===================================================================
# Registry: maps entity_type strings to handler classes
# ===================================================================

ENTITY_HANDLERS = {
    "area": AreaMarkdown,
    "goal": GoalMarkdown,
    "vision": VisionMarkdown,
    "inbox": InboxMarkdown,
    "context": ContextMarkdown,
    "weekly_review": WeeklyReviewMarkdown,
}
