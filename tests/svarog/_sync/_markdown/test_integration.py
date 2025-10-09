"""Integration tests for markdown sync functionality."""

from __future__ import annotations

import hashlib
import typing as t

from svarog._sync.file_sync import SyncOptions
from svarog._sync.file_sync import sync_files
from svarog._sync.section_mapping import parse_section_argument

if t.TYPE_CHECKING:
    from pathlib import Path


def test_yaml_to_markdown_sync_example_from_plan(tmp_path: Path) -> None:
    """Test the example from the implementation plan.

    This test verifies that we can sync YAML content to markdown sections
    with different rendering options (table, code block, etc.).
    """

    # Create source YAML file
    source_yaml = tmp_path / "source.yaml"
    source_yaml.write_text(
        """
inputs:
  - name: username
    description: Name of the user to use
    required: true
  - name: password
    description: Password for authentication
    required: true
  - name: verbose
    description: Enable verbose output
    required: false
outputs:
  - name: result
    description: Result of the operation
config:
  retries: 3
  timeout: 30
""".strip()
    )

    # Create target markdown file
    target_md = tmp_path / "target.md"
    target_before_md = target_md.with_name(target_md.stem + "_before" + target_md.suffix)
    target_text = """
# Documentation

This is the documentation file.

## Inputs of the action

Old inputs content that should be replaced.

## Outputs of the action

Old outputs content that should be replaced.

## Configuration

Old configuration content that should remain unchanged.

## Configuration with section name level

Old configuration content that should remain unchanged.

## Summary

Summary section that should remain unchanged.
""".strip()
    target_md.write_text(target_text)
    target_before_md.write_text(target_text)

    mappings = [
        parse_section_argument(
            "yaml:inputs->markdown(render_as=table):"
            '"Documentation"."Inputs of the action"?create=true'
        ),
        parse_section_argument(
            "yaml:outputs->markdown(render_as=table_with_headers_capitalized):"
            '"Documentation"."Outputs of the action"?create=true'
        ),
        parse_section_argument(
            "yaml:config->markdown(render_as=code_block):"
            '"Documentation"."Configuration"?create=true'
        ),
        parse_section_argument(
            "yaml:config->markdown(render_as=code_block(language=yaml,"
            'include_source_section_name=True)):"Documentation".'
            '"Configuration with section name level"?create=true'
        ),
    ]

    # Run sync commands
    options = SyncOptions(
        section_mappings=mappings,
        show_diff=True,
    )
    result = sync_files(str(source_yaml), str(target_md), options=options)
    assert result.changed

    # Read final markdown
    final_content = target_md.read_text()

    # Check each section
    for mapping in mappings:
        hash_input = f"{source_yaml}{target_md}{mapping.raw}".encode()

        section_id = hashlib.sha1(hash_input).hexdigest()[:8].upper()  # noqa: S324 - SHA1 is acceptable for non-cryptographic hash purposes
        assert f"Start of section {section_id}" in final_content
        assert f"End of section {section_id}" in final_content

    assert "| name" in final_content
    assert "description" in final_content
    assert "required |" in final_content
    assert "| username" in final_content
    assert "Name of the user to use" in final_content
    assert "True |" in final_content or "true |" in final_content
    assert "| password" in final_content
    assert "Password for authentication" in final_content
    assert "| verbose" in final_content
    assert "Enable verbose output" in final_content
    assert "False |" in final_content or "false |" in final_content

    assert "| Name" in final_content
    assert "Description |" in final_content
    assert "| result" in final_content
    assert "Result of the operation |" in final_content

    assert (
        r"""```yaml
retries: 3
timeout: 30
```"""
        in final_content
    )
    assert (
        r"""```yaml
config:
  retries: 3
  timeout: 30
```"""
        in final_content
    )


def test_markdown_render_types() -> None:
    """Test different markdown render types."""
    from svarog._sync._markdown import MarkdownRenderType
    from svarog._sync._markdown import get_renderer

    # Test table renderer
    data = [
        {"name": "test1", "value": "val1"},
        {"name": "test2", "value": "val2"},
    ]

    renderer = get_renderer(MarkdownRenderType.TABLE)
    result = renderer.render(data)
    assert "| name | value |" in result or "| value | name |" in result
    assert "| test1 | val1 |" in result or "| val1 | test1 |" in result

    # Test code block renderer
    code_renderer = get_renderer(MarkdownRenderType.CODE_BLOCK)
    config_data = {"key1": "value1", "key2": 42}
    result = code_renderer.render(config_data, language="yaml")
    assert "```yaml" in result
    assert "key1" in result


def test_parse_markdown_options() -> None:
    """Test parsing of markdown render options."""
    from svarog._sync._markdown import MarkdownRenderType
    from svarog._sync._markdown import parse_markdown_options

    # Test simple render type
    render_type, options = parse_markdown_options("render_as=table")
    assert render_type == MarkdownRenderType.TABLE
    assert options == {}

    # Test render type with options
    render_type, options = parse_markdown_options(
        "render_as=code_block(language=yaml,include_source_section_name=true)"
    )
    assert render_type == MarkdownRenderType.CODE_BLOCK
    assert options["language"] == "yaml"
    assert options["include_source_section_name"] is True

    # Test None
    render_type, options = parse_markdown_options(None)
    assert render_type == MarkdownRenderType.CODE_BLOCK
    assert options == {}


def test_section_mapping_with_markdown_options() -> None:
    """Test section mapping parser handles markdown adapter options."""
    from svarog._sync.section_mapping import parse_section_argument

    mapping = parse_section_argument(
        'yaml:inputs->markdown(render_as=table):"Documentation"."Inputs"'
    )

    assert mapping.src_adapter == "yaml"
    assert mapping.dst_adapter == "markdown"
    assert mapping.dst_options == "render_as=table"
    assert len(mapping.src_path) == 1
    assert mapping.src_path[0].key == "inputs"
    assert len(mapping.dst_path) == 2
    assert mapping.dst_path[0].key == "Documentation"
    assert mapping.dst_path[1].key == "Inputs"
