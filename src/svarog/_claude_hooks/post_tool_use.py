#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# ///

import json
import typing as t

from ._common import get_logs_directory


def process_post_tool_use(input_data: dict[str, t.Any]) -> None:
    """Process post tool use data and log it."""
    # Ensure log directory exists
    log_dir = get_logs_directory()
    log_path = log_dir / "post_tool_use.json"

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
