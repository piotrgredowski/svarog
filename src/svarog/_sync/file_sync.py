from __future__ import annotations

import difflib
import hashlib
import secrets
import shutil
import string
import typing as t
from dataclasses import dataclass
from dataclasses import field
from datetime import datetime
from datetime import timezone
from io import StringIO
from pathlib import Path

if t.TYPE_CHECKING:
    from .section_mapping import SectionMapping
from ._exceptions import FileSyncError
from ._markdown import MarkdownAdapter
from ._markdown import parse_markdown_options
from .structure_adapter import get_adapter_class


@dataclass(slots=True)
class SyncResult:
    """Describe the outcome of a file synchronization."""

    changed: bool
    reason: str
    diff: str | None = None
    backup_path: Path | None = None


def _make_section_list() -> list[SectionMapping]:
    return []


@dataclass(slots=True)
class SyncOptions:
    """Runtime options for file synchronization."""

    dry_run: bool = False
    show_diff: bool = False
    backup: bool = False
    allow_binary: bool = False
    encoding: str = "utf-8"
    section_mappings: list[SectionMapping] = field(default_factory=_make_section_list)


def is_binary(path: Path, sample_bytes: int = 2048) -> bool:
    """Return ``True`` when ``path`` is detected as binary.

    Args:
        path: File whose content should be inspected.
        sample_bytes: Maximum number of bytes to inspect.

    Returns:
        Whether the file appears to be binary.

    Raises:
        FileSyncError: If the file cannot be read.
    """
    try:
        with path.open("rb") as buffer:
            chunk = buffer.read(sample_bytes)
    except OSError as error:  # pragma: no cover - surfaced upstream
        message = "Failed to read " + str(path) + ": " + str(error)
        raise FileSyncError(message) from error

    if not chunk:
        return False

    if b"\0" in chunk:
        return True

    try:
        chunk.decode("utf-8")
    except UnicodeDecodeError:
        return True

    return False


def read_text(path: Path, *, encoding: str) -> str:
    """Return textual content of ``path`` using ``encoding``.

    Args:
        path: File to read.
        encoding: Text encoding used for decoding.

    Returns:
        File contents as a string.

    Raises:
        FileSyncError: If the file cannot be read with the given encoding.
    """
    try:
        return path.read_text(encoding=encoding)
    except (OSError, UnicodeDecodeError) as error:
        message = "Failed to read " + str(path) + ": " + str(error)
        raise FileSyncError(message) from error


def compute_diff(
    src_text: str,
    dst_text: str,
    *,
    src_label: str,
    dst_label: str,
) -> str:
    """Return a unified diff between source and destination text.

    Args:
        src_text: Updated source text.
        dst_text: Original destination text.
        src_label: Label for the source file in diff headers.
        dst_label: Label for the destination file in diff headers.

    Returns:
        A unified diff string.
    """
    diff = difflib.unified_diff(
        dst_text.splitlines(keepends=True),
        src_text.splitlines(keepends=True),
        fromfile=src_label,
        tofile=dst_label,
    )
    return "".join(diff)


