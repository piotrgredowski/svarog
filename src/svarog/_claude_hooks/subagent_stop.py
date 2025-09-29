import contextlib
import json
import typing as t
from pathlib import Path

from svarog._utils.svarlog_logger import logger
from svarog._utils.tts import say

from ._common import get_logs_directory


def announce_subagent_completion() -> None:
    """Announce subagent completion using the best available TTS service."""
    # Use fixed message for subagent completion
    completion_message = "Subagent Complete"

    say(completion_message)


def process_subagent_stop(input_data: dict[str, t.Any], *, chat: bool = False) -> None:
    """Process subagent stop hook data and optionally save chat transcript."""
    # Ensure log directory exists
    log_dir = get_logs_directory()
    log_path = log_dir / "subagent_stop.json"

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

    # Handle --chat switch (same as stop.py)
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
                chat_file = log_dir / "chat.json"
                with chat_file.open("w") as f:
                    json.dump(chat_data, f, indent=2)
            except OSError as e:
                logger.error("Failed to process chat transcript", error=str(e))

    # Announce subagent completion via TTS
    announce_subagent_completion()
