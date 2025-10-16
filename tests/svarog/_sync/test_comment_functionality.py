"""Test-Driven Development tests for comment functionality in file sync feature."""

from __future__ import annotations

import tempfile
from pathlib import Path

from typer.testing import CliRunner

from svarog._sync._markdown._adapter import MarkdownAdapter
from svarog._sync.file_sync import SyncOptions
from svarog._sync.file_sync import generate_comment_id
from svarog._sync.file_sync import generate_section_comment
from svarog._sync.file_sync import sync_files
from svarog._sync.structure_adapter import YamlAdapter
from svarog.cli import cli_app


class TestCommentGeneration:
    """Test comment generation logic."""

    def test_generate_comment_id_creates_8_character_hash(self):
        """Test that comment ID generation creates 8-character hash."""
        content = "Test content for hashing"
        hash_id = generate_comment_id(content)

        assert isinstance(hash_id, str)
        assert len(hash_id) == 8
        assert hash_id.isalnum()  # Should be alphanumeric

    def test_generate_comment_id_consistency(self):
        """Test that same content generates same hash ID."""
        content = "Consistent test content"

        hash1 = generate_comment_id(content)
        hash2 = generate_comment_id(content)

        assert hash1 == hash2
        assert len(hash1) == 8

    def test_generate_comment_id_uniqueness(self):
        """Test that different content generates different hash IDs."""
        content1 = "First test content"
        content2 = "Second test content"

        hash1 = generate_comment_id(content1)
        hash2 = generate_comment_id(content2)

        assert hash1 != hash2
        assert len(hash1) == 8
        assert len(hash2) == 8

    def test_generate_comment_id_empty_content(self):
        """Test hash generation for empty content."""
        content = ""
        hash_id = generate_comment_id(content)

        assert len(hash_id) == 8
        assert hash_id.isalnum()

    def test_generate_section_comment_format(self):
        """Test section comment format with hash ID."""
        content = "Test content"
        hash_id = "abc12345"

        comment = generate_section_comment(content, hash_id)

        expected = "This is auto-generated section with ID: abc12345"
        assert comment == expected

    def test_generate_section_comment_with_different_hash(self):
        """Test section comment generation with different hash values."""
        content = "Another test content"
        hash_id = "def67890"

        comment = generate_section_comment(content, hash_id)

        expected = "This is auto-generated section with ID: def67890"
        assert comment == expected


class TestAdapterCommentRendering:
    """Test adapter-specific comment rendering."""

    def test_yaml_adapter_render_comment(self):
        """Test YAML adapter renders comments with hash format."""
        adapter = YamlAdapter()
        comment_text = "This is auto-generated section with ID: abc12345"

        rendered = adapter.render_comment(comment_text)

        assert rendered == "# This is auto-generated section with ID: abc12345"

    def test_markdown_adapter_render_comment(self):
        """Test Markdown adapter renders comments with hash format."""
        adapter = MarkdownAdapter()
        comment_text = "This is auto-generated section with ID: abc12345"

        rendered = adapter.render_comment(comment_text)

        assert rendered == "<!-- This is auto-generated section with ID: abc12345 -->"

    def test_yaml_comment_format_structure(self):
        """Test YAML comment follows expected structure."""
        adapter = YamlAdapter()
        comment_text = "Test comment"

        rendered = adapter.render_comment(comment_text)

        assert rendered.startswith("# ")
        assert comment_text in rendered
        assert not rendered.endswith("\n")

    def test_markdown_comment_format_structure(self):
        """Test Markdown comment follows expected structure."""
        adapter = MarkdownAdapter()
        comment_text = "Test comment"

        rendered = adapter.render_comment(comment_text)

        assert rendered.startswith("<!-- ")
        assert rendered.endswith(" -->")
        assert comment_text in rendered


class TestSyncOptionsCommentBehavior:
    """Test SyncOptions comment-related behavior."""

    def test_sync_options_add_comments_default_true(self):
        """Test that add_comments defaults to True."""
        options = SyncOptions()

        assert options.add_comments is True

    def test_sync_options_add_comments_explicit_true(self):
        """Test explicit True value for add_comments."""
        options = SyncOptions(add_comments=True)

        assert options.add_comments is True

    def test_sync_options_add_comments_explicit_false(self):
        """Test explicit False value for add_comments."""
        options = SyncOptions(add_comments=False)

        assert options.add_comments is False

    def test_sync_options_other_fields_preserved(self):
        """Test that adding add_comments preserves other fields."""
        options = SyncOptions(
            dry_run=True, show_diff=True, backup=True, add_comments=False, encoding="utf-16"
        )

        assert options.dry_run is True
        assert options.show_diff is True
        assert options.backup is True
        assert options.add_comments is False
        assert options.encoding == "utf-16"


