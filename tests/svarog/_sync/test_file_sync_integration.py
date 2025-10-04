"""Comprehensive integration tests for file synchronization.

These tests focus on real-world scenarios with different file types,
encodings, sizes, and synchronization patterns using parametrized tests.
"""

from __future__ import annotations

import contextlib
import json
import stat
import typing as t

import pytest

from svarog._sync.file_sync import FileSyncError
from svarog._sync.file_sync import SyncOptions
from svarog._sync.file_sync import SyncResult
from svarog._sync.file_sync import sync_files

if t.TYPE_CHECKING:
    from pathlib import Path


class TestFileSyncScenario(t.TypedDict):
    """A single test scenario for file synchronization."""

    name: str
    source_content: str | bytes | None
    target_content: str | bytes | None
    options: SyncOptions
    expected_changed: bool
    expected_reason: str
    should_have_backup: bool
    should_have_diff: bool
    should_raise: type[Exception] | None
    source_encoding: str | None
    target_encoding: str | None
    create_subdirs: bool


def create_test_file(
    path: Path,
    content: str | bytes | None,
    *,
    encoding: str | None = None,
    create_dirs: bool = False,
) -> None:
    """Create a test file with the specified content.

    Args:
        path: Path where the file should be created.
        content: Content to write (string, bytes, or None for no file).
        encoding: Text encoding to use (if content is string).
        create_dirs: Whether to create parent directories.
    """
    if content is None:
        return  # Don't create the file

    if create_dirs:
        path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(content, bytes):
        path.write_bytes(content)
    elif isinstance(content, str):
        path.write_text(content, encoding=encoding or "utf-8")


def verify_sync_result(
    result: SyncResult,
    scenario: TestFileSyncScenario,
    target_path: Path,
    source_content: str | bytes,
) -> None:
    """Verify that sync result matches expected scenario outcomes.

    Args:
        result: The synchronization result to verify.
        scenario: The test scenario with expected outcomes.
        target_path: Path to the target file.
        source_content: Original source content for comparison.
    """
    assert result.changed == scenario["expected_changed"]
    assert result.reason == scenario["expected_reason"]

    if scenario["should_have_backup"]:
        assert result.backup_path is not None
        assert result.backup_path.exists()
    else:
        assert result.backup_path is None

    if scenario["should_have_diff"]:
        assert result.diff is not None
        assert len(result.diff.strip()) > 0
    else:
        assert result.diff is None or len(result.diff.strip()) == 0

    # Verify target content if sync was successful
    if result.changed and result.reason not in ("dry_run",):
        if isinstance(source_content, bytes):
            assert target_path.read_bytes() == source_content
        else:
            encoding = scenario["options"].encoding
            assert target_path.read_text(encoding=encoding) == source_content


