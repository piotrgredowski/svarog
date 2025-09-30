import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

from svarog._claude_hooks.notification import announce_notification
from svarog._claude_hooks.notification import process_notification
from svarog._utils.tts import enable_tts
from svarog._utils.tts import set_tts_function


class TestNotification:
    """Test cases for notification handling."""

    @patch("random.random")
    @patch("getpass.getuser")
    def test_announce_notification_with_engineer_name_env(
        self, mock_getuser: MagicMock, mock_random: MagicMock
    ) -> None:
        """Test announce_notification with ENGINEER_NAME environment variable."""
        mock_random.return_value = 0.2  # Less than 0.3, should include name
        mock_getuser.return_value = "testuser"

        # Set up TTS mock
        mock_tts = MagicMock()
        set_tts_function(mock_tts)

        try:
            with patch.dict(os.environ, {"ENGINEER_NAME": "John"}):
                announce_notification()

            mock_tts.assert_called_once_with("John, your agent needs your input")
        finally:
            # Restore original TTS
            enable_tts()

    @patch("random.random")
    @patch("getpass.getuser")
    def test_announce_notification_with_getuser_fallback(
        self, mock_getuser: MagicMock, mock_random: MagicMock
    ) -> None:
        """Test announce_notification falling back to getuser when ENGINEER_NAME is empty."""
        mock_random.return_value = 0.2  # Less than 0.3, should include name
        mock_getuser.return_value = "testuser"

        # Set up TTS mock
        mock_tts = MagicMock()
        set_tts_function(mock_tts)

        try:
            with patch.dict(os.environ, {"ENGINEER_NAME": ""}, clear=False):
                announce_notification()

            mock_tts.assert_called_once_with("testuser, your agent needs your input")
        finally:
            # Restore original TTS
            enable_tts()

    @patch("random.random")
    @patch("getpass.getuser")
    def test_announce_notification_generic_message(
        self, mock_getuser: MagicMock, mock_random: MagicMock
    ) -> None:
        """Test announce_notification with generic message when random >= 0.3."""
        mock_random.return_value = 0.5  # Greater than 0.3, should use generic message
        mock_getuser.return_value = "testuser"

        # Set up TTS mock
        mock_tts = MagicMock()
        set_tts_function(mock_tts)

        try:
            with patch.dict(os.environ, {"ENGINEER_NAME": "John"}):
                announce_notification()

            mock_tts.assert_called_once_with("Your agent needs your input")
        finally:
            # Restore original TTS
            enable_tts()

    def test_process_notification_creates_log_file(self) -> None:
        """Test that process_notification creates log file and writes data."""
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}),
        ):
            test_data = {"message": "test message", "timestamp": "2023-01-01"}

            process_notification(test_data, notify=False)

            log_file = Path(temp_dir) / "notification.json"
            assert log_file.exists()

            with log_file.open() as f:
                logged_data = json.load(f)

            assert logged_data == [test_data]

    def test_process_notification_appends_to_existing_log(self) -> None:
        """Test that process_notification appends to existing log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "notification.json"

            # Create existing log data
            existing_data = [{"message": "existing", "timestamp": "2023-01-01"}]
            with log_file.open("w") as f:
                json.dump(existing_data, f)

            with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                new_data = {"message": "new message", "timestamp": "2023-01-02"}

                process_notification(new_data, notify=False)

                with log_file.open() as f:
                    logged_data = json.load(f)

                assert len(logged_data) == 2
                assert logged_data[0] == existing_data[0]
                assert logged_data[1] == new_data

    def test_process_notification_handles_corrupted_log(self) -> None:
        """Test that process_notification handles corrupted JSON log file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "notification.json"

            # Create corrupted log file
            with log_file.open("w") as f:
                f.write("invalid json content")

            with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                test_data = {"message": "test message", "timestamp": "2023-01-01"}

                process_notification(test_data, notify=False)

                with log_file.open() as f:
                    logged_data = json.load(f)

                # Should start fresh with just the new data
                assert logged_data == [test_data]

    def test_process_notification_calls_announce_when_notify_true(self) -> None:
        """Test that process_notification calls announce_notification when notify=True."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up TTS mock to capture TTS calls
            mock_tts = MagicMock()
            set_tts_function(mock_tts)

            try:
                with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                    test_data = {"message": "test message", "timestamp": "2023-01-01"}

                    # Mock random and getuser for predictable announce_notification behavior
                    with (
                        patch("random.random", return_value=0.5),
                        patch("getpass.getuser", return_value="testuser"),
                    ):
                        process_notification(test_data, notify=True)

                # Verify TTS was called (indicating announce_notification was called)
                mock_tts.assert_called_once_with("Your agent needs your input")
            finally:
                # Restore original TTS
                enable_tts()

    def test_process_notification_skips_announce_for_generic_message(self) -> None:
        """Test that process_notification skips announce for generic Claude waiting message."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up TTS mock to capture TTS calls
            mock_tts = MagicMock()
            set_tts_function(mock_tts)

            try:
                with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                    test_data = {
                        "message": "Claude is waiting for your input",
                        "timestamp": "2023-01-01",
                    }

                    process_notification(test_data, notify=True)

                # Verify TTS was NOT called (indicating announce_notification was NOT called)
                mock_tts.assert_not_called()
            finally:
                # Restore original TTS
                enable_tts()

    def test_process_notification_no_announce_when_notify_false(self) -> None:
        """Test that process_notification doesn't call announce when notify=False."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up TTS mock to capture TTS calls
            mock_tts = MagicMock()
            set_tts_function(mock_tts)

            try:
                with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": temp_dir}):
                    test_data = {"message": "test message", "timestamp": "2023-01-01"}

                    process_notification(test_data, notify=False)

                # Verify TTS was NOT called (indicating announce_notification was NOT called)
                mock_tts.assert_not_called()
            finally:
                # Restore original TTS
                enable_tts()
