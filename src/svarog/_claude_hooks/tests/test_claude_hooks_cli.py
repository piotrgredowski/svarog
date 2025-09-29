import json
import tempfile
from pathlib import Path

from typer.testing import CliRunner

from svarog._claude_hooks._cli import claude_hooks_app
from svarog._utils.tts import disable_tts
from svarog._utils.tts import enable_tts


class TestClaudeHooksCLI:
    """Test cases for the Claude hooks CLI interface."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()
        # Disable TTS to avoid side effects during testing
        disable_tts()

    def teardown_method(self) -> None:
        """Clean up after tests."""
        enable_tts()

    def test_claude_hooks_app_help(self) -> None:
        """Test the help command for claude hooks app."""
        result = self.runner.invoke(claude_hooks_app, ["--help"])
        assert result.exit_code == 0
        assert "claude-hooks" in result.stdout
        assert "A collection of Claude hooks utilities" in result.stdout

    def test_notification_command_success(self) -> None:
        """Test notification command with valid JSON input."""
        test_data = {"message": "test notification", "timestamp": "2023-01-01"}
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(claude_hooks_app, ["notification"], input=json_input)

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "notification.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_notification_command_with_notify_flag(self) -> None:
        """Test notification command with --notify flag."""
        test_data = {"message": "test notification", "timestamp": "2023-01-01"}
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(
                claude_hooks_app, ["notification", "--notify"], input=json_input
            )

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "notification.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_notification_command_invalid_json(self) -> None:
        """Test notification command with invalid JSON input."""
        invalid_json = "not valid json"

        result = self.runner.invoke(claude_hooks_app, ["notification"], input=invalid_json)

        assert result.exit_code == 1
        assert "Error: Invalid JSON input" in result.stderr

    def test_post_tool_use_command_success(self) -> None:
        """Test post_tool_use command with valid JSON input."""
        test_data = {"tool": "bash", "result": "success", "timestamp": "2023-01-01"}
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(claude_hooks_app, ["post-tool-use"], input=json_input)

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "post_tool_use.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_post_tool_use_command_invalid_json(self) -> None:
        """Test post_tool_use command with invalid JSON input."""
        invalid_json = "not valid json"

        result = self.runner.invoke(claude_hooks_app, ["post-tool-use"], input=invalid_json)

        assert result.exit_code == 1
        assert "Error: Invalid JSON input" in result.stderr

    def test_pre_tool_use_command_success(self) -> None:
        """Test pre_tool_use command with valid JSON input."""
        test_data = {
            "tool_name": "bash",
            "tool_input": {"command": "ls -la"},
            "timestamp": "2023-01-01",
        }
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(claude_hooks_app, ["pre-tool-use"], input=json_input)

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "pre_tool_use.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_pre_tool_use_command_invalid_json(self) -> None:
        """Test pre_tool_use command with invalid JSON input."""
        invalid_json = "not valid json"

        result = self.runner.invoke(claude_hooks_app, ["pre-tool-use"], input=invalid_json)

        assert result.exit_code == 1
        assert "Error: Invalid JSON input" in result.stderr

    def test_stop_command_success(self) -> None:
        """Test stop command with valid JSON input."""
        test_data = {"status": "completed", "timestamp": "2023-01-01"}
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(claude_hooks_app, ["stop"], input=json_input)

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "stop.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_stop_command_with_chat_flag(self) -> None:
        """Test stop command with --chat flag."""
        test_data = {"status": "completed", "timestamp": "2023-01-01"}
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(claude_hooks_app, ["stop", "--chat"], input=json_input)

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "stop.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_stop_command_invalid_json(self) -> None:
        """Test stop command with invalid JSON input."""
        invalid_json = "not valid json"

        result = self.runner.invoke(claude_hooks_app, ["stop"], input=invalid_json)

        assert result.exit_code == 1
        assert "Error: Invalid JSON input" in result.stderr

    def test_subagent_stop_command_success(self) -> None:
        """Test subagent_stop command with valid JSON input."""
        test_data = {"subagent_id": "123", "status": "completed", "timestamp": "2023-01-01"}
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(claude_hooks_app, ["subagent-stop"], input=json_input)

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "subagent_stop.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_subagent_stop_command_with_chat_flag(self) -> None:
        """Test subagent_stop command with --chat flag."""
        test_data = {"subagent_id": "123", "status": "completed", "timestamp": "2023-01-01"}
        json_input = json.dumps(test_data)

        with tempfile.TemporaryDirectory() as temp_dir, self.runner.isolated_filesystem(temp_dir):
            result = self.runner.invoke(
                claude_hooks_app, ["subagent-stop", "--chat"], input=json_input
            )

            assert result.exit_code == 0

            # Verify log file was created
            logs_dir = Path("_claude_hooks_logs")
            if logs_dir.exists():
                log_file = logs_dir / "subagent_stop.json"
                if log_file.exists():
                    with log_file.open() as f:
                        logged_data = json.load(f)
                    assert test_data in logged_data

    def test_subagent_stop_command_invalid_json(self) -> None:
        """Test subagent_stop command with invalid JSON input."""
        invalid_json = "not valid json"

        result = self.runner.invoke(claude_hooks_app, ["subagent-stop"], input=invalid_json)

        assert result.exit_code == 1
        assert "Error: Invalid JSON input" in result.stderr
