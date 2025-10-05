from __future__ import annotations

import typing as t

import pytest

from svarog._sync._exceptions import FileSyncError
from svarog._sync.file_sync import SyncOptions
from svarog._sync.file_sync import SyncResult
from svarog._sync.file_sync import sync_files

if t.TYPE_CHECKING:
    from pathlib import Path


def write_text(path: Path, content: str, *, encoding: str = "utf-8") -> None:
    path.write_text(content, encoding=encoding)


def read_text(path: Path, *, encoding: str = "utf-8") -> str:
    return path.read_text(encoding=encoding)


def test_creates_target_when_missing(tmp_path: Path) -> None:
    src = tmp_path / "source.txt"
    dst = tmp_path / "target.txt"
    write_text(src, "hello")

    result = sync_files(src, dst, options=SyncOptions())

    assert isinstance(result, SyncResult)
    assert result.changed is True
    assert result.reason == "target_created"
    assert result.diff is None
    assert result.backup_path is None
    assert read_text(dst) == "hello"


def test_noop_when_already_in_sync(tmp_path: Path) -> None:
    src = tmp_path / "source.txt"
    dst = tmp_path / "target.txt"
    write_text(src, "content")
    write_text(dst, "content")

    result = sync_files(src, dst, options=SyncOptions())

    assert result.changed is False
    assert result.reason == "already_in_sync"
    assert result.diff is None
    assert result.backup_path is None
    assert read_text(dst) == "content"


def test_dry_run_shows_diff_without_modifying_target(tmp_path: Path) -> None:
    src = tmp_path / "source.txt"
    dst = tmp_path / "target.txt"
    write_text(src, "new\n")
    write_text(dst, "old\n")

    result = sync_files(src, dst, options=SyncOptions(dry_run=True, show_diff=True))

    assert result.changed is False
    assert result.reason == "dry_run"
    assert result.backup_path is None
    assert result.diff is not None
    assert "--- source.txt" in result.diff
    assert "+++ target.txt" in result.diff
    assert read_text(dst) == "old\n"


def test_overwrites_and_creates_backup(tmp_path: Path) -> None:
    src = tmp_path / "source.txt"
    dst = tmp_path / "target.txt"
    write_text(src, "updated")
    write_text(dst, "stale")

    result = sync_files(src, dst, options=SyncOptions(show_diff=True, backup=True))

    assert result.changed is True
    assert result.reason == "target_updated"
    assert result.diff is not None
    assert result.backup_path is not None
    assert result.backup_path.exists()
    assert read_text(result.backup_path) == "stale"
    assert read_text(dst) == "updated"


def test_blocks_binary_content_without_flag(tmp_path: Path) -> None:
    src = tmp_path / "source.bin"
    dst = tmp_path / "target.bin"
    src.write_bytes(b"\x00\x01")

    with pytest.raises(FileSyncError) as exc:
        sync_files(
            src,
            dst,
            options=SyncOptions(),
        )

    assert "Binary file detected" in str(exc.value)
    assert not dst.exists()


def test_allows_binary_content_when_flag_enabled(tmp_path: Path) -> None:
    src = tmp_path / "source.bin"
    dst = tmp_path / "target.bin"
    payload = b"\x00\x01\x02"
    src.write_bytes(payload)

    result = sync_files(src, dst, options=SyncOptions(allow_binary=True))

    assert result.changed is True
    assert result.reason == "target_created"
    assert result.backup_path is None
    assert dst.read_bytes() == payload


def test_raises_encoding_error_when_source_not_decodable(tmp_path: Path) -> None:
    src = tmp_path / "source.txt"
    dst = tmp_path / "target.txt"
    src.write_bytes(b"\xff\xfe")

    with pytest.raises(FileSyncError) as exc:
        sync_files(
            src,
            dst,
            options=SyncOptions(encoding="utf-8"),
        )

    assert "Binary file detected" in str(exc.value)
    assert not dst.exists()


def test_raises_when_source_and_target_are_same_path(tmp_path: Path) -> None:
    src = tmp_path / "same.txt"
    write_text(src, "data")

    with pytest.raises(FileSyncError) as exc:
        sync_files(
            src,
            src,
            options=SyncOptions(),
        )

    assert "must be different" in str(exc.value)