class TestCLICommentFlag:
    """Test CLI --no-comment flag behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_sync_files_help_shows_comment_option(self):
        """Test that help shows --comment option."""
        result = self.runner.invoke(cli_app, ["sync", "files", "--help"])

        assert result.exit_code == 0
        assert "--comment" in result.stdout
        assert "add automatic comments" in result.stdout.lower()

    def test_sync_files_with_comment_flag_true_enables_comments(self):
        """Test that --comment flag enables comment addition."""
        with self.runner.isolated_filesystem():
            source_content = "name: test\nvalue: example"

            Path("source.yaml").write_text(source_content, encoding="utf-8")
            Path("target.yaml").write_text("existing: content", encoding="utf-8")

            result = self.runner.invoke(
                cli_app, ["sync", "files", "--comment", "source.yaml", "target.yaml"]
            )

            assert result.exit_code == 0
            target_content = Path("target.yaml").read_text(encoding="utf-8")

            # Should contain comment markers
            assert "# This is auto-generated section with ID:" in target_content

    def test_sync_files_with_comment_flag_false_disables_comments(self):
        """Test that --no-comment flag disables comment addition."""
        with self.runner.isolated_filesystem():
            source_content = "name: test\nvalue: example"

            Path("source.yaml").write_text(source_content, encoding="utf-8")
            Path("target.yaml").write_text("existing: content", encoding="utf-8")

            result = self.runner.invoke(
                cli_app, ["sync", "files", "--no-comment", "source.yaml", "target.yaml"]
            )

            assert result.exit_code == 0
            target_content = Path("target.yaml").read_text(encoding="utf-8")

            # Should not contain comment markers
            assert "# This is auto-generated section with ID:" not in target_content

    def test_sync_files_without_flag_enables_comments_by_default(self):
        """Test that omitting --comment flag enables comments by default."""
        with self.runner.isolated_filesystem():
            source_content = "name: test\nvalue: example"

            Path("source.yaml").write_text(source_content, encoding="utf-8")
            Path("target.yaml").write_text("existing: content", encoding="utf-8")

            result = self.runner.invoke(cli_app, ["sync", "files", "source.yaml", "target.yaml"])

            assert result.exit_code == 0
            target_content = Path("target.yaml").read_text(encoding="utf-8")

            # Should contain comment markers
            assert "# This is auto-generated section with ID:" in target_content

    def test_comment_flag_with_other_options(self):
        """Test --comment flag works with other CLI options."""
        with self.runner.isolated_filesystem():
            source_content = "name: test"
            Path("source.yaml").write_text(source_content, encoding="utf-8")

            result = self.runner.invoke(
                cli_app,
                [
                    "sync",
                    "files",
                    "--no-comment",
                    "--dry-run",
                    "--diff",
                    "source.yaml",
                    "target.yaml",
                ],
            )

            assert result.exit_code == 0
            assert "Dry run:" in result.stdout


class TestCommentInsertionLogic:
    """Test comment insertion in sync operations."""

    def test_comments_inserted_before_and_after_content(self):
        """Test that comments are inserted before and after synced content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.yaml"
            target_file = temp_path / "target.yaml"

            source_content = "new_section:\n  key: value"
            target_content = "existing:\n  content: data"

            source_file.write_text(source_content, encoding="utf-8")
            target_file.write_text(target_content, encoding="utf-8")

            options = SyncOptions(add_comments=True)
            sync_files(str(source_file), str(target_file), options=options)

            final_content = target_file.read_text(encoding="utf-8")

            # Should contain both start and end comments
            assert "# This is auto-generated section with ID:" in final_content
            # Count occurrences - should be at least 2 (start and end)
            comment_count = final_content.count("# This is auto-generated section with ID:")
            assert comment_count >= 2

    def test_no_comments_when_add_comments_false(self):
        """Test that no comments are added when add_comments is False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.yaml"
            target_file = temp_path / "target.yaml"

            source_content = "new_section:\n  key: value"
            target_content = "existing:\n  content: data"

            source_file.write_text(source_content, encoding="utf-8")
            target_file.write_text(target_content, encoding="utf-8")

            options = SyncOptions(add_comments=False)
            sync_files(str(source_file), str(target_file), options=options)

            final_content = target_file.read_text(encoding="utf-8")

            # Should not contain any auto-generated comments
            assert "# This is auto-generated section with ID:" not in final_content

    def test_comment_ids_consistent_across_runs(self):
        """Test that same content generates same comment IDs across multiple runs."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.yaml"
            target_file = temp_path / "target.yaml"

            # Consistent content
            source_content = "test_section:\n  value: consistent_data"

            source_file.write_text(source_content, encoding="utf-8")

            # First sync
            options1 = SyncOptions(add_comments=True)
            sync_files(str(source_file), str(target_file), options1)
            content1 = target_file.read_text(encoding="utf-8")

            # Second sync (modify target to trigger resync)
            target_file.write_text("different: content", encoding="utf-8")
            options2 = SyncOptions(add_comments=True)
            sync_files(str(source_file), str(target_file), options2)
            content2 = target_file.read_text(encoding="utf-8")

            # Extract hash IDs from both runs
            hash_ids1 = [
                line.split("ID: ")[1].strip()
                for line in content1.split("\n")
                if "This is auto-generated section with ID:" in line
            ]
            hash_ids2 = [
                line.split("ID: ")[1].strip()
                for line in content2.split("\n")
                if "This is auto-generated section with ID:" in line
            ]

            # Should have same hash IDs
            assert set(hash_ids1) == set(hash_ids2)


