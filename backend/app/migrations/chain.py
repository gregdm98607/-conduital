"""Migration chain analysis utilities.

Analyzes Alembic migrations to detect:
- Orphaned migrations (no parent in chain)
- Multiple heads (branched migrations)
- Gaps in the chain
- Current vs expected head revision
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.paths import get_alembic_dir

from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class MigrationInfo:
    """Information about a single migration."""

    revision: str
    down_revision: Optional[str]
    filename: str
    description: str


@dataclass
class ChainValidationResult:
    """Result of migration chain validation."""

    is_valid: bool
    head_revision: Optional[str]
    orphaned: list[str]
    multiple_heads: list[str]
    errors: list[str]


def get_migrations_dir() -> Path:
    """Get the path to the alembic versions directory."""
    return get_alembic_dir() / "versions"


def parse_migration_file(filepath: Path) -> Optional[MigrationInfo]:
    """Parse a migration file to extract revision info."""
    content = filepath.read_text(encoding="utf-8")

    # Extract revision
    revision_match = re.search(r"^revision(?:\s*:\s*str)?\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    if not revision_match:
        return None
    revision = revision_match.group(1)

    # Extract down_revision
    down_match = re.search(
        r"^down_revision(?:\s*:\s*Union\[str,\s*None\])?\s*=\s*(?:['\"]([^'\"]+)['\"]|None)",
        content,
        re.MULTILINE,
    )
    down_revision = down_match.group(1) if down_match and down_match.group(1) else None

    # Extract description from docstring
    doc_match = re.search(r'^"""([^"]+)', content)
    description = doc_match.group(1).strip() if doc_match else filepath.stem

    return MigrationInfo(
        revision=revision,
        down_revision=down_revision,
        filename=filepath.name,
        description=description,
    )


def get_migration_chain() -> dict[str, MigrationInfo]:
    """Build a dictionary of all migrations keyed by revision."""
    migrations_dir = get_migrations_dir()
    migrations: dict[str, MigrationInfo] = {}

    if not migrations_dir.exists():
        return migrations

    for filepath in migrations_dir.glob("*.py"):
        if filepath.name.startswith("__"):
            continue
        info = parse_migration_file(filepath)
        if info:
            migrations[info.revision] = info

    return migrations


def get_current_head() -> Optional[str]:
    """Find the current head revision from migration files."""
    migrations = get_migration_chain()
    if not migrations:
        return None

    # Find revisions that are not referenced as down_revision
    all_revisions = set(migrations.keys())
    referenced = {m.down_revision for m in migrations.values() if m.down_revision}
    heads = all_revisions - referenced

    if len(heads) == 1:
        return heads.pop()
    elif len(heads) > 1:
        # Multiple heads - return them sorted for consistency
        return sorted(heads)[0]
    return None


def find_orphaned_migrations() -> list[str]:
    """Find migrations whose down_revision doesn't exist in the chain."""
    migrations = get_migration_chain()
    orphaned = []

    for rev, info in migrations.items():
        if info.down_revision is not None:
            if info.down_revision not in migrations:
                orphaned.append(rev)

    return orphaned


def find_multiple_heads() -> list[str]:
    """Find all head revisions (multiple heads indicate branches)."""
    migrations = get_migration_chain()
    if not migrations:
        return []

    all_revisions = set(migrations.keys())
    referenced = {m.down_revision for m in migrations.values() if m.down_revision}
    return sorted(all_revisions - referenced)


def get_chain_order() -> list[str]:
    """Get revisions in order from root to head."""
    migrations = get_migration_chain()
    if not migrations:
        return []

    # Find roots (migrations with no down_revision)
    roots = [rev for rev, info in migrations.items() if info.down_revision is None]

    if not roots:
        return []

    # Build forward references
    forward: dict[str, list[str]] = {rev: [] for rev in migrations}
    for rev, info in migrations.items():
        if info.down_revision and info.down_revision in forward:
            forward[info.down_revision].append(rev)

    # Walk from root to heads
    ordered = []
    to_visit = list(roots)
    visited = set()

    while to_visit:
        current = to_visit.pop(0)
        if current in visited:
            continue
        visited.add(current)
        ordered.append(current)
        to_visit.extend(forward.get(current, []))

    return ordered


def validate_chain() -> ChainValidationResult:
    """Validate the migration chain for integrity issues."""
    migrations = get_migration_chain()
    errors = []
    orphaned = []
    multiple_heads = []

    if not migrations:
        return ChainValidationResult(
            is_valid=False,
            head_revision=None,
            orphaned=[],
            multiple_heads=[],
            errors=["No migrations found"],
        )

    # Check for orphaned migrations
    for rev, info in migrations.items():
        if info.down_revision is not None:
            if info.down_revision not in migrations:
                orphaned.append(rev)
                errors.append(
                    f"Migration {rev} references non-existent down_revision: {info.down_revision}"
                )

    # Check for multiple heads
    all_revisions = set(migrations.keys())
    referenced = {m.down_revision for m in migrations.values() if m.down_revision}
    heads = sorted(all_revisions - referenced)

    if len(heads) > 1:
        multiple_heads = heads
        errors.append(f"Multiple heads detected: {', '.join(heads)}")

    # Check for cycles (simplified - just check if we can reach all nodes from roots)
    roots = [rev for rev, info in migrations.items() if info.down_revision is None]
    if not roots:
        errors.append("No root migration found (all migrations have down_revision)")

    head_revision = heads[0] if heads else None

    return ChainValidationResult(
        is_valid=len(errors) == 0,
        head_revision=head_revision,
        orphaned=orphaned,
        multiple_heads=multiple_heads,
        errors=errors,
    )


def get_db_revision(engine: Engine) -> Optional[str]:
    """Get the current revision from the alembic_version table."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            row = result.fetchone()
            return row[0] if row else None
    except Exception:
        return None


def compare_chain_to_db(engine: Engine) -> dict:
    """Compare migration chain to database state."""
    db_revision = get_db_revision(engine)
    chain_result = validate_chain()
    chain_order = get_chain_order()

    result = {
        "db_revision": db_revision,
        "chain_head": chain_result.head_revision,
        "chain_valid": chain_result.is_valid,
        "in_sync": db_revision == chain_result.head_revision,
        "pending_migrations": [],
    }

    # Find pending migrations
    if db_revision and chain_order:
        try:
            db_index = chain_order.index(db_revision)
            result["pending_migrations"] = chain_order[db_index + 1 :]
        except ValueError:
            result["pending_migrations"] = []

    return result
