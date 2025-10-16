"""Renderers for converting structured data to markdown format."""

from __future__ import annotations

import typing as t
from abc import ABC
from abc import abstractmethod
from enum import Enum

import yaml


class MarkdownRenderType(str, Enum):
    """Enum for different markdown render types."""

    CODE_BLOCK = "code_block"
    TABLE = "table"
    TABLE_WITH_HEADERS_CAPITALIZED = "table_with_headers_capitalized"
    TABLE_WITH_HEADERS_TITLE_CASED = "table_with_headers_title_cased"


class BaseMarkdownRenderer(ABC):
    """Base class for markdown renderers."""

    @abstractmethod
    def render(self, data: object, **_options: object) -> str:
        """Render data as a markdown table.

        Args:
            data: The data to render (must be a list of dicts).
            **_options: Options for rendering (unused).

        Returns:
            Rendered markdown table.

        Raises:
            TypeError: If data is not a list of dictionaries.
        """
        ...


class CodeBlockRenderer(BaseMarkdownRenderer):
    """Renderer for code blocks."""

    def render(self, data: object, **options: object) -> str:
        """Render data as a code block.

        Args:
            data: The data to render.
            **options: Options for rendering.
                language: Language identifier for syntax highlighting (default: yaml).
                include_source_section_name: Whether to include the section name (default: False).
                source_section_name: The source section name to include.

        Returns:
            Rendered code block.
        """
        opts = t.cast("dict[str, object]", options)
        language = t.cast("str", opts.get("language", "yaml"))
        include_source_section_name = t.cast("bool", opts.get("include_source_section_name", False))
        source_section_name = t.cast("str", opts.get("source_section_name", ""))

        if isinstance(data, dict | list):
            if include_source_section_name and isinstance(data, dict) and source_section_name:
                # Wrap data with section name
                wrapped_data = {source_section_name: data}
                content = yaml.dump(wrapped_data, sort_keys=False, allow_unicode=True).strip()
            else:
                content = yaml.dump(data, sort_keys=False, allow_unicode=True).strip()
        else:
            content = str(data)

        return f"```{language}\n{content}\n```"


class TableRenderer(BaseMarkdownRenderer):
    """Renderer for markdown tables."""

    def render(self, data: object, **__: object) -> str:
        """Render data as a markdown table.

        Args:
            data: The data to render (must be a list of dicts).

        Returns:
            Rendered markdown table.

        Raises:
            TypeError: If data is not a list of dictionaries.
        """
        if not isinstance(data, list):
            msg = "Table renderer expects a list of dictionaries"
            raise TypeError(msg)

        if not data:
            return ""

        first_item = data[0]
        if not all(isinstance(item, dict) for item in data):
            msg = "Table renderer expects all items to be dictionaries"
            raise TypeError(msg)

        original_headers = list(t.cast("dict[str, object]", first_item))
        headers = self._format_headers(original_headers)
        rows = [
            [str(t.cast("dict[str, object]", item).get(key, "")) for key in original_headers]
            for item in data
        ]

        return self._format_table(headers, rows)

    def _format_headers(self, headers: list[str]) -> list[str]:
        """Format table headers. This method can be overridden by subclasses."""
        return headers

    _LEFT_TABLE_BORDER = "| "
    _MIDDLE_TABLE_BORDER = " | "
    _RIGHT_TABLE_BORDER = " |"

    def _format_table(self, headers: list[str], rows: list[list[str]]) -> str:
        """Format headers and rows into a markdown table.

        Args:
            headers: Column headers.
            rows: Table rows.

        Returns:
            Formatted markdown table.
        """
        header_line = (
            self._LEFT_TABLE_BORDER
            + self._MIDDLE_TABLE_BORDER.join(headers)
            + self._RIGHT_TABLE_BORDER
        )
        separator = (
            self._LEFT_TABLE_BORDER
            + self._MIDDLE_TABLE_BORDER.join(["-" * len(h) for h in headers])
            + self._RIGHT_TABLE_BORDER
        )
        data_lines = [
            self._LEFT_TABLE_BORDER + self._MIDDLE_TABLE_BORDER.join(row) + self._RIGHT_TABLE_BORDER
            for row in rows
        ]

        return "\n".join([header_line, separator, *data_lines])


class TableWithHeadersCapitalizedRenderer(TableRenderer):
    """Renderer for tables with capitalized headers."""

    def _format_headers(self, headers: list[str]) -> list[str]:
        """Format table headers by capitalizing them."""
        return [h.capitalize() for h in headers]


class TableWithHeadersTitleCasedRenderer(TableRenderer):
    """Renderer for tables with title-cased headers."""

    def _format_headers(self, headers: list[str]) -> list[str]:
        """Format table headers by title-casing them."""
        return [h.title() for h in headers]


def get_renderer(render_type: MarkdownRenderType) -> BaseMarkdownRenderer:
    """Get a markdown renderer by type.

    Args:
        render_type: The type of renderer to get.

    Returns:
        An instance of the requested renderer.

    Raises:
        ValueError: If the render type is not supported.
    """
    renderer_map: dict[MarkdownRenderType, type[BaseMarkdownRenderer]] = {
        MarkdownRenderType.CODE_BLOCK: CodeBlockRenderer,
        MarkdownRenderType.TABLE: TableRenderer,
        MarkdownRenderType.TABLE_WITH_HEADERS_CAPITALIZED: TableWithHeadersCapitalizedRenderer,
        MarkdownRenderType.TABLE_WITH_HEADERS_TITLE_CASED: TableWithHeadersTitleCasedRenderer,
    }

    renderer_class = renderer_map.get(render_type)
    if renderer_class is None:
        msg = f"Unsupported render type: {render_type}"
        raise ValueError(msg)

    return renderer_class()
