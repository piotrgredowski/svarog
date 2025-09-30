import json
import tempfile
from pathlib import Path

import pytest

from svarog._claude_hooks.post_tool_use import process_post_tool_use


class TestPostToolUse:
    """Test cases for post tool use processing."""

    def test_process_post_tool_use_creates_log_file(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that process_post_tool_use creates log file and writes data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monkeypatch.setenv("SVAROG__CLAUDE_HOOKS_LOGS_DIR", temp_dir)
            test_data = {"tool": "bash", "result": "success", "timestamp": "2023-01-01"}

            process_post_tool_use(test_data)

            log_file = Path(temp_dir) / "post_tool_use.json"
            assert log_file.exists()

            with log_file.open() as f:
                logged_data = json.load(f)

            assert logged_data == [test_data]

    def test_process_post_tool_use_appends_to_existing_log(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that process_post_tool_use appends to existing log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monkeypatch.setenv("SVAROG__CLAUDE_HOOKS_LOGS_DIR", temp_dir)
            log_file = Path(temp_dir) / "post_tool_use.json"

            # Create existing log data
            existing_data = [{"tool": "read", "result": "success", "timestamp": "2023-01-01"}]
            with log_file.open("w") as f:
                json.dump(existing_data, f)

            new_data = {"tool": "bash", "result": "success", "timestamp": "2023-01-02"}

            process_post_tool_use(new_data)

            with log_file.open() as f:
                logged_data = json.load(f)

            assert len(logged_data) == 2
            assert logged_data[0] == existing_data[0]
            assert logged_data[1] == new_data

    def test_process_post_tool_use_handles_corrupted_log(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that process_post_tool_use handles corrupted JSON log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monkeypatch.setenv("SVAROG__CLAUDE_HOOKS_LOGS_DIR", temp_dir)
            log_file = Path(temp_dir) / "post_tool_use.json"

            # Create corrupted log file
            with log_file.open("w") as f:
                f.write("invalid json content")

            test_data = {"tool": "bash", "result": "error", "timestamp": "2023-01-01"}

            process_post_tool_use(test_data)

            with log_file.open() as f:
                logged_data = json.load(f)

            # Should start fresh with just the new data
            assert logged_data == [test_data]

    def test_process_post_tool_use_with_empty_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that process_post_tool_use handles empty input data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monkeypatch.setenv("SVAROG__CLAUDE_HOOKS_LOGS_DIR", temp_dir)
            test_data = {}

            process_post_tool_use(test_data)

            log_file = Path(temp_dir) / "post_tool_use.json"
            assert log_file.exists()

            with log_file.open() as f:
                logged_data = json.load(f)

            assert logged_data == [test_data]

    def test_process_post_tool_use_with_complex_data(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that process_post_tool_use handles complex nested data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            monkeypatch.setenv("SVAROG__CLAUDE_HOOKS_LOGS_DIR", temp_dir)
            test_data = {
                "tool": "read",
                "result": {
                    "status": "success",
                    "data": ["line1", "line2"],
                    "metadata": {"lines": 2, "encoding": "utf-8"},
                },
                "timestamp": "2023-01-01T12:00:00Z",
            }

            process_post_tool_use(test_data)

            log_file = Path(temp_dir) / "post_tool_use.json"
            with log_file.open() as f:
                logged_data = json.load(f)

            assert logged_data == [test_data]
