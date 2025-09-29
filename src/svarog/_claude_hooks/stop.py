import contextlib
import json
import secrets
import typing as t
from pathlib import Path

from svarog._claude_hooks._common import get_logs_directory
from svarog._utils.svarlog_logger import logger
from svarog._utils.tts import say


def get_completion_messages() -> list[str]:
    """Return list of friendly completion messages."""
    return [
        "Work complete!",
        "All done!",
        "Task finished!",
        "Job complete!",
        "Ready for next task!",
    ]


def get_completion_message() -> str:
    messages = get_completion_messages()
    return secrets.choice(messages)


def announce_completion() -> None:
    """Announce completion using the best available TTS service."""
    completion_message = get_completion_message()

    # Call the TTS script with the completion message
    logger.info("Announcing completion", message=completion_message)

    say(completion_message)


def process_stop(input_data: dict[str, t.Any], *, chat: bool = False) -> None:
    """Process stop hook data and optionally save chat transcript."""
    # These fields are available but not used in current implementation
    # Keeping them for potential future use
    _ = input_data.get("session_id", "")
    _ = input_data.get("stop_hook_active", False)

    # Ensure log directory exists
    log_dir = get_logs_directory()
    log_path = log_dir / "stop.json"

    # Read existing log data or initialize empty list
    if log_path.exists():
        with log_path.open() as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []

    # Append new data
    log_data.append(input_data)

    # Write back to file with formatting
    with log_path.open("w") as f:
        json.dump(log_data, f, indent=2)

    # Handle --chat switch
    if chat and "transcript_path" in input_data:
        transcript_path = Path(input_data["transcript_path"])
        if transcript_path.exists():
            # Read .jsonl file and convert to JSON array
            chat_data = []
            try:
                with transcript_path.open() as f:
                    for transcript_line in f:
                        stripped_line = transcript_line.strip()
                        if stripped_line:
                            with contextlib.suppress(json.JSONDecodeError):
                                chat_data.append(json.loads(stripped_line))

                # Write to logs/chat.json
                chat_file = log_dir / "chat.json"
                with chat_file.open("w") as f:
                    json.dump(chat_data, f, indent=2)
            except OSError as e:
                logger.error("Failed to process chat transcript", error=str(e))

    # Announce completion via TTS
    announce_completion()