def ensure_backup(path: Path) -> Path:
    """Create and return a timestamped backup of ``path``.

    Args:
        path: File that should be backed up.

    Returns:
        Location of the backup file.

    Raises:
        FileSyncError: If the backup cannot be created.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_name = path.name + "." + timestamp + ".bak"
    backup_path = path.with_name(backup_name)
    try:
        shutil.copy2(path, backup_path)
    except (OSError, shutil.Error) as error:
        message = "Failed to create backup for " + str(path) + ": " + str(error)
        raise FileSyncError(message) from error
    return backup_path


def sync_files(
    source: Path | str,
    target: Path | str,
    *,
    options: SyncOptions | None = None,
) -> SyncResult:
    """Synchronize ``target`` so that it matches ``source``.

    Args:
    source: File whose content should be propagated.
    target: File that should receive the content.
    options: Runtime options toggling synchronization behavior.

    Returns:
        Result describing the synchronization outcome.

    Raises:
        FileSyncError: If validation fails or if the operation cannot complete.
    """
    resolved_options = options or SyncOptions()
    source_path, target_path = _validate_inputs(source, target)
    binary_mode, target_exists = _resolve_binary_mode(
        source_path,
        target_path,
        allow_binary=resolved_options.allow_binary,
    )

    if binary_mode:
        return _sync_binary(
            source_path,
            target_path,
            options=resolved_options,
            target_exists=target_exists,
        )

    return _sync_text(
        source_path,
        target_path,
        options=resolved_options,
        target_exists=target_exists,
    )


def _validate_inputs(source: Path | str, target: Path | str) -> tuple[Path, Path]:
    """Validate source and target paths before synchronization.

    Args:
        source: Candidate source file path.
        target: Candidate target file path.

    Returns:
        Validated source and target paths.

    Raises:
        FileSyncError: If validation fails.
    """
    source_path = Path(source)
    target_path = Path(target)
    source_resolved = source_path.resolve(strict=False)
    target_resolved = target_path.resolve(strict=False)

    if source_resolved == target_resolved:
        message = "Source and target paths must be different."
        raise FileSyncError(message)

    if not source_path.exists():
        message = "Source file not found: " + str(source_path)
        raise FileSyncError(message)

    if source_path.is_dir():
        message = "Source path is a directory: " + str(source_path)
        raise FileSyncError(message)

    if target_path.exists() and target_path.is_dir():
        message = "Target path is a directory: " + str(target_path)
        raise FileSyncError(message)

    return source_path, target_path


def _resolve_binary_mode(
    source: Path,
    target: Path,
    *,
    allow_binary: bool,
) -> tuple[bool, bool]:
    """Determine whether binary mode must be used.

    Args:
        source: Source file path.
        target: Target file path.
        allow_binary: Whether binary files are permitted.

    Returns:
        Tuple of ``(use_binary_mode, target_exists)``.

    Raises:
        FileSyncError: If binary content is detected without permission.
    """
    target_exists = target.exists()
    source_is_binary = is_binary(source)
    target_is_binary = target_exists and is_binary(target)

    if (source_is_binary or target_is_binary) and not allow_binary:
        message = "Binary file detected; pass --binary to allow."
        raise FileSyncError(message)

    return (source_is_binary or target_is_binary), target_exists


def _sync_binary(
    source: Path,
    target: Path,
    *,
    options: SyncOptions,
    target_exists: bool,
) -> SyncResult:
    """Synchronize files in binary mode.

    Args:
        source: Source file path.
        target: Target file path.
        options: Runtime synchronization options.
        target_exists: Whether the target already exists.

    Returns:
        Result of the synchronization.
    """
    src_bytes = source.read_bytes()
    dst_bytes = target.read_bytes() if target_exists else None

    if target_exists and dst_bytes == src_bytes:
        return SyncResult(changed=False, reason="already_in_sync")

    if options.dry_run:
        return SyncResult(changed=False, reason="dry_run")

    backup_path = ensure_backup(target) if options.backup and target_exists else None
    _ensure_parent_directory(target)
    target.write_bytes(src_bytes)

    reason = "target_updated" if target_exists else "target_created"
    return SyncResult(
        changed=True,
        reason=reason,
        diff=None,
        backup_path=backup_path,
    )


def _sync_text(
    source: Path,
    target: Path,
    *,
    options: SyncOptions,
    target_exists: bool,
) -> SyncResult:
    """Synchronize files in text mode.

    Args:
        source: Source file path.
        target: Target file path.
        options: Runtime synchronization options.
        target_exists: Whether the target already exists.

    Returns:
        Result of the synchronization.
    """
    # If section mappings are present, use structured section sync
    if getattr(options, "section_mappings", None):
        return _sync_structured_sections(
            source,
            target,
            options=options,
            target_exists=target_exists,
        )

    source_text = read_text(source, encoding=options.encoding)
    target_text = read_text(target, encoding=options.encoding) if target_exists else ""

    diff = None
    if options.show_diff:
        diff = compute_diff(
            source_text,
            target_text,
            src_label=source.name,
            dst_label=target.name,
        )

    if target_exists and source_text == target_text:
        return SyncResult(changed=False, reason="already_in_sync", diff=diff)

    if options.dry_run:
        return SyncResult(changed=False, reason="dry_run", diff=diff)

    backup_path = ensure_backup(target) if options.backup and target_exists else None
    _ensure_parent_directory(target)
    target.write_text(source_text, encoding=options.encoding)

    reason = "target_updated" if target_exists else "target_created"
    return SyncResult(
        changed=True,
        reason=reason,
        diff=diff,
        backup_path=backup_path,
    )


def _ensure_string_ends_with_newline(content: str) -> str:
    """Ensure that the given string ends with a newline character.

    Args:
        content: The input string.

    Returns:
        The input string, guaranteed to end with a newline character.
    """
    if not content.endswith("\n"):
        return content + "\n"
    return content


def _get_comment_content(
    *,
    warning_text: str,
) -> str:
    return warning_text


def _get_start_comment_content(
    *,
    source_file_path: Path,
    mapping: SectionMapping,
    section_id: str,
) -> str:
    warning_text = ". ".join(
        [
            f"Start of section {section_id}. It is auto-generated. Do not edit it",
            f"Source: '{source_file_path}'",
            f"Mapping: '{mapping.raw}'",
        ]
    )
    return _get_comment_content(warning_text=warning_text)


def _get_end_comment_content(
    *,
    section_id: str,
) -> str:
    warning_text = f"End of section {section_id}. It is auto-generated. Do not edit it."
    return _get_comment_content(warning_text=warning_text)


def _get_random_id(length: int) -> str:
    return "".join(secrets.choice(string.ascii_uppercase) for _ in range(length))


def _get_section_id(source_file_path: Path, target_file_path: Path, mapping_raw: str) -> str:
    """Generate a deterministic section ID."""
    hash_input = f"{source_file_path}{target_file_path}{mapping_raw}".encode()

    return hashlib.sha1(hash_input).hexdigest()[:8].upper()  # noqa: S324 - SHA1 is acceptable for non-cryptographic hash purposes


def _sync_structured_sections(  # noqa: C901,PLR0912,PLR0915 - function complexity accepted
    source: Path,
    target: Path,
    *,
    options: SyncOptions,
    target_exists: bool,
) -> SyncResult:
    """Synchronize only mapped sections between structured files (YAML, JSON, etc)."""
    if not options.section_mappings:
        # This should not be reached if called from _sync_text
        return SyncResult(changed=False, reason="no_sections_defined")

    src_adapter_class = get_adapter_class(options.section_mappings[0].src_adapter, source)
    src_adapter = src_adapter_class()

    dst_adapter_class = get_adapter_class(options.section_mappings[0].dst_adapter, target)
    dst_adapter = dst_adapter_class()

    try:
        with source.open(encoding=options.encoding) as f:
            src_data = src_adapter.load(f)
    except FileNotFoundError as exc:
        raise FileSyncError(path=source) from exc

    dst_data = None
    if target_exists:
        try:
            with target.open(encoding=options.encoding) as f:
                dst_data = dst_adapter.load(f)
        except FileNotFoundError:
            pass  # Not a problem, we can create it

    if dst_data is None:
        dst_data = {}

    # keep reference to original dst data for potential future use

    for mapping in options.section_mappings:
        try:
            value = src_adapter.get_section(src_data, mapping.src_path)
        except (KeyError, IndexError) as e:
            section_name = "".join(str(s.key) for s in mapping.src_path)
            msg = "Source section not found: " + section_name + ": " + str(e)
            raise FileSyncError(msg) from e

        # Check if destination adapter is markdown and parse render options
        if isinstance(dst_adapter, MarkdownAdapter):
            render_type, render_opts = parse_markdown_options(mapping.dst_options)

            # Add source section name to render options if needed
            if render_opts.get("include_source_section_name"):
                source_section_name = "".join(str(s.key) for s in mapping.src_path)
                render_opts["source_section_name"] = source_section_name

            dst_adapter.set_options(
                render_type=render_type,
                render_options=render_opts,
            )
            section_id = _get_section_id(source, target, mapping.raw)
            # MarkdownAdapter has extended set_section signature
            start_comment = _get_start_comment_content(
                source_file_path=source,
                mapping=mapping,
                section_id=section_id,
            )
            end_comment = _get_end_comment_content(
                section_id=section_id,
            )

            dst_adapter.set_section(
                data=t.cast("dict[str, object]", dst_data),
                path=mapping.dst_path,
                value=value,
                previous_value=start_comment,
                next_value=end_comment,
                create=mapping.create,
            )
        else:
            dst_adapter.set_section(dst_data, mapping.dst_path, value, create=mapping.create)

    new_dst_content = StringIO()
    dst_adapter.dump(dst_data, new_dst_content)
    new_dst_text = new_dst_content.getvalue()
    new_dst_text = _ensure_string_ends_with_newline(new_dst_text)

    old_dst_text = ""
    if target_exists:
        old_dst_text = target.read_text(encoding=options.encoding)

    diff = None
    if options.show_diff:
        diff = compute_diff(
            new_dst_text,
            old_dst_text,
            src_label=f"{source.name} (section)",
            dst_label=target.name,
        )

    if new_dst_text == old_dst_text:
        return SyncResult(changed=False, reason="already_in_sync", diff=diff)

    if options.dry_run:
        return SyncResult(changed=False, reason="dry_run", diff=diff)

    backup_path = ensure_backup(target) if options.backup and target_exists else None
    _ensure_parent_directory(target)
    target.write_text(new_dst_text, encoding=options.encoding)

    reason = "target_updated" if target_exists else "target_created"
    return SyncResult(
        changed=True,
        reason=reason,
        diff=diff,
        backup_path=backup_path,
    )


def _ensure_parent_directory(target: Path) -> None:
    """Ensure that the parent directory for ``target`` exists."""
    target.parent.mkdir(parents=True, exist_ok=True)