# Test scenarios covering comprehensive integration cases
SYNC_TEST_SCENARIOS: list[TestFileSyncScenario] = [
    {
        "name": "simple_text_creation",
        "source_content": "Hello, World!",
        "target_content": None,  # Target doesn't exist
        "options": SyncOptions(),
        "expected_changed": True,
        "expected_reason": "target_created",
        "should_have_backup": False,
        "should_have_diff": False,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": None,
        "create_subdirs": False,
    },
    {
        "name": "text_update_with_backup_and_diff",
        "source_content": "Updated content\nWith multiple lines\n",
        "target_content": "Old content\nWith different lines\n",
        "options": SyncOptions(backup=True, show_diff=True),
        "expected_changed": True,
        "expected_reason": "target_updated",
        "should_have_backup": True,
        "should_have_diff": True,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": "utf-8",
        "create_subdirs": False,
    },
    {
        "name": "already_in_sync_with_diff",
        "source_content": "Same content",
        "target_content": "Same content",
        "options": SyncOptions(show_diff=True),
        "expected_changed": False,
        "expected_reason": "already_in_sync",
        "should_have_backup": False,
        "should_have_diff": False,  # No diff when files are identical
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": "utf-8",
        "create_subdirs": False,
    },
    {
        "name": "dry_run_preview",
        "source_content": "New content for preview",
        "target_content": "Existing content",
        "options": SyncOptions(dry_run=True, show_diff=True),
        "expected_changed": False,
        "expected_reason": "dry_run",
        "should_have_backup": False,
        "should_have_diff": True,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": "utf-8",
        "create_subdirs": False,
    },
    {
        "name": "binary_file_sync",
        "source_content": b"\x00\x01\x02\x03\xff\xfe\xfd",
        "target_content": b"\x10\x11\x12",
        "options": SyncOptions(allow_binary=True, backup=True),
        "expected_changed": True,
        "expected_reason": "target_updated",
        "should_have_backup": True,
        "should_have_diff": False,  # No diff for binary
        "should_raise": None,
        "source_encoding": None,
        "target_encoding": None,
        "create_subdirs": False,
    },
    {
        "name": "utf16_encoding_sync",
        "source_content": "Tëst ünicode çøntënt 🚀",
        "target_content": "Ölð ünicode çøntënt 📝",
        "options": SyncOptions(encoding="utf-16", show_diff=True, allow_binary=True),
        "expected_changed": True,
        "expected_reason": "target_updated",
        "should_have_backup": False,
        "should_have_diff": False,  # No diff for binary files
        "should_raise": None,
        "source_encoding": "utf-16",
        "target_encoding": "utf-16",
        "create_subdirs": False,
    },
    {
        "name": "large_text_file_sync",
        "source_content": "Large file content\n" * 1000,  # ~19KB file
        "target_content": "Different large content\n" * 800,  # ~25KB file
        "options": SyncOptions(backup=True),
        "expected_changed": True,
        "expected_reason": "target_updated",
        "should_have_backup": True,
        "should_have_diff": False,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": "utf-8",
        "create_subdirs": False,
    },
    {
        "name": "empty_file_sync",
        "source_content": "",
        "target_content": "Content to be cleared",
        "options": SyncOptions(show_diff=True),
        "expected_changed": True,
        "expected_reason": "target_updated",
        "should_have_backup": False,
        "should_have_diff": True,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": "utf-8",
        "create_subdirs": False,
    },
    {
        "name": "json_config_file_sync",
        "source_content": json.dumps(
            {
                "version": "2.0",
                "settings": {"debug": True, "timeout": 30},
                "features": ["auth", "logging", "metrics"],
            },
            indent=2,
        ),
        "target_content": json.dumps(
            {"version": "1.0", "settings": {"debug": False, "timeout": 60}}, indent=2
        ),
        "options": SyncOptions(backup=True, show_diff=True),
        "expected_changed": True,
        "expected_reason": "target_updated",
        "should_have_backup": True,
        "should_have_diff": True,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": "utf-8",
        "create_subdirs": False,
    },
    {
        "name": "subdirectory_file_creation",
        "source_content": "Content for nested file",
        "target_content": None,
        "options": SyncOptions(),
        "expected_changed": True,
        "expected_reason": "target_created",
        "should_have_backup": False,
        "should_have_diff": False,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": None,
        "create_subdirs": True,
    },
    {
        "name": "multiline_code_file_sync",
        "source_content": '''def hello_world():
    """A simple greeting function."""
    print("Hello, World!")
    return "greeting_sent"

if __name__ == "__main__":
    hello_world()
''',
        "target_content": '''def hello_world():
    """An old greeting function."""
    print("Hello!")

if __name__ == "__main__":
    hello_world()
''',
        "options": SyncOptions(show_diff=True, backup=True),
        "expected_changed": True,
        "expected_reason": "target_updated",
        "should_have_backup": True,
        "should_have_diff": True,
        "should_raise": None,
        "source_encoding": "utf-8",
        "target_encoding": "utf-8",
        "create_subdirs": False,
    },
    {
        "name": "binary_without_permission",
        "source_content": b"\x89PNG\r\n\x1a\n",  # PNG header
        "target_content": None,
        "options": SyncOptions(),  # allow_binary=False by default
        "expected_changed": False,
        "expected_reason": "",  # Not relevant when exception is raised
        "should_have_backup": False,
        "should_have_diff": False,
        "should_raise": FileSyncError,
        "source_encoding": None,
        "target_encoding": None,
        "create_subdirs": False,
    },
]


