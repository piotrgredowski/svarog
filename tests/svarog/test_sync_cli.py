from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from svarog.cli import cli_app


class TestSyncCLI:
    """Integration tests for the ``svarog sync`` command."""

    def setup_method(self) -> None:
        """Create a Typer runner for tests."""
        self.runner = CliRunner()

    def test_sync_group_help(self) -> None:
        """Ensure the sync command group exposes helpful usage output."""
        result = self.runner.invoke(cli_app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "files" in result.stdout
        assert "Synchronize file contents" in result.stdout

    def test_sync_files_help(self) -> None:
        """Ensure the files subcommand advertises available options."""
        result = self.runner.invoke(cli_app, ["sync", "files", "--help"])
        assert result.exit_code == 0
        assert "--dry-run" in result.stdout
        assert "--diff" in result.stdout
        assert "--backup" in result.stdout
        assert "--binary" in result.stdout

    def test_sync_creates_missing_target(self) -> None:
        """Copy content to a missing target file."""
        with self.runner.isolated_filesystem():
            Path("source.txt").write_text("hello", encoding="utf-8")
            result = self.runner.invoke(
                cli_app,
                ["sync", "files", "source.txt", "target.txt"],
            )
            assert result.exit_code == 0
            assert "Synchronized source.txt -> target.txt." in result.stdout
            assert Path("target.txt").read_text(encoding="utf-8") == "hello"

    def test_sync_reports_already_in_sync(self) -> None:
        """Report when no synchronization work is required."""
        with self.runner.isolated_filesystem():
            Path("source.txt").write_text("data", encoding="utf-8")
            Path("target.txt").write_text("data", encoding="utf-8")

            first = self.runner.invoke(
                cli_app,
                ["sync", "files", "source.txt", "target.txt"],
            )
            assert first.exit_code == 0

            second = self.runner.invoke(
                cli_app,
                ["sync", "files", "source.txt", "target.txt"],
            )
            assert second.exit_code == 0
            assert "Already in sync." in second.stdout

    def test_sync_dry_run_with_diff(self) -> None:
        """Show diff output without modifying the destination in dry-run mode."""
        with self.runner.isolated_filesystem():
            Path("source.txt").write_text("new\n", encoding="utf-8")
            Path("target.txt").write_text("old\n", encoding="utf-8")

            result = self.runner.invoke(
                cli_app,
                [
                    "sync",
                    "files",
                    "source.txt",
                    "target.txt",
                    "--dry-run",
                    "--diff",
                ],
            )
            assert result.exit_code == 0
            assert "Dry run" in result.stdout
            assert "--- source.txt" in result.stdout
            assert "+++ target.txt" in result.stdout
            assert Path("target.txt").read_text(encoding="utf-8") == "old\n"

    def test_sync_creates_backup(self) -> None:
        """Backup the existing target before overwriting."""
        with self.runner.isolated_filesystem():
            Path("source.txt").write_text("updated", encoding="utf-8")
            Path("target.txt").write_text("stale", encoding="utf-8")

            result = self.runner.invoke(
                cli_app,
                [
                    "sync",
                    "files",
                    "source.txt",
                    "target.txt",
                    "--backup",
                    "--diff",
                ],
            )
            assert result.exit_code == 0
            assert "Synchronized source.txt -> target.txt." in result.stdout
            assert "Backup created at" in result.stdout
            backups = sorted(Path().glob("target.txt.*.bak"))
            assert len(backups) == 1
            assert backups[0].read_text(encoding="utf-8") == "stale"
            assert Path("target.txt").read_text(encoding="utf-8") == "updated"

    def test_sync_blocks_binary_without_flag(self) -> None:
        """Block binary synchronization unless explicitly requested."""
        with self.runner.isolated_filesystem():
            Path("source.bin").write_bytes(b"\x00\x01")

            result = self.runner.invoke(
                cli_app,
                [
                    "sync",
                    "files",
                    "source.bin",
                    "target.bin",
                ],
            )
            assert result.exit_code == 1
            assert "Binary file detected" in result.stderr
            assert not Path("target.bin").exists()

    def test_sync_allows_binary_with_flag(self) -> None:
        """Allow binary synchronization when the flag is passed."""
        with self.runner.isolated_filesystem():
            payload = b"\x00\x01\x02"
            Path("source.bin").write_bytes(payload)

            result = self.runner.invoke(
                cli_app,
                [
                    "sync",
                    "files",
                    "source.bin",
                    "target.bin",
                    "--binary",
                ],
            )
            assert result.exit_code == 0
            assert Path("target.bin").read_bytes() == payload

    @pytest.mark.parametrize(
        ("args", "expected"),
        [
            (("missing.txt", "target.txt"), "Source file not found"),
            (("source.txt", "target"), "Target path is a directory"),
        ],
    )
    def test_sync_reports_errors(self, args: tuple[str, str], expected: str) -> None:
        """Surface configuration and validation errors from the sync module."""
        with self.runner.isolated_filesystem():
            Path("source.txt").write_text("content", encoding="utf-8")
            Path("target").mkdir()

            cli_args = ["sync", "files", *args]
            result = self.runner.invoke(cli_app, cli_args)
            assert result.exit_code == 1
            assert expected in result.stderr

    def test_sync_errors_on_same_path(self) -> None:
        """Reject attempts to synchronize a file with itself."""
        with self.runner.isolated_filesystem():
            Path("file.txt").write_text("text", encoding="utf-8")

            result = self.runner.invoke(
                cli_app,
                [
                    "sync",
                    "files",
                    "file.txt",
                    "file.txt",
                ],
            )
            assert result.exit_code == 1
            assert "must be different" in result.stderr
