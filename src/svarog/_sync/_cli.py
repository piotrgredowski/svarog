from __future__ import annotations

import typer

from svarog._sync.file_sync import FileSyncError
from svarog._sync.file_sync import SyncOptions
from svarog._sync.file_sync import sync_files

SRC_ARGUMENT = typer.Argument(..., help="Source file to read from.", show_default=False)
DST_ARGUMENT = typer.Argument(..., help="Target file to write to.", show_default=False)
DRY_RUN_OPTION = typer.Option(
    default=False,
    help="Preview actions without writing modifications.",
    is_flag=True,
)
DIFF_OPTION = typer.Option(
    default=False,
    help="Show a unified diff of the proposed changes.",
    is_flag=True,
)
BACKUP_OPTION = typer.Option(
    default=False,
    help="Create a timestamped backup before overwriting the target.",
    is_flag=True,
)
BINARY_OPTION = typer.Option(
    default=False,
    help="Allow synchronization of binary files.",
    is_flag=True,
)
ENCODING_OPTION = typer.Option(
    default="utf-8",
    help="Text encoding to use when reading or writing files.",
)

sync_app = typer.Typer(
    name="sync",
    help="Synchronize file contents between paths.",
)


@sync_app.command()
def files(  # noqa: PLR0913
    src: str = SRC_ARGUMENT,
    dst: str = DST_ARGUMENT,
    *,
    dry_run: bool = DRY_RUN_OPTION,
    diff: bool = DIFF_OPTION,
    backup: bool = BACKUP_OPTION,
    binary: bool = BINARY_OPTION,
    encoding: str = ENCODING_OPTION,
) -> None:
    """Synchronize one file's contents into another.

    Args:
        src: Source file path as a string.
        dst: Target file path as a string.
        dry_run: Whether to preview actions without writing.
        diff: Whether to display a unified diff.
        backup: Whether to save a backup of the target before overwriting.
        binary: Whether binary files are allowed.
        encoding: Text encoding to use for reads and writes.

    Raises:
        typer.Exit: When synchronization cannot be completed.
    """
    options = SyncOptions(
        dry_run=dry_run,
        show_diff=diff,
        backup=backup,
        allow_binary=binary,
        encoding=encoding,
    )

    try:
        result = sync_files(src, dst, options=options)
    except FileSyncError as error:
        typer.echo("Error: " + str(error), err=True)
        raise typer.Exit(code=1) from error

    if result.reason == "dry_run":
        typer.echo("Dry run: " + src + " -> " + dst + ".")
    elif result.reason == "already_in_sync":
        typer.echo("Already in sync.")
    else:
        typer.echo("Synchronized " + src + " -> " + dst + ".")

    if result.backup_path is not None:
        typer.echo("Backup created at " + str(result.backup_path) + ".")

    if result.diff:
        typer.echo(result.diff.rstrip("\n"))