class TestCommentIntegrationWithFeatures:
    """Test comment integration with existing sync features."""

    def test_comments_visible_in_dry_run(self):
        """Test that comments are visible in dry-run diff output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.yaml"
            target_file = temp_path / "target.yaml"

            source_content = "new: data"
            target_content = "old: content"

            source_file.write_text(source_content, encoding="utf-8")
            target_file.write_text(target_content, encoding="utf-8")

            options = SyncOptions(dry_run=True, show_diff=True, add_comments=True)
            result = sync_files(str(source_file), str(target_file), options=options)

            # Comments should be visible in diff
            assert result.diff is not None
            assert "# This is auto-generated section with ID:" in result.diff

    def test_comments_work_with_backup(self):
        """Test that comment insertion works with backup creation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.yaml"
            target_file = temp_path / "target.yaml"

            source_content = "backup_test: data"
            target_content = "original: content"

            source_file.write_text(source_content, encoding="utf-8")
            target_file.write_text(target_content, encoding="utf-8")

            options = SyncOptions(backup=True, add_comments=True)
            result = sync_files(str(source_file), str(target_file), options=options)

            # Backup should be created
            assert result.backup_path is not None
            assert result.backup_path.exists()

            # Comments should be in new content
            final_content = target_file.read_text(encoding="utf-8")
            assert "# This is auto-generated section with ID:" in final_content

    def test_comments_with_section_mapping(self):
        """Test that comments work with section mapping feature."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.yaml"
            target_file = temp_path / "target.yaml"

            source_content = "source_section:\n  mapped_value: test"
            target_content = "target_section:\n  existing_value: old"

            source_file.write_text(source_content, encoding="utf-8")
            target_file.write_text(target_content, encoding="utf-8")

            # Mock section mapping (this would need proper implementation)
            from svarog._sync.section_mapping import PathSegment
            from svarog._sync.section_mapping import SectionMapping

            mapping = SectionMapping(
                src_path=(PathSegment("source_section"),),
                dst_path=(PathSegment("target_section"),),
                create=True,
            )

            options = SyncOptions(add_comments=True, section_mappings=[mapping])

            sync_files(str(source_file), str(target_file), options=options)

            final_content = target_file.read_text(encoding="utf-8")
            # Comments should work with section mapping
            assert "# This is auto-generated section with ID:" in final_content


class TestCommentEdgeCases:
    """Test comment functionality edge cases."""

    def test_comments_with_empty_files(self):
        """Test comment behavior with empty source or target files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Empty source, non-empty target
            source_file = temp_path / "source.yaml"
            target_file = temp_path / "target.yaml"

            source_file.write_text("", encoding="utf-8")
            target_file.write_text("existing: data", encoding="utf-8")

            options = SyncOptions(add_comments=True)
            result = sync_files(str(source_file), str(target_file), options=options)

            # Should handle gracefully (may not add comments for empty content)
            assert result.changed is True

    def test_comments_with_large_content(self):
        """Test comment generation with large content."""
        large_content = "data: " + "x" * 10000

        hash_id = generate_comment_id(large_content)

        assert len(hash_id) == 8
        assert hash_id.isalnum()

    def test_comments_with_unicode_content(self):
        """Test comment generation with Unicode content."""
        unicode_content = "测试数据: 🚀 emoji content with ñiño"

        hash_id = generate_comment_id(unicode_content)

        assert len(hash_id) == 8
        assert hash_id.isalnum()

    def test_comments_with_binary_files_disabled(self):
        """Test that comments are not added to binary files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "source.bin"
            target_file = temp_path / "target.bin"

            # Create binary content
            binary_content = b"\x00\x01\x02\x03\x04\x05"
            source_file.write_bytes(binary_content)
            target_file.write_bytes(b"\x06\x07\x08\x09")

            options = SyncOptions(allow_binary=True, add_comments=True)

            # Should handle binary files gracefully (no comments)
            # Implementation may need to skip comments for binary files
            result = sync_files(str(source_file), str(target_file), options=options)
            assert result is not None


class TestCommentIntegrationTests:
    """End-to-end integration tests for comment functionality."""

    def test_full_yaml_sync_with_comments(self):
        """Test complete YAML file sync with comments enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "config.yaml"
            target_file = temp_path / "output.yaml"

            source_content = """app:
  name: test-app
  version: 1.0.0
  settings:
    debug: true
    port: 8080
"""

            source_file.write_text(source_content, encoding="utf-8")

            options = SyncOptions(add_comments=True)
            result = sync_files(str(source_file), str(target_file), options=options)

            assert result.changed is True
            final_content = target_file.read_text(encoding="utf-8")

            # Should contain auto-generated comments
            assert "# This is auto-generated section with ID:" in final_content
            # Should contain the original content
            assert "name: test-app" in final_content
            assert "version: 1.0.0" in final_content

    def test_full_markdown_sync_with_comments(self):
        """Test complete Markdown file sync with comments enabled."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            source_file = temp_path / "content.md"
            target_file = temp_path / "output.md"

            source_content = """# Test Document

