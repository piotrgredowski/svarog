#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import getpass
import json
import os
import random
import typing as t

from svarog._claude_hooks._common import get_logs_directory
from svarog._utils.tts import say


def announce_notification() -> None:
    """Announce that the agent needs user input."""
    # Get engineer name if available
    engineer_name = os.getenv("ENGINEER_NAME", "").strip() or getpass.getuser()

    if engineer_name and random.random() < 0.3:  # noqa: PLR2004, S311
        notification_message = f"{engineer_name}, your agent needs your input"
    else:
        notification_message = "Your agent needs your input"
    say(notification_message)


def process_notification(input_data: dict[str, t.Any], *, notify: bool = False) -> None:
    """Process notification data and optionally announce via TTS."""
    # Ensure log directory exists
    log_dir = get_logs_directory()
    log_file = log_dir / "notification.json"

    # Read existing log data or initialize empty list
    if log_file.exists():
        with log_file.open() as f:
            try:
                log_data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                log_data = []
    else:
        log_data = []

    # Append new data
    log_data.append(input_data)

    # Write back to file with formatting
    with log_file.open("w") as f:
        json.dump(log_data, f, indent=2)

    # Announce notification via TTS only if notify flag is set
    # Skip TTS for the generic "Claude is waiting for your input" message
    if notify and input_data.get("message") != "Claude is waiting for your input":
        announce_notification()
