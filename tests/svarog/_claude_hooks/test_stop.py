import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from svarog._claude_hooks.stop import announce_completion
from svarog._claude_hooks.stop import get_completion_message
from svarog._claude_hooks.stop import get_completion_messages
from svarog._claude_hooks.stop import process_stop
from svarog._utils.tts import disable_tts
from svarog._utils.tts import enable_tts
from svarog._utils.tts import set_tts_function


class TestStop:
    """Test cases for stop hook processing."""

    def test_get_completion_messages(self) -> None:
        """Test that get_completion_messages returns expected list."""
        messages = get_completion_messages()

        expected_messages = [
            "Work complete!",
            "All done!",
            "Task finished!",
            "Job complete!",
            "Ready for next task!",
        ]

        assert messages == expected_messages
        assert isinstance(messages, list)
        assert len(messages) == 5

    @patch("random.choice")
    def test_get_completion_message(self, mock_choice: MagicMock) -> None:
        """Test that get_completion_message returns a random message."""
        mock_choice.return_value = "Work complete!"

        message = get_completion_message()

        assert message == "Work complete!"
        mock_choice.assert_called_once()

        # Verify it was called with the correct list
        called_args = mock_choice.call_args[0][0]
        expected_messages = get_completion_messages()
        assert called_args == expected_messages

    @patch("svarog._claude_hooks.stop.get_completion_message")
    def test_announce_completion(self, mock_get_message: MagicMock) -> None:
        """Test that announce_completion calls TTS with completion message."""
        mock_get_message.return_value = "Task finished!"

        # Create a mock TTS function to capture calls
        mock_tts = MagicMock()
        set_tts_function(mock_tts)

        try:
            announce_completion()

            mock_get_message.assert_called_once()
            mock_tts.assert_called_once_with("Task finished!")
        finally:
            # Restore TTS after test
            enable_tts()

    def test_process_stop_creates_log_file(self) -> None:
        """Test that process_stop creates log file and writes data."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            # Disable TTS for this test
            disable_tts()

            try:
                test_data = {"status": "completed", "timestamp": "2023-01-01"}

                process_stop(test_data, chat=False)

                log_file = Path(temp_dir) / "stop.json"
                assert log_file.exists()

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [test_data]
            finally:
                # Restore TTS after test
                enable_tts()

    def test_process_stop_appends_to_existing_log(self) -> None:
        """Test that process_stop appends to existing log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "stop.json"

            # Create existing log data
            existing_data = [{"status": "started", "timestamp": "2023-01-01"}]
            with log_file.open("w") as f:
                json.dump(existing_data, f)

            with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                # Disable TTS for this test
                disable_tts()

                try:
                    new_data = {"status": "completed", "timestamp": "2023-01-02"}

                    process_stop(new_data, chat=False)

                    with log_file.open() as f:
                        logged_data = json.load(f)

                    assert len(logged_data) == 2
                    assert logged_data[0] == existing_data[0]
                    assert logged_data[1] == new_data
                finally:
                    # Restore TTS after test
                    enable_tts()

    def test_process_stop_handles_corrupted_log(self) -> None:
        """Test that process_stop handles corrupted JSON log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "stop.json"

            # Create corrupted log file
            with log_file.open("w") as f:
                f.write("invalid json content")

            with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                # Disable TTS for this test
                disable_tts()

                try:
                    test_data = {"status": "completed", "timestamp": "2023-01-01"}

                    process_stop(test_data, chat=False)

                    with log_file.open() as f:
                        logged_data = json.load(f)

                    # Should start fresh with just the new data
                    assert logged_data == [test_data]
                finally:
                    # Restore TTS after test
                    enable_tts()

    def test_process_stop_with_chat_transcript(self) -> None:
        """Test that process_stop handles chat transcript when chat=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a mock transcript file
            transcript_file = Path(temp_dir) / "transcript.jsonl"
            with transcript_file.open("w") as f:
                f.write('{"role": "user", "content": "Hello"}\n')
                f.write('{"role": "assistant", "content": "Hi there"}\n')

            with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                # Disable TTS for this test
                disable_tts()

                try:
                    test_data = {
                        "status": "completed",
                        "timestamp": "2023-01-01",
                        "transcript_path": str(transcript_file),
                    }

                    process_stop(test_data, chat=True)

                    # Check that chat.json was created
                    chat_file = Path(temp_dir) / "chat.json"
                    assert chat_file.exists()

                    with chat_file.open() as f:
                        chat_data = json.load(f)

                    assert len(chat_data) == 2
                    assert chat_data[0]["role"] == "user"
                    assert chat_data[1]["role"] == "assistant"
                finally:
                    # Restore TTS after test
                    enable_tts()

    def test_process_stop_with_empty_data(self) -> None:
        """Test that process_stop handles empty input data."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            # Disable TTS for this test
            disable_tts()

            try:
                test_data = {}

                process_stop(test_data, chat=False)

                log_file = Path(temp_dir) / "stop.json"
                assert log_file.exists()

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [test_data]
            finally:
                # Restore TTS after test
                enable_tts()
