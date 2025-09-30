import os
import pathlib
import tempfile
from unittest.mock import patch

from svarog._claude_hooks._common import get_logs_directory


class TestCommon:
    """Test cases for common utilities."""

    def test_get_logs_directory_default(self) -> None:
        """Test getting logs directory with default name."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to the temp directory so logs are created there
            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(temp_dir)
                logs_dir = get_logs_directory()
                expected_path = pathlib.Path(temp_dir) / ".claude/hooks_logs"
                assert logs_dir.resolve() == expected_path.resolve()
                assert logs_dir.exists()
                assert logs_dir.is_dir()
            finally:
                os.chdir(original_cwd)

    def test_get_logs_directory_custom_env(self) -> None:
        """Test getting logs directory with custom environment variable."""
        custom_dir_name = "custom_logs"
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": custom_dir_name}):
                    logs_dir = get_logs_directory()
                    expected_path = pathlib.Path(temp_dir) / custom_dir_name
                    assert logs_dir.resolve() == expected_path.resolve()
                    assert logs_dir.exists()
                    assert logs_dir.is_dir()
            finally:
                os.chdir(original_cwd)

    def test_get_logs_directory_creates_nested_path(self) -> None:
        """Test that nested directory paths are created properly."""
        nested_dir_name = "logs/nested/deep"
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(temp_dir)
                with patch.dict(os.environ, {"SVAROG__CLAUDE_HOOKS_LOGS_DIR": nested_dir_name}):
                    logs_dir = get_logs_directory()
                    expected_path = pathlib.Path(temp_dir) / nested_dir_name
                    assert logs_dir.resolve() == expected_path.resolve()
                    assert logs_dir.exists()
                    assert logs_dir.is_dir()
            finally:
                os.chdir(original_cwd)

    def test_get_logs_directory_exists_already(self) -> None:
        """Test that existing directory is returned without error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = pathlib.Path.cwd()
            try:
                os.chdir(temp_dir)
                # Create directory first
                first_call = get_logs_directory()
                assert first_call.exists()

                # Call again to ensure it handles existing directory
                second_call = get_logs_directory()
                assert second_call == first_call
                assert second_call.exists()
            finally:
                os.chdir(original_cwd)
