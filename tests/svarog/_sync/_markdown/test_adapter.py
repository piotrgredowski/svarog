"""Test the markdown adapter."""

from __future__ import annotations

import typing as t
from textwrap import dedent

import pytest
import yaml

from svarog._sync import SyncOptions
from svarog._sync import sync_files
from svarog._sync.section_mapping import parse_section_argument

if t.TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def src_yaml_file(tmp_path: Path) -> Path:
    """Create a sample source YAML file."""
    content = {
        "info": {
            "title": "Test Title",
            "version": "1.0.0",
        },
        "data": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ],
    }
    file = tmp_path / "src.yaml"
    with file.open("w") as f:
        yaml.dump(content, f)
    return file


@pytest.fixture
def dst_md_file(tmp_path: Path) -> Path:
    """Create a sample destination Markdown file."""
    file = tmp_path / "dst.md"
    file.touch()
    return file


def test_sync_to_markdown_table(src_yaml_file: Path, dst_md_file: Path):
    """Test syncing a YAML section to a Markdown table."""
    mapping = parse_section_argument(
        "yaml:data -> markdown(render_as=table):data_section?create=true"
    )
    options = SyncOptions(section_mappings=[mapping])

    sync_files(src_yaml_file, dst_md_file, options=options)

    content = dst_md_file.read_text()

    assert "| name  | age |" in content or "| age | name |" in content
    assert "| Alice | 30  |" in content or "| 30 | Alice |" in content
    assert "| Bob   | 25  |" in content or "| 25 | Bob |" in content


def test_sync_to_markdown_code_block(src_yaml_file: Path, dst_md_file: Path):
    """Test syncing a YAML section to a Markdown code block."""
    mapping = parse_section_argument(
        "yaml:info -> markdown(render_as=code_block):info_section?create=true"
    )
    options = SyncOptions(section_mappings=[mapping])

    sync_files(src_yaml_file, dst_md_file, options=options)

    content = dst_md_file.read_text()
    expected_block = dedent(
        """
        ```yaml
        title: Test Title
        version: 1.0.0
        ```"""
    )
    assert expected_block in content
