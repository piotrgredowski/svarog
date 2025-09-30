import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from svarog._claude_hooks.subagent_stop import announce_subagent_completion
from svarog._claude_hooks.subagent_stop import process_subagent_stop
from svarog._utils.tts import disable_tts
from svarog._utils.tts import enable_tts


class TestSubagentStop:
    """Test cases for subagent stop hook processing."""

    def test_announce_subagent_completion(self) -> None:
        """Test that announce_subagent_completion calls TTS with fixed message."""
        # Use TTS dependency injection system to disable TTS for testing
        disable_tts()
        try:
            # This should not raise an exception
            announce_subagent_completion()
        finally:
            # Re-enable TTS for other tests
            enable_tts()

    def test_process_subagent_stop_creates_log_file(self) -> None:
        """Test that process_subagent_stop creates log file and writes data."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            # Disable TTS for testing
            disable_tts()
            try:
                test_data = {
                    "subagent_id": "123",
                    "status": "completed",
                    "timestamp": "2023-01-01",
                }

                process_subagent_stop(test_data, chat=False)

                log_file = Path(temp_dir) / "subagent_stop.json"
                assert log_file.exists()

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [test_data]
            finally:
                enable_tts()

    def test_process_subagent_stop_appends_to_existing_log(self) -> None:
        """Test that process_subagent_stop appends to existing log file."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            log_file = Path(temp_dir) / "subagent_stop.json"

            # Create existing log data
            existing_data = [{"subagent_id": "456", "status": "started", "timestamp": "2023-01-01"}]
            with log_file.open("w") as f:
                json.dump(existing_data, f)

            # Disable TTS for testing
            disable_tts()
            try:
                new_data = {
                    "subagent_id": "123",
                    "status": "completed",
                    "timestamp": "2023-01-02",
                }

                process_subagent_stop(new_data, chat=False)

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert len(logged_data) == 2
                assert logged_data[0] == existing_data[0]
                assert logged_data[1] == new_data
            finally:
                enable_tts()

    def test_process_subagent_stop_handles_corrupted_log(self) -> None:
        """Test that process_subagent_stop handles corrupted JSON log file."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            log_file = Path(temp_dir) / "subagent_stop.json"

            # Create corrupted log file
            with log_file.open("w") as f:
                f.write("invalid json content")

            # Disable TTS for testing
            disable_tts()
            try:
                test_data = {
                    "subagent_id": "123",
                    "status": "completed",
                    "timestamp": "2023-01-01",
                }

                process_subagent_stop(test_data, chat=False)

                with log_file.open() as f:
                    logged_data = json.load(f)

                # Should start fresh with just the new data
                assert logged_data == [test_data]
            finally:
                enable_tts()

    def test_process_subagent_stop_with_chat_true(self) -> None:
        """Test process_subagent_stop behavior when chat=True."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            # Disable TTS for testing
            disable_tts()
            try:
                test_data = {
                    "subagent_id": "123",
                    "status": "completed",
                    "timestamp": "2023-01-01",
                    "transcript": ["message1", "message2"],
                }

                process_subagent_stop(test_data, chat=True)

                log_file = Path(temp_dir) / "subagent_stop.json"
                assert log_file.exists()

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [test_data]
            finally:
                enable_tts()

    def test_process_subagent_stop_with_empty_data(self) -> None:
        """Test that process_subagent_stop handles empty input data."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            # Disable TTS for testing
            disable_tts()
            try:
                test_data = {}

                process_subagent_stop(test_data, chat=False)

                log_file = Path(temp_dir) / "subagent_stop.json"
                assert log_file.exists()

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [test_data]
            finally:
                enable_tts()

    def test_process_subagent_stop_with_complex_data(self) -> None:
        """Test that process_subagent_stop handles complex nested data."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            # Disable TTS for testing
            disable_tts()
            try:
                test_data = {
                    "subagent_id": "123",
                    "status": "completed",
                    "timestamp": "2023-01-01T12:00:00Z",
                    "metadata": {
                        "tools_used": ["bash", "read", "write"],
                        "duration": 45.2,
                        "success": True,
                    },
                    "output": {
                        "result": "Task completed successfully",
                        "artifacts": ["file1.py", "file2.txt"],
                    },
                }

                process_subagent_stop(test_data, chat=True)

                log_file = Path(temp_dir) / "subagent_stop.json"
                with log_file.open() as f:
                    logged_data = json.load(f)

                assert logged_data == [test_data]
            finally:
                enable_tts()

    def test_process_subagent_stop_with_chat_transcript(self) -> None:
        """Test that process_subagent_stop handles chat transcript when chat=True."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            # Create a mock transcript file
            transcript_file = Path(temp_dir) / "transcript.jsonl"
            with transcript_file.open("w") as f:
                f.write('{"role": "user", "content": "Hello"}\n')
                f.write('{"role": "assistant", "content": "Hi there"}\n')

            # Disable TTS for testing
            disable_tts()
            try:
                test_data = {
                    "subagent_id": "123",
                    "status": "completed",
                    "timestamp": "2023-01-01",
                    "transcript_path": str(transcript_file),
                }

                process_subagent_stop(test_data, chat=True)

                # Check that chat.json was created
                chat_file = Path(temp_dir) / "chat.json"
                assert chat_file.exists()

                with chat_file.open() as f:
                    chat_data = json.load(f)

                assert len(chat_data) == 2
                assert chat_data[0]["role"] == "user"
                assert chat_data[1]["role"] == "assistant"
            finally:
                enable_tts()
