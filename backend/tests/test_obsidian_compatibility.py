"""
Phase 5 — Obsidian compatibility tests.

Ensures that:
- Markdown files render correctly in Obsidian (valid frontmatter + markdown)
- Obsidian edits (adding/removing frontmatter fields) don't break parsing
- Wikilinks, callouts, and other Obsidian-specific syntax in body content
  are preserved through read/write cycles
"""

import textwrap
from pathlib import Path

import pytest

from app.storage.local_folder import LocalFolderProvider
from app.sync.entity_markdown import AreaMarkdown, GoalMarkdown


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def storage_root(tmp_path: Path) -> Path:
    (tmp_path / "10_Projects").mkdir()
    (tmp_path / "areas").mkdir()
    (tmp_path / "goals").mkdir()
    return tmp_path


@pytest.fixture()
def provider(storage_root: Path) -> LocalFolderProvider:
    return LocalFolderProvider(
        root_path=storage_root,
        watch_directories=["10_Projects"],
    )


# ---------------------------------------------------------------------------
# 1. Valid Obsidian markdown format
# ---------------------------------------------------------------------------


class TestObsidianMarkdownFormat:
    """Verify output files use valid Obsidian-compatible frontmatter + markdown."""

    def test_frontmatter_uses_triple_dash_delimiters(self, provider, storage_root):
        """Obsidian requires --- delimiters for YAML frontmatter."""
        entity_id = "10_Projects/FrontmatterTest.md"
        provider.write_entity("project", entity_id, {
            "title": "Frontmatter Test",
            "status": "active",
            "priority": 3,
            "momentum_score": 0.5,
        })
        content = (storage_root / entity_id).read_text(encoding="utf-8")
        assert content.startswith("---\n")
        # Should have exactly two --- delimiters
        assert content.count("\n---\n") >= 1 or content.startswith("---\n")

    def test_frontmatter_values_are_valid_yaml(self, provider, storage_root):
        """Frontmatter should be parseable by any YAML parser (Obsidian uses its own)."""
        import yaml

        entity_id = "10_Projects/YamlTest.md"
        provider.write_entity("project", entity_id, {
            "title": "YAML Validity",
            "status": "active",
            "priority": 1,
            "momentum_score": 0.99,
        })
        content = (storage_root / entity_id).read_text(encoding="utf-8")

        # Extract frontmatter between --- delimiters
        parts = content.split("---")
        assert len(parts) >= 3, "Expected at least two --- delimiters"
        yaml_str = parts[1]
        parsed = yaml.safe_load(yaml_str)
        assert isinstance(parsed, dict)

    def test_body_uses_standard_markdown_headings(self, provider, storage_root):
        """Body should use # headings, not Obsidian-specific formatting."""
        entity_id = "10_Projects/HeadingTest.md"
        provider.write_entity("project", entity_id, {
            "title": "Heading Test",
            "description": "A project.",
            "status": "active",
            "priority": 1,
            "momentum_score": 0.0,
            "tasks": [
                {"title": "Do thing", "checked": False, "marker": "tracker:task:h1"},
            ],
        })
        content = (storage_root / entity_id).read_text(encoding="utf-8")
        assert "# Heading Test" in content
        assert "## Next Actions" in content


# ---------------------------------------------------------------------------
# 2. Obsidian edits don't break parsing
# ---------------------------------------------------------------------------


