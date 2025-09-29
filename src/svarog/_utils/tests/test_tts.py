from unittest.mock import MagicMock

from svarog._utils import tts


class TestTTS:
    """Test cases for TTS utilities."""

    def setup_method(self) -> None:
        """Set up test environment before each test."""
        # Create a mock TTS function for most tests
        self.mock_tts_function = MagicMock()
        tts.set_tts_function(self.mock_tts_function)

    def teardown_method(self) -> None:
        """Clean up test environment after each test."""
        # Restore original TTS function
        tts.enable_tts()

    def test_say_with_global_mock_function(self) -> None:
        """Test the say function using global TTS function setting."""
        test_text = "Hello, World!"
        tts.say(test_text)

        # Verify the mock function was called with the text
        self.mock_tts_function.assert_called_once_with(test_text)

    def test_say_with_empty_string(self) -> None:
        """Test say function with empty string."""
        tts.say("")

        self.mock_tts_function.assert_called_once_with("")

    def test_say_with_special_characters(self) -> None:
        """Test say function with special characters."""
        special_text = "Hello! @#$%^&*() 123"
        tts.say(special_text)

        self.mock_tts_function.assert_called_once_with(special_text)

    def test_disable_and_enable_tts(self) -> None:
        """Test disabling and enabling TTS."""
        # Disable TTS
        tts.disable_tts()

        # This should not cause any errors and should use the no-op function
        tts.say("This should be silent")

        # Re-enable TTS
        tts.enable_tts()

        # Now it should use the real TTS function again
        # We can test this by setting a fresh mock
        fresh_mock = MagicMock()
        tts.set_tts_function(fresh_mock)

        tts.say("Now it should call our mock")
        fresh_mock.assert_called_once_with("Now it should call our mock")

    def test_disable_tts_function(self) -> None:
        """Test the disable TTS functionality."""
        # Disable TTS and ensure it doesn't raise errors
        tts.disable_tts()
        tts.say("This should be silent")

    def test_set_tts_function_directly(self) -> None:
        """Test that set_tts_function works correctly."""
        # Create a custom mock function
        custom_mock = MagicMock()

        # Set it and verify it's used
        tts.set_tts_function(custom_mock)
        tts.say("Direct function test")

        custom_mock.assert_called_once_with("Direct function test")