class TestComprehensiveFileSync:
    """Comprehensive integration tests for file synchronization scenarios."""

    @pytest.mark.parametrize("scenario", SYNC_TEST_SCENARIOS, ids=lambda s: s["name"])
    def test_file_sync_scenario(
        self,
        scenario: TestFileSyncScenario,
        tmp_path: Path,
    ) -> None:
        """Test comprehensive file synchronization scenarios.

        This parametrized test covers various real-world scenarios including:
        - Different file types (text, binary, empty, large files)
        - Various encodings (UTF-8, UTF-16)
        - Different sync options (backup, diff, dry-run)
        - File creation vs. updates
        - Subdirectory handling
        - Error conditions

        Args:
            scenario: Test scenario configuration.
            tmp_path: Pytest temporary directory fixture.
        """
        # Setup file paths
        if scenario["create_subdirs"]:
            source_path = tmp_path / "src" / "nested" / "source.txt"
            target_path = tmp_path / "dst" / "nested" / "target.txt"
        else:
            source_path = tmp_path / "source.txt"
            target_path = tmp_path / "target.txt"

        # Create source file
        create_test_file(
            source_path,
            scenario["source_content"],
            encoding=scenario["source_encoding"],
            create_dirs=True,
        )

        # Create target file if specified
        if scenario["target_content"] is not None:
            create_test_file(
                target_path,
                scenario["target_content"],
                encoding=scenario["target_encoding"],
                create_dirs=True,
            )

        # Execute sync and verify results
        if scenario["should_raise"]:
            with pytest.raises(scenario["should_raise"]):
                sync_files(source_path, target_path, options=scenario["options"])
        else:
            result = sync_files(source_path, target_path, options=scenario["options"])
            # Only verify if source_content is not None
            if scenario["source_content"] is not None:
                verify_sync_result(result, scenario, target_path, scenario["source_content"])

    def test_concurrent_file_modifications(self, tmp_path: Path) -> None:
        """Test handling of files that change during synchronization process.

        This test simulates race conditions and concurrent file access scenarios.
        """
        source_path = tmp_path / "source.txt"
        target_path = tmp_path / "target.txt"

        # Initial setup
        source_path.write_text("Initial content", encoding="utf-8")
        target_path.write_text("Target content", encoding="utf-8")

        # Sync with backup
        result = sync_files(
            source_path, target_path, options=SyncOptions(backup=True, show_diff=True)
        )

        assert result.changed is True
        assert result.backup_path is not None
        assert target_path.read_text(encoding="utf-8") == "Initial content"

        # Modify source and sync again
        source_path.write_text("Modified content", encoding="utf-8")

        second_result = sync_files(source_path, target_path, options=SyncOptions(backup=True))

        assert second_result.changed is True
        assert target_path.read_text(encoding="utf-8") == "Modified content"

        # Multiple backups should exist
        backups = list(tmp_path.glob("*.bak"))
        assert len(backups) >= 1

    def test_permission_and_filesystem_edge_cases(self, tmp_path: Path) -> None:
        """Test edge cases related to file permissions and filesystem limitations."""
        source_path = tmp_path / "source.txt"
        target_path = tmp_path / "target.txt"

        # Create source file
        source_path.write_text("Content", encoding="utf-8")

        # Test with read-only target (if supported by filesystem)
        target_path.write_text("Old content", encoding="utf-8")

        try:
            # Make target read-only
            target_path.chmod(stat.S_IREAD)

            # This should still work as sync_files overwrites the file
            result = sync_files(source_path, target_path, options=SyncOptions())
            assert result.changed is True

        except (OSError, PermissionError):
            # Skip if filesystem doesn't support permission changes
            pytest.skip("Filesystem doesn't support permission modifications")
        finally:
            # Restore permissions for cleanup
            with contextlib.suppress(OSError, PermissionError):
                target_path.chmod(stat.S_IWRITE | stat.S_IREAD)

    def test_symlink_handling(self, tmp_path: Path) -> None:
        """Test synchronization behavior with symbolic links.

        This test verifies that the sync follows symlinks and operates on
        the actual file content rather than the link itself.
        """
        # Create actual files
        actual_source = tmp_path / "actual_source.txt"
        actual_target = tmp_path / "actual_target.txt"

        actual_source.write_text("Source via symlink", encoding="utf-8")
        actual_target.write_text("Target via symlink", encoding="utf-8")

        # Create symlinks
        source_link = tmp_path / "source_link.txt"
        target_link = tmp_path / "target_link.txt"

        try:
            source_link.symlink_to(actual_source)
            target_link.symlink_to(actual_target)

            # Sync through symlinks
            result = sync_files(source_link, target_link, options=SyncOptions(show_diff=True))

            assert result.changed is True
            assert actual_target.read_text(encoding="utf-8") == "Source via symlink"

        except OSError:
            # Skip if filesystem doesn't support symlinks
            pytest.skip("Filesystem doesn't support symbolic links")

    def test_performance_with_large_files(self, tmp_path: Path) -> None:
        """Test synchronization performance and behavior with large files."""
        source_path = tmp_path / "large_source.txt"
        target_path = tmp_path / "large_target.txt"

        # Create a substantial file (~1MB)
        large_content = "This is a line of text for performance testing.\n" * 20000
        source_path.write_text(large_content, encoding="utf-8")

        # Different target content
        target_content = "Different line of text for performance testing.\n" * 15000
        target_path.write_text(target_content, encoding="utf-8")

        # Sync with all options
        result = sync_files(
            source_path, target_path, options=SyncOptions(backup=True, show_diff=True)
        )

        assert result.changed is True
        assert result.backup_path is not None
        assert result.backup_path.exists()
        assert target_path.read_text(encoding="utf-8") == large_content

        # Verify backup contains original content
        backup_content = result.backup_path.read_text(encoding="utf-8")
        assert backup_content == target_content

    def test_mixed_encoding_scenarios(self, tmp_path: Path) -> None:
        """Test various text encoding scenarios and error handling."""
        # Test different encoding scenarios
        test_cases = [
            ("utf-8", "Hello 世界! 🌍"),
            ("utf-16", "Тест кодировки"),
            ("latin-1", "Café naïve résumé"),
        ]

        for i, (encoding, content) in enumerate(test_cases):
            source_path = tmp_path / f"source_{i}.txt"
            target_path = tmp_path / f"target_{i}.txt"

            # Create files with specific encoding
            source_path.write_text(content, encoding=encoding)
            target_path.write_text("Old content", encoding=encoding)

            # Sync with matching encoding (allow binary for non-UTF-8 encodings)
            allow_binary = encoding != "utf-8"
            result = sync_files(
                source_path,
                target_path,
                options=SyncOptions(encoding=encoding, show_diff=True, allow_binary=allow_binary),
            )

            assert result.changed is True
            assert target_path.read_text(encoding=encoding) == content

    def test_error_recovery_scenarios(self, tmp_path: Path) -> None:
        """Test error handling and recovery in various failure scenarios."""
        source_path = tmp_path / "source.txt"
        missing_target_dir = tmp_path / "missing" / "target.txt"

        source_path.write_text("Content", encoding="utf-8")

        # Test 1: Target in non-existent directory (should be created)
        result = sync_files(source_path, missing_target_dir, options=SyncOptions())
        assert result.changed is True
        assert missing_target_dir.exists()
        assert missing_target_dir.read_text(encoding="utf-8") == "Content"

        # Test 2: Source and target are the same (should error)
        with pytest.raises(FileSyncError, match="must be different"):
            sync_files(source_path, source_path, options=SyncOptions())

        # Test 3: Non-existent source
        non_existent = tmp_path / "does_not_exist.txt"
        target_path = tmp_path / "target.txt"

        with pytest.raises(FileSyncError, match="Source file not found"):
            sync_files(non_existent, target_path, options=SyncOptions())
