import typing as t

import pyttsx3

from svarog._utils.svarlog_logger import logger


class TTSProtocol(t.Protocol):
    """Protocol for TTS functions."""

    def __call__(self, text: str) -> None:
        """Speak the provided text."""


def _say_with_pyttsx3(text: str) -> None:  # pragma: no cover
    """Speak the provided text using pyttsx3 TTS engine."""
    # Initialize TTS engine
    engine = pyttsx3.init()  # type: ignore[no-untyped-call]

    # Configure engine settings
    engine.setProperty("rate", 180)  # Speech rate (words per minute)
    engine.setProperty("volume", 0.8)  # Volume (0.0 to 1.0)

    logger.debug(f"🎙️ pyttsx3 says: '{text}'")

    # Speak the text
    engine.say(text)
    engine.runAndWait()

    logger.debug("✅ Playback complete!")


def _noop_tts(text: str) -> None:
    """No-op TTS function for testing."""
    logger.debug(f"🔇 TTS disabled: '{text}'")


# Global TTS function that can be easily replaced for testing
_current_tts_function: TTSProtocol = _say_with_pyttsx3  # pragma: no cover


def set_tts_function(tts_function: TTSProtocol) -> None:  # pragma: no cover
    """Set the TTS function to use. Useful for testing."""
    global _current_tts_function  # noqa: PLW0603
    _current_tts_function = tts_function


def disable_tts() -> None:  # pragma: no cover
    """Disable TTS by setting a no-op function."""
    set_tts_function(_noop_tts)


def enable_tts() -> None:  # pragma: no cover
    """Enable TTS by setting the real pyttsx3 function."""
    set_tts_function(_say_with_pyttsx3)


def say(text: str) -> None:
    """Speak the provided text.

    Args:
        text: The text to speak.
    """
    _current_tts_function(text)


if __name__ == "__main__":  # pragma: no cover
    say("That's the demo text!")
