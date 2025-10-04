import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from svarog._claude_hooks.pre_tool_use import is_dangerous_rm_command
from svarog._claude_hooks.pre_tool_use import is_env_file_access
from svarog._claude_hooks.pre_tool_use import process_pre_tool_use


class TestPreToolUse:
    """Test cases for pre tool use processing."""

    def test_is_dangerous_rm_command_basic_patterns(self) -> None:
        """Test detection of basic dangerous rm command patterns."""
        dangerous_commands = [
            "rm -rf /",
            "rm -rf /home",
            "rm -rf .",
            "rm -rf *",
            "rm -fr /tmp",
            "rm -Rf /var",
            "RM -RF /",  # Case insensitive
            "rm  -rf  /",  # Extra spaces
        ]

        for cmd in dangerous_commands:
            assert is_dangerous_rm_command(cmd), f"Should detect '{cmd}' as dangerous"

    def test_is_dangerous_rm_command_long_form_flags(self) -> None:
        """Test detection of long form rm command flags."""
        dangerous_commands = [
            "rm --recursive --force /",
            "rm --force --recursive /home",
            "rm --recursive --force .",
        ]

        for cmd in dangerous_commands:
            assert is_dangerous_rm_command(cmd), f"Should detect '{cmd}' as dangerous"

    def test_is_dangerous_rm_command_separated_flags(self) -> None:
        """Test detection of separated rm flags."""
        dangerous_commands = [
            "rm -r /tmp -f",
            "rm -f /var -r",
            "rm -r . -f",
        ]

        for cmd in dangerous_commands:
            assert is_dangerous_rm_command(cmd), f"Should detect '{cmd}' as dangerous"

    def test_is_dangerous_rm_command_safe_patterns(self) -> None:
        """Test that safe rm commands are not flagged as dangerous."""
        safe_commands = [
            "rm file.txt",
            "rm -f file.txt",
            "rm -r specific_dir",
            "rm ./specific_file",
            "rm /path/to/specific/file",
            "ls -la",
            "mkdir test",
        ]

        for cmd in safe_commands:
            assert not is_dangerous_rm_command(cmd), f"Should not detect '{cmd}' as dangerous"

    def test_is_dangerous_rm_command_edge_cases(self) -> None:
        """Test edge cases for rm command detection."""
        # Test with various spacing and formatting
        dangerous_commands = [
            "  rm   -rf   /  ",  # Leading/trailing spaces
            "rm\t-rf\t/",  # Tabs
            "rm -rf / && echo done",  # Part of compound command
            "sudo rm -rf /",  # With sudo
        ]

        for cmd in dangerous_commands:
            assert is_dangerous_rm_command(cmd), f"Should detect '{cmd}' as dangerous"

    def test_process_pre_tool_use_creates_log_file(self) -> None:
        """Test that process_pre_tool_use creates log file and writes data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable to control logs directory
            old_env = os.environ.get("SVAROG__CLAUDE_HOOKS_LOGS_DIR")
            os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = temp_dir

            try:
                test_data = {"tool": "bash", "command": "ls -la", "timestamp": "2023-01-01"}

                process_pre_tool_use(test_data)

                log_file = Path(temp_dir) / "pre_tool_use.json"
                assert log_file.exists()

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [test_data]
            finally:
                # Restore original environment
                if old_env is None:
                    os.environ.pop("SVAROG__CLAUDE_HOOKS_LOGS_DIR", None)
                else:
                    os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = old_env

    def test_process_pre_tool_use_appends_to_existing_log(self) -> None:
        """Test that process_pre_tool_use appends to existing log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable to control logs directory
            old_env = os.environ.get("SVAROG__CLAUDE_HOOKS_LOGS_DIR")
            os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = temp_dir

            try:
                log_file = Path(temp_dir) / "pre_tool_use.json"

                # Create existing log data
                existing_data = [{"tool": "read", "file": "test.txt", "timestamp": "2023-01-01"}]
                with log_file.open("w") as f:
                    json.dump(existing_data, f)

                new_data = {"tool": "bash", "command": "echo hello", "timestamp": "2023-01-02"}

                process_pre_tool_use(new_data)

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert len(logged_data) == 2
                assert logged_data[0] == existing_data[0]
                assert logged_data[1] == new_data
            finally:
                # Restore original environment
                if old_env is None:
                    os.environ.pop("SVAROG__CLAUDE_HOOKS_LOGS_DIR", None)
                else:
                    os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = old_env

    def test_process_pre_tool_use_handles_corrupted_log(self) -> None:
        """Test that process_pre_tool_use handles corrupted JSON log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable to control logs directory
            old_env = os.environ.get("SVAROG__CLAUDE_HOOKS_LOGS_DIR")
            os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = temp_dir

            try:
                log_file = Path(temp_dir) / "pre_tool_use.json"

                # Create corrupted log file
                with log_file.open("w") as f:
                    f.write("invalid json content")

                test_data = {"tool": "bash", "command": "pwd", "timestamp": "2023-01-01"}

                process_pre_tool_use(test_data)

                with log_file.open() as f:
                    logged_data = json.load(f)

                # Should start fresh with just the new data
                assert logged_data == [test_data]
            finally:
                # Restore original environment
                if old_env is None:
                    os.environ.pop("SVAROG__CLAUDE_HOOKS_LOGS_DIR", None)
                else:
                    os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = old_env

    @patch("sys.exit")
    @patch("sys.stderr")
    def test_process_pre_tool_use_blocks_dangerous_command(self, mock_stderr, mock_exit) -> None:
        """Test that process_pre_tool_use blocks dangerous rm command."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable to control logs directory
            old_env = os.environ.get("SVAROG__CLAUDE_HOOKS_LOGS_DIR")
            os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = temp_dir

            try:
                dangerous_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "rm -rf /"},
                    "timestamp": "2023-01-01",
                }

                process_pre_tool_use(dangerous_data)

                # Check that exit was called with code 2
                mock_exit.assert_called_once_with(2)

                # Check that warning was printed to stderr
                stderr_calls = [call[0][0] for call in mock_stderr.write.call_args_list]
                blocked_found = any("BLOCKED" in str(call) for call in stderr_calls)
                assert blocked_found, "Should print BLOCKED message for dangerous command"
            finally:
                # Restore original environment
                if old_env is None:
                    os.environ.pop("SVAROG__CLAUDE_HOOKS_LOGS_DIR", None)
                else:
                    os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = old_env

    def test_process_pre_tool_use_allows_safe_command(self) -> None:
        """Test that process_pre_tool_use allows safe commands."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable to control logs directory
            old_env = os.environ.get("SVAROG__CLAUDE_HOOKS_LOGS_DIR")
            os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = temp_dir

            try:
                safe_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "ls -la"},
                    "timestamp": "2023-01-01",
                }

                process_pre_tool_use(safe_data)

                # Check that data was logged (no exit was called)
                log_file = Path(temp_dir) / "pre_tool_use.json"
                assert log_file.exists()

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [safe_data]
            finally:
                # Restore original environment
                if old_env is None:
                    os.environ.pop("SVAROG__CLAUDE_HOOKS_LOGS_DIR", None)
                else:
                    os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = old_env

    def test_is_env_file_access_read_tool(self) -> None:
        """Test env file access detection for Read tool."""
        assert is_env_file_access("Read", {"file_path": ".env"})
        assert is_env_file_access("Read", {"file_path": "/path/to/.env"})
        assert not is_env_file_access("Read", {"file_path": ".env.sample"})
        assert not is_env_file_access("Read", {"file_path": "config.py"})

    def test_is_env_file_access_bash_tool(self) -> None:
        """Test env file access detection for Bash tool."""
        assert is_env_file_access("Bash", {"command": "cat .env"})
        assert is_env_file_access("Bash", {"command": "echo SECRET=value > .env"})
        assert is_env_file_access("Bash", {"command": "touch .env"})
        assert not is_env_file_access("Bash", {"command": "cat .env.sample"})
        assert not is_env_file_access("Bash", {"command": "ls -la"})

    @patch("sys.exit")
    def test_process_pre_tool_use_blocks_env_file_access(self, mock_exit) -> None:
        """Test that process_pre_tool_use blocks .env file access."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set environment variable to control logs directory
            old_env = os.environ.get("SVAROG__CLAUDE_HOOKS_LOGS_DIR")
            os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = temp_dir

            try:
                env_data = {
                    "tool_name": "Read",
                    "tool_input": {"file_path": ".env"},
                    "timestamp": "2023-01-01",
                }

                process_pre_tool_use(env_data)

                # Check that exit was called with code 2
                mock_exit.assert_called_once_with(2)
            finally:
                # Restore original environment
                if old_env is None:
                    os.environ.pop("SVAROG__CLAUDE_HOOKS_LOGS_DIR", None)
                else:
                    os.environ["SVAROG__CLAUDE_HOOKS_LOGS_DIR"] = old_env

    def test_is_dangerous_rm_command_edge_case_with_newlines(self) -> None:
        """Test dangerous rm detection with edge case patterns."""
        # Test a pattern that might be missed
        edge_case_commands = [
            "rm -rf / # dangerous comment",
            "sudo rm -rf /tmp/*",
        ]

        for cmd in edge_case_commands:
            result = is_dangerous_rm_command(cmd)
            # These should be detected as dangerous
            assert result, f"Should detect '{cmd}' as dangerous"
