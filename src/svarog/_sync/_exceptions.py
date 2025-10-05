from pathlib import Path


class FileSyncError(Exception):
    """Raise when file synchronization fails.

    Prefer callers to provide either a message or a path so the class
    constructs consistent messages internally.
    """

    def __init__(
        self,
        message: str | None = None,
        *,
        path: Path | str | None = None,
    ) -> None:
        if message is None:
            if path is not None:
                msg = "Source file not found: " + str(path)
            else:
                msg = "File synchronization failed."
        else:
            msg = message
        super().__init__(msg)