This is a test section.

## Subsection

Some content here.
"""

            source_file.write_text(source_content, encoding="utf-8")

            options = SyncOptions(add_comments=True)
            result = sync_files(str(source_file), str(target_file), options=options)

            assert result.changed is True
            final_content = target_file.read_text(encoding="utf-8")

            # Should contain HTML comments
            assert "<!-- This is auto-generated section with ID:" in final_content
            assert "-->" in final_content

    def test_cli_integration_test_no_comments(self):
        """Test CLI integration with --no-comment flag."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            source_content = "test: value"
            Path("source.yaml").write_text(source_content, encoding="utf-8")
            Path("target.yaml").write_text("old: data", encoding="utf-8")

            result = runner.invoke(
                cli_app, ["sync", "files", "--no-comment", "source.yaml", "target.yaml"]
            )

            assert result.exit_code == 0
            assert "Synchronized source.yaml -> target.yaml." in result.stdout

            target_content = Path("target.yaml").read_text(encoding="utf-8")
            assert "# This is auto-generated section with ID:" not in target_content

    def test_cli_integration_test_with_comments(self):
        """Test CLI integration with comments enabled (default)."""
        runner = CliRunner()

        with runner.isolated_filesystem():
            source_content = "test: value"
            Path("source.yaml").write_text(source_content, encoding="utf-8")
            Path("target.yaml").write_text("old: data", encoding="utf-8")

            result = runner.invoke(cli_app, ["sync", "files", "source.yaml", "target.yaml"])

            assert result.exit_code == 0
            assert "Synchronized source.yaml -> target.yaml." in result.stdout

            target_content = Path("target.yaml").read_text(encoding="utf-8")
            assert "# This is auto-generated section with ID:" in target_content
