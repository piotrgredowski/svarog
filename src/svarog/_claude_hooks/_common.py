import os
import pathlib


def get_logs_directory() -> pathlib.Path:
    """Get the directory where logs are stored."""
    dir_name = os.getenv("SVAROG__CLAUDE_HOOKS_LOGS_DIR", ".claude/hooks_logs")
    dir_ = pathlib.Path.cwd() / dir_name
    dir_.mkdir(parents=True, exist_ok=True)
    return dir_