class TestObsidianEditsPreserved:
    """Simulate Obsidian user adding/removing frontmatter fields."""

    def test_extra_frontmatter_fields_ignored(self, provider, storage_root):
        """
        Obsidian users may add custom frontmatter fields (tags, aliases, cssclass).
        These should survive parsing without causing errors.
        """
        entity_id = "10_Projects/ExtraFields.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 2
            tags:
              - productivity
              - obsidian
            aliases:
              - My Cool Project
            cssclass: wide-page
            custom_field: some_value
            ---
            # Extra Fields Project

            Content here.
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert result["metadata"]["project_status"] == "active"
        assert result["metadata"]["priority"] == 2
        # Extra fields should be in metadata dict
        assert result["metadata"]["tags"] == ["productivity", "obsidian"]
        assert result["metadata"]["cssclass"] == "wide-page"

    def test_obsidian_removes_conduital_field(self, provider, storage_root):
        """
        If an Obsidian user accidentally removes a Conduital field
        (e.g. momentum_score), parsing should still work with defaults.
        """
        entity_id = "10_Projects/MissingField.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            ---
            # Missing Priority

            No priority or momentum_score in frontmatter.
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert result["metadata"]["project_status"] == "active"
        # Missing fields should not crash — they just won't be in metadata
        assert "priority" not in result["metadata"] or result["metadata"].get("priority") is None

    def test_obsidian_changes_status_value(self, provider, storage_root):
        """Obsidian user manually changes project_status in frontmatter."""
        entity_id = "10_Projects/StatusEdit.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 3
            momentum_score: 0.7
            ---
            # Status Edit

            - [ ] Task A <!-- tracker:task:se1 -->
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        # Obsidian user edits the status
        content = (storage_root / entity_id).read_text(encoding="utf-8")
        content = content.replace("project_status: active", "project_status: someday_maybe")
        (storage_root / entity_id).write_text(content, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert result["metadata"]["project_status"] == "someday_maybe"


# ---------------------------------------------------------------------------
# 3. Obsidian-specific syntax in body content
# ---------------------------------------------------------------------------


class TestObsidianSyntaxPreserved:
    """Obsidian wikilinks, callouts, and embeds in body should survive round-trips."""

    def test_wikilinks_preserved(self, provider, storage_root):
        """[[wikilinks]] in body should survive write → read → write."""
        entity_id = "10_Projects/WikiLinks.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 1
            ---
            # Wiki Links Project

            This references [[Another Project]] and [[My Area/Health]].
            Also has a display-name link: [[Target Page|Display Name]].

            ## Next Actions

            - [ ] Check [[Reference Doc]] <!-- tracker:task:wl1 -->
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert "[[Another Project]]" in result["content"]
        assert "[[Target Page|Display Name]]" in result["content"]
        assert "[[Reference Doc]]" in result["tasks"][0]["title"] or \
               "Reference Doc" in result["tasks"][0]["title"]

    def test_callouts_preserved(self, provider, storage_root):
        """Obsidian callouts (> [!note]) should survive parsing."""
        entity_id = "10_Projects/Callouts.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 2
            ---
            # Callout Project

            > [!note] Important Note
            > This is an Obsidian callout block.

            > [!warning] Deadline
            > Project deadline is approaching.

            ## Next Actions

            - [ ] Review callouts <!-- tracker:task:co1 -->
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert "[!note]" in result["content"]
        assert "[!warning]" in result["content"]

    def test_obsidian_embeds_preserved(self, provider, storage_root):
        """![[embeds]] should survive parsing."""
        entity_id = "10_Projects/Embeds.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 1
            ---
            # Embeds Project

            ![[screenshot.png]]
            ![[Another Document#Section]]

            ## Next Actions

            - [ ] Check embed <!-- tracker:task:em1 -->
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert "![[screenshot.png]]" in result["content"]
        assert "![[Another Document#Section]]" in result["content"]

    def test_dataview_queries_preserved(self, provider, storage_root):
        """Obsidian Dataview inline queries should survive."""
        entity_id = "10_Projects/Dataview.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 1
            ---
            # Dataview Project

            ```dataview
            TABLE file.mtime as "Modified"
            FROM "10_Projects"
            SORT file.mtime DESC
            ```

            Inline: `= this.priority`
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        result = provider.read_entity("project", entity_id)
        assert "```dataview" in result["content"]
        assert "`= this.priority`" in result["content"]

    def test_metadata_update_preserves_obsidian_body(self, provider, storage_root):
        """
        When Conduital writes metadata updates, the Obsidian-specific
        body content (wikilinks, callouts, etc.) should be preserved.
        """
        entity_id = "10_Projects/PreserveBody.md"
        md = textwrap.dedent("""\
            ---
            project_status: active
            priority: 3
            momentum_score: 0.5
            ---
            # Preserve Body

            Links to [[Other Project]] and uses ![[embed.png]].

            > [!tip] Useful tip
            > Don't lose this content.

            ## Next Actions

            - [ ] Important task <!-- tracker:task:pb1 -->
        """)
        (storage_root / entity_id).write_text(md, encoding="utf-8")

        # Update only metadata via provider
        provider.write_entity("project", entity_id, {
            "status": "completed",
            "priority": 1,
            "momentum_score": 1.0,
        })

        # Read back and verify body is preserved
        result = provider.read_entity("project", entity_id)
        assert "[[Other Project]]" in result["content"]
        assert "![[embed.png]]" in result["content"]
        assert "[!tip]" in result["content"]
        assert result["metadata"]["project_status"] == "completed"
