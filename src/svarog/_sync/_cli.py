from __future__ import annotations

import typer

from ._exceptions import FileSyncError
from .file_sync import SyncOptions
from .file_sync import sync_files
from .section_mapping import SectionMappingError
from .section_mapping import parse_section_argument

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

# Option for mapping sections: created at module level to satisfy linting rules
SECTION_OPTION = typer.Option(
    None,
    "--section",
    "-s",
    help=(
        "Map a source section into a destination section. "
        "Format: <adapter>:src_path-><adapter>:dst_path[?options]. Repeatable."
    ),
)

# Option for adding automatic comments
COMMENT_OPTION = typer.Option(
    default=True,
    help="Add automatic comments when syncing files.",
)

sync_app = typer.Typer(
    name="sync",
    help="Synchronize file contents between paths.",
    no_args_is_help=True,
)


@sync_app.command(no_args_is_help=True)
def files(  # noqa: PLR0913
    src: str = SRC_ARGUMENT,
    dst: str = DST_ARGUMENT,
    *,
    dry_run: bool = DRY_RUN_OPTION,
    diff: bool = DIFF_OPTION,
    backup: bool = BACKUP_OPTION,
    binary: bool = BINARY_OPTION,
    encoding: str = ENCODING_OPTION,
    comment: bool = COMMENT_OPTION,
    section: str = SECTION_OPTION,
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
        comment: Whether to add automatic comments.
        section: Optional list of section mapping strings as accepted by --section.

    Raises:
        typer.Exit: When synchronization cannot be completed.
    """
    options = SyncOptions(
        dry_run=dry_run,
        show_diff=diff,
        backup=backup,
        allow_binary=binary,
        encoding=encoding,
        add_comments=comment,  # Add comments based on flag value
    )

    # Parse section mapping arguments if provided
    if section is not None:
        try:
            options.section_mappings = [parse_section_argument(section)]
        except SectionMappingError as error:
            typer.echo("Invalid section mapping: " + str(error), err=True)
            raise typer.Exit(code=2) from error

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
