"""Markdown structure adapter for syncing content with markdown files."""

from __future__ import annotations

import re
import typing as t

import mistune

if t.TYPE_CHECKING:
    from _typeshed import SupportsRead
    from _typeshed import SupportsWrite

    from svarog._sync.section_mapping import PathSegment

from svarog._sync._exceptions import FileSyncError
from svarog._sync.structure_adapter import StructureAdapter

from ._renderers import MarkdownRenderType
from ._renderers import get_renderer


class MarkdownAdapter(StructureAdapter[dict[str, object]]):
    """Structure adapter for Markdown files with section navigation."""

    def render_comment(self, text: str) -> str:
        return f"<!-- {text} -->"

    def set_options(
        self,
        *args: t.Any,  #  # noqa: ANN401
        render_type: MarkdownRenderType | None = None,
        render_options: dict[str, object] | None = None,
        **kwargs: t.Any,  #  # noqa: ANN401
    ) -> None:
        del args, kwargs

        self._render_type = render_type or MarkdownRenderType.CODE_BLOCK
        self._render_options = render_options or {}

    def load(self, stream: SupportsRead[str] | SupportsRead[bytes]) -> dict[str, object]:
        """Parse a markdown stream into a hierarchical structure."""
        try:
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
        except Exception as error:
            msg = f"Failed to read markdown stream: {error}"
            raise FileSyncError(msg) from error

        try:
            markdown_ast = mistune.create_markdown(renderer=None)(content)
            return self._build_structure(markdown_ast, content)
        except Exception as error:
            msg = f"Failed to parse markdown: {error}"
            raise FileSyncError(msg) from error

    def dump(self, data: dict[str, object], stream: SupportsWrite[str]) -> None:
        """Serialize markdown structure to a stream."""
        try:
            content = self._render_structure(data)
            stream.write(content)
        except Exception as error:
            msg = f"Failed to serialize markdown: {error}"
            raise FileSyncError(msg) from error

    def _build_structure(
        self, ast: list[dict[str, object]], original_content: str
    ) -> dict[str, object]:
        """Build a hierarchical structure from markdown AST."""
        structure: dict[str, object] = {"_content": [], "_original": original_content}
        current_section: list[str] = []
        section_stack: list[tuple[int, list[str]]] = []

        for node in ast:
            if not isinstance(node, dict):
                continue

            node_type = node.get("type")

            if node_type == "heading":
                attrs = node.get("attrs", {})
                level = int(t.cast("int", attrs.get("level", 1))) if isinstance(attrs, dict) else 1
                text = self._extract_heading_text(node)

                # Pop sections from stack that are at same or deeper level
                while section_stack and section_stack[-1][0] >= level:
                    section_stack.pop()

                # Build path for this heading
                current_section = section_stack[-1][1] + [text] if section_stack else [text]

                section_stack.append((level, current_section))

                # Initialize section in structure with level
                self._ensure_section_exists(structure=structure, path=current_section, level=level)
            elif current_section:
                # Add content to current section
                section_data = self._get_section_data(structure, current_section)
                if "_content" not in section_data:
                    section_data["_content"] = []
                t.cast("list[dict[str, object]]", section_data["_content"]).append(node)
            else:
                # Root level content
                t.cast("list[dict[str, object]]", structure["_content"]).append(node)

        return structure

    def _extract_heading_text(self, heading_node: dict[str, object]) -> str:
        """Extract plain text from a heading node."""
        children = heading_node.get("children", [])
        if not isinstance(children, list):
            return ""

        text_parts: list[str] = []
        for child in children:
            if isinstance(child, dict) and child.get("type") == "text":
                raw = child.get("raw", "")
                if isinstance(raw, str):
                    text_parts.append(raw)
            elif isinstance(child, str):
                text_parts.append(child)

        return "".join(text_parts)

    def _ensure_section_exists(
        self, *, structure: dict[str, object], path: list[str], level: int | None = None
    ) -> None:
        """Ensure a section exists in the structure at the given path."""
        current = structure
        for i, segment in enumerate(path):
            if segment not in current:
                section_data: dict[str, object] = {"_content": []}
                # Store level only for the final segment (the actual heading)
                if level is not None and i == len(path) - 1:
                    section_data["_level"] = level
                current[segment] = section_data
            current = t.cast("dict[str, object]", current[segment])

    def _get_section_data(self, structure: dict[str, object], path: list[str]) -> dict[str, object]:
        """Get section data at the given path."""
        current = structure
        for segment in path:
            if segment not in current:
                msg = f"Section not found: {'.'.join(path)}"
                raise FileSyncError(msg)
            current = t.cast("dict[str, object]", current[segment])

        return t.cast("dict[str, object]", current)

    def _render_structure(self, structure: dict[str, object], *, level: int = 0) -> str:
        """Render structure back to markdown."""
        parts: list[str] = []

        # Render root content first
        if "_content" in structure:
            content_nodes = t.cast("list[dict[str, object]]", structure["_content"])
            for node in content_nodes:
                rendered = self._render_node(node)
                if rendered:
                    parts.append(rendered)

        # Render subsections
        for key, value in structure.items():
            if key in ("_content", "_original", "_level"):
                continue

            if isinstance(value, dict):
                # Render heading using stored level if available
                stored_level = value.get("_level")
                if isinstance(stored_level, int):
                    heading_level = stored_level
                elif level > 0:
                    heading_level = level
                else:
                    heading_level = 1

                parts.append("#" * heading_level + " " + key)

                # Recursively render subsection
                subsection_content = self._render_structure(value, level=level + 1)
                if subsection_content:
                    parts.append(subsection_content)

        return "\n\n".join(parts)

    def _render_node(self, node: dict[str, object]) -> str:
        """Render a single AST node to markdown."""
        node_type = node.get("type")

        if node_type == "rendered":
            # Custom node type for rendered data from YAML
            return self._render_data_node(node)
        if node_type == "paragraph":
            return self._render_paragraph(node)
        if node_type == "code_block":
            return self._render_code_block(node)
        if node_type == "comment":
            return self._render_comment(node)
        if node_type == "blank_line":
            return ""

        # Fallback
        return ""

    def _render_data_node(self, node: dict[str, object]) -> str:
        """Render a data node with specified renderer."""
        data = node.get("data")
        render_type = node.get("render_type", MarkdownRenderType.CODE_BLOCK)
        render_options = node.get("render_options", {})

        if isinstance(render_type, str):
            render_type = MarkdownRenderType(render_type)

        renderer = get_renderer(render_type)
        opts = t.cast("dict[str, object]", render_options) if render_options else {}
        return renderer.render(data, **opts)

    def _render_paragraph(self, node: dict[str, object]) -> str:
        """Render a paragraph node."""
        children = node.get("children", [])
        if not isinstance(children, list):
            return ""

        text_parts: list[str] = []
        for child in children:
            if isinstance(child, dict) and child.get("type") == "text":
                raw = child.get("raw", "")
                if isinstance(raw, str):
                    text_parts.append(raw)

        return "".join(text_parts)

    def _render_code_block(self, node: dict[str, object]) -> str:
        """Render a code block node."""
        raw = node.get("raw", "")
        info = node.get("attrs", {})
        lang = ""
        if isinstance(info, dict):
            lang = info.get("info", "")
        code = raw if isinstance(raw, str) else ""
        return f"```{lang}\n{code.rstrip()}\n```"

    def _render_comment(self, node: dict[str, object]) -> str:
        text = node.get("data", "")
        return f"<!-- {text} -->" if text else ""

    def get_section(
        self, data: dict[str, object], path: tuple[PathSegment, ...]
    ) -> dict[str, object]:
        """Extract a subsection from markdown structure."""
        current: dict[str, object] = data

        for segment in path:
            if segment.key is None:
                msg = "Markdown adapter requires named sections (keys)"
                raise FileSyncError(msg)

            if segment.key not in current:
                msg = f"Section '{segment.key}' not found in markdown"
                raise FileSyncError(msg)

            current = t.cast("dict[str, object]", current[segment.key])

        return current

    def set_section(  # noqa: C901,PLR0912,PLR0913 - complexity and branch count accepted for now
        self,
        data: dict[str, object],
        path: tuple[PathSegment, ...],
        value: object,
        previous_value: object | None = None,
        next_value: object | None = None,
        *,
        create: bool = False,
    ) -> None:
        """Update a subsection in markdown structure."""
        if not path:
            msg = "Cannot set empty path"
            raise FileSyncError(msg)

        current: dict[str, object] = data

        # Navigate to parent of target
        for segment in path[:-1]:
            if segment.key is None:
                msg = "Markdown adapter requires named sections"
                raise FileSyncError(msg)

            if segment.key not in current:
                if create:
                    current[segment.key] = {"_content": []}
                else:
                    msg = f"Section '{segment.key}' not found"
                    raise FileSyncError(msg)

            current = t.cast("dict[str, object]", current[segment.key])

        # Set the final value
        last_segment = path[-1]
        if last_segment.key is None:
            msg = "Markdown adapter requires named sections"
            raise FileSyncError(msg)

        # Ensure the section exists
        if last_segment.key not in current:
            if create:
                # Create new section without level (will default to level 1 or parent+1)
                current[last_segment.key] = {"_content": []}
            else:
                msg = f"Section '{last_segment.key}' not found"
                raise FileSyncError(msg)

        target_section = t.cast("dict[str, object]", current[last_segment.key])

        nodes_to_be_added: list[object] = []
        # Render the value as markdown content

        if isinstance(value, dict | list) and self._render_type:
            rendered_node = {
                "type": "rendered",
                "data": value,
                "render_type": self._render_type.value,
                "render_options": self._render_options or {},
            }

            nodes_to_be_added = [rendered_node]

        else:
            # Just store the value directly
            nodes_to_be_added = [value] if not isinstance(value, list) else value
        if previous_value:
            nodes_to_be_added.insert(0, {"type": "comment", "data": previous_value})
        if next_value:
            nodes_to_be_added.append({"type": "comment", "data": next_value})
        target_section["_content"] = nodes_to_be_added


def parse_markdown_options(options_str: str | None) -> tuple[MarkdownRenderType, dict[str, object]]:
    """Parse markdown rendering options from section mapping."""
    if not options_str:
        return MarkdownRenderType.CODE_BLOCK, {}

    # Parse render_as parameter
    match = re.match(r"render_as=(\w+)(?:\((.*)\))?", options_str)
    if not match:
        msg = f"Invalid markdown options: {options_str}"
        raise FileSyncError(msg)

    render_type_str = match.group(1)
    params_str = match.group(2) or ""

    # Convert render type string to enum
    try:
        render_type = MarkdownRenderType(render_type_str)
    except ValueError as error:
        msg = f"Unknown render type: {render_type_str}"
        raise FileSyncError(msg) from error

    # Parse parameters
    render_options: dict[str, object] = {}
    if params_str:
        for param in params_str.split(","):
            key_value = param.strip().split("=", 1)
            if len(key_value) == 2:  # noqa: PLR2004 - simple length check
                key = key_value[0].strip()
                value = key_value[1].strip()
                # Parse boolean values
                if value.lower() == "true":
                    render_options[key] = True
                elif value.lower() == "false":
                    render_options[key] = False
                else:
                    render_options[key] = value

    return render_type, render_options
