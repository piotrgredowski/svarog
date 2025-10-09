"""Protocol and implementations for structure-aware file operations."""

from __future__ import annotations

import typing as t
from abc import ABC
from abc import abstractmethod

import yaml

from ._exceptions import FileSyncError

if t.TYPE_CHECKING:
    from pathlib import Path

    from _typeshed import SupportsRead
    from _typeshed import SupportsWrite

    from .section_mapping import PathSegment

T = t.TypeVar("T")


class StructureAdapter(ABC, t.Generic[T]):
    """Define a common interface for structured file format handlers."""

    def set_options(self, *args: t.Any, **kwargs: t.Any) -> None:  #  # noqa: ANN401
        del args, kwargs

    @abstractmethod
    def load(self, stream: SupportsRead[str] | SupportsRead[bytes]) -> T:
        """Parse a stream into a structured data object."""
        ...

    @abstractmethod
    def dump(self, data: T, stream: SupportsWrite[str]) -> None:
        """Serialize a structured data object into a stream."""
        ...

    def get_section(self, data: T, path: tuple[PathSegment, ...]) -> T:
        """Extract a subsection from a data structure."""
        # This default implementation can be overridden for format-specific needs
        current: T = data
        for segment in path:
            if segment.key == "*":
                return current
            if segment.key:
                if not isinstance(current, dict):
                    msg = f"Cannot access key '{segment.key}' on non-dict element."
                    raise FileSyncError(msg)
                current = current[segment.key]

            for index in segment.indices:
                if not isinstance(current, list):
                    msg = f"Cannot access index '{index}' on non-list element."
                    raise FileSyncError(msg)
                if index == "*":
                    # Wildcard, handled by caller or requires specific logic
                    msg = "Wildcard '*' must be handled by the synchronization logic."
                    raise NotImplementedError(msg)
                current = current[index]
        return current

    def set_section(  # noqa: C901,PLR0912 - complexity and branch count accepted for now
        self,
        data: T,
        path: tuple[PathSegment, ...],
        value: object,
        _previous_value: object | None = None,
        _next_value: object | None = None,
        *,
        create: bool = False,
    ) -> None:
        """Update a subsection in a data structure."""
        # This default implementation can be overridden
        current = data
        for i, segment in enumerate(path[:-1]):
            if segment.key:
                if not isinstance(current, dict):
                    msg = f"Cannot access key '{segment.key}' on non-dict element."
                    raise FileSyncError(msg)
                if segment.key not in current and create:
                    current[segment.key] = {} if path[i + 1].key else []
                current = current[segment.key]

            for index in segment.indices:
                if not isinstance(current, list):
                    msg = f"Cannot access index '{index}' on non-list element."
                    raise FileSyncError(msg)
                if index == "*":
                    msg = "Wildcard '*' is not supported in 'set_section'."
                    raise NotImplementedError(msg)
                if create and index >= len(current):
                    current.extend([None] * (index - len(current) + 1))
                current = current[index]

        last_segment = path[-1]
        if last_segment.key:
            if not isinstance(current, dict):
                msg = f"Cannot set key '{last_segment.key}' on non-dict element."
                raise FileSyncError(msg)
            current[last_segment.key] = value
        elif last_segment.indices:
            if not isinstance(current, list):
                msg = "Cannot set index on non-list element."
                raise FileSyncError(msg)
            if len(last_segment.indices) > 1:
                msg = "Multi-index set is not supported."
                raise NotImplementedError(msg)
            index = last_segment.indices[0]
            if index == "*":
                msg = "Wildcard '*' is not supported in 'set_section'."
                raise NotImplementedError(msg)
            if create and index >= len(current):
                current.extend([None] * (index - len(current) + 1))
            current[index] = value

    @abstractmethod
    def render_comment(self, text: str) -> str:
        raise NotImplementedError


class YamlAdapter(StructureAdapter[object]):
    """A structure adapter for YAML files."""

    def load(self, stream: SupportsRead[str] | SupportsRead[bytes]) -> object:
        """Parse a YAML stream safely."""
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as e:
            msg = f"Failed to parse YAML: {e}"
            raise FileSyncError(msg) from e

    def dump(self, data: object, stream: SupportsWrite[str]) -> None:
        """Dump data to a YAML stream, preserving order if possible."""
        yaml.dump(data, stream, sort_keys=False, allow_unicode=True)

    def render_comment(self, text: str) -> str:
        return f"# {text}"


def get_adapter_class(name: str | None, file_path: Path) -> type[StructureAdapter[object]]:
    """Return a structure adapter based on name or file extension."""
    from ._markdown import MarkdownAdapter

    adapter_map = {
        "yaml": YamlAdapter,
        "json": None,  # Placeholder for future JSON adapter
        "markdown": MarkdownAdapter,
    }
    if name:
        adapter_class = adapter_map.get(name)
        if adapter_class:
            return adapter_class
        if name not in adapter_map:
            msg = f"Unsupported adapter: {name}"
            raise FileSyncError(msg)
        msg = f"Adapter '{name}' is not yet implemented."
        raise NotImplementedError(msg)

    suffix = file_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        return YamlAdapter
    if suffix in {".md", ".markdown"}:
        return MarkdownAdapter
    if suffix == ".json":
        msg = "JSON adapter is not yet implemented."
        raise NotImplementedError(msg)

    msg = f"Could not infer adapter for file {file_path}. Please specify one (e.g., 'yaml:...')."
    raise FileSyncError(msg)
