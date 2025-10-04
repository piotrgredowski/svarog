"""Utilities for parsing section mapping arguments used by the sync CLI."""

from __future__ import annotations

import re
import shlex
import typing as t
import urllib.parse
from dataclasses import dataclass
from enum import Enum

SECTION_SEPARATOR: t.Final[str] = "->"
OPTION_SEPARATOR: t.Final[str] = "?"
ESCAPE_CHARACTER: t.Final[str] = "\\"
SUPPORTED_OPTIONS: t.Final[frozenset[str]] = frozenset({"create", "force"})
SUPPORTED_ADAPTERS: t.Final[tuple[str, ...]] = ("yaml", "json", "fm")
_INDEX_PATTERN: t.Final[re.Pattern[str]] = re.compile(r"\[(?P<index>-?\d+|\*)\]")
_VALID_ADAPTER: t.Final[re.Pattern[str]] = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_MIN_QUOTED_LENGTH: t.Final[int] = 2


class ErrorCode(str, Enum):
    """Error codes for section mapping validation."""

    EMPTY_MAPPING = "empty_mapping"
    MISSING_PATHS = "missing_paths"
    EMPTY_OPTIONS = "empty_options"
    MISSING_SEPARATOR = "missing_separator"
    MISSING_SOURCE_OR_DEST = "missing_source_or_dest"
    EMPTY_ADAPTER = "empty_adapter"
    INVALID_ADAPTER = "invalid_adapter"
    UNSUPPORTED_ADAPTER = "unsupported_adapter"
    EMPTY_PATH_WITH_ADAPTER = "empty_path_with_adapter"
    UNSUPPORTED_OPTION = "unsupported_option"
    INVALID_BOOL = "invalid_bool"
    EMPTY_PATH = "empty_path"
    EMPTY_SEGMENT = "empty_segment"
    EMPTY_INDEX_SEGMENT = "empty_index_segment"
    MISSING_SEGMENT = "missing_segment"
    DANGLING_ESCAPE = "dangling_escape"
    UNTERMINATED_QUOTE = "unterminated_quote"
    EMPTY_SEGMENT_KEY = "empty_segment_key"
    UNSUPPORTED_INDEX = "unsupported_index"
    INVALID_INDEX = "invalid_index"
    DANGLING_KEY_ESCAPE = "dangling_key_escape"


_ERROR_MESSAGES: t.Final[dict[ErrorCode, str]] = {
    ErrorCode.EMPTY_MAPPING: "Section mapping cannot be empty.",
    ErrorCode.MISSING_PATHS: "Section mapping must include a source and destination path.",
    ErrorCode.EMPTY_OPTIONS: "Section mapping options cannot be empty.",
    ErrorCode.MISSING_SEPARATOR: "Section mapping must contain '" + SECTION_SEPARATOR + "'.",
    ErrorCode.MISSING_SOURCE_OR_DEST: (
        "Section mapping must include both source and destination paths."
    ),
    ErrorCode.EMPTY_ADAPTER: "Adapter prefix cannot be empty.",
    ErrorCode.INVALID_ADAPTER: "Invalid adapter identifier: {detail}",
    ErrorCode.UNSUPPORTED_ADAPTER: "Unsupported adapter: {detail}",
    ErrorCode.EMPTY_PATH_WITH_ADAPTER: "Path cannot be empty when adapter is specified.",
    ErrorCode.UNSUPPORTED_OPTION: "Unsupported option: {detail}",
    ErrorCode.INVALID_BOOL: "Invalid boolean value for {detail}.",
    ErrorCode.EMPTY_PATH: "Path cannot be empty.",
    ErrorCode.EMPTY_SEGMENT: "Path segment cannot be empty.",
    ErrorCode.EMPTY_INDEX_SEGMENT: "Index-only segment must include an index.",
    ErrorCode.MISSING_SEGMENT: "Path must contain at least one segment.",
    ErrorCode.DANGLING_ESCAPE: "Path cannot end with an incomplete escape sequence.",
    ErrorCode.UNTERMINATED_QUOTE: "Unterminated quoted segment in path.",
    ErrorCode.EMPTY_SEGMENT_KEY: "Path segment key cannot be empty.",
    ErrorCode.UNSUPPORTED_INDEX: "Unsupported index token: {detail}",
    ErrorCode.INVALID_INDEX: "Invalid index value: {detail}",
    ErrorCode.DANGLING_KEY_ESCAPE: "Key cannot end with an escape character.",
}


class SectionMappingError(ValueError):
    """Raise when a section mapping argument is invalid."""

    def __init__(self, code: ErrorCode, *, detail: str | None = None) -> None:
        template = _ERROR_MESSAGES.get(code, "Unknown section mapping error.")
        if "{detail}" in template:
            rendered = template.format(detail=detail or "")
        elif detail is None:
            rendered = template
        else:
            rendered = template + detail
        super().__init__(rendered)
        self.code = code.value
        self.detail = detail


IndexToken = int | str


@dataclass(slots=True)
class PathSegment:
    """Represent a single traversal step within a structured document."""

    key: str | None
    indices: tuple[IndexToken, ...] = ()

    def __post_init__(self) -> None:
        if self.key is not None and self.key == "":
            raise SectionMappingError(ErrorCode.EMPTY_SEGMENT_KEY)
        for index in self.indices:
            if isinstance(index, str) and index != "*":
                raise SectionMappingError(ErrorCode.UNSUPPORTED_INDEX, detail=index)


@dataclass(slots=True)
class SectionMapping:
    """Describe a mapping from a source path to a destination path."""

    raw: str
    src_adapter: str | None
    src_path: tuple[PathSegment, ...]
    dst_adapter: str | None
    dst_path: tuple[PathSegment, ...]
    create: bool = False
    force: bool = False


def parse_section_argument(argument: str) -> SectionMapping:
    """Parse a CLI mapping string into a SectionMapping instance."""
    if not argument:
        raise SectionMappingError(ErrorCode.EMPTY_MAPPING)

    mapping_part, option_part = _split_options(argument)
    src_token, dst_token = _split_mapping(mapping_part)
    src_adapter, src_path_token = _split_adapter(src_token)
    dst_adapter, dst_path_token = _split_adapter(dst_token)

    src_path = _parse_path(src_path_token)
    dst_path = _parse_path(dst_path_token)

    options = _parse_options(option_part)

    return SectionMapping(
        raw=argument,
        src_adapter=src_adapter,
        src_path=src_path,
        dst_adapter=dst_adapter,
        dst_path=dst_path,
        create=options.get("create", False),
        force=options.get("force", False),
    )


def _split_options(argument: str) -> tuple[str, str | None]:
    if OPTION_SEPARATOR not in argument:
        return argument, None

    mapping_part, option_part = argument.split(OPTION_SEPARATOR, 1)
    if not mapping_part:
        raise SectionMappingError(ErrorCode.MISSING_PATHS)
    if not option_part:
        raise SectionMappingError(ErrorCode.EMPTY_OPTIONS)
    return mapping_part, option_part


def _split_mapping(mapping_part: str) -> tuple[str, str]:
    if SECTION_SEPARATOR not in mapping_part:
        raise SectionMappingError(ErrorCode.MISSING_SEPARATOR)

    src_token, dst_token = mapping_part.split(SECTION_SEPARATOR, 1)
    src_token = src_token.strip()
    dst_token = dst_token.strip()
    if not src_token or not dst_token:
        raise SectionMappingError(ErrorCode.MISSING_SOURCE_OR_DEST)
    return src_token, dst_token


def _split_adapter(token: str) -> tuple[str | None, str]:
    if ":" not in token:
        return None, token.strip()

    adapter, path = token.split(":", 1)
    adapter = adapter.strip()
    path = path.strip()

    if not adapter:
        raise SectionMappingError(ErrorCode.EMPTY_ADAPTER)
    if not _VALID_ADAPTER.match(adapter):
        raise SectionMappingError(ErrorCode.INVALID_ADAPTER, detail=adapter)
    if adapter not in SUPPORTED_ADAPTERS:
        raise SectionMappingError(ErrorCode.UNSUPPORTED_ADAPTER, detail=adapter)
    if not path:
        raise SectionMappingError(ErrorCode.EMPTY_PATH_WITH_ADAPTER)

    return adapter, path


def _parse_options(option_part: str | None) -> dict[str, bool]:
    if option_part is None:
        return {}

    parsed: dict[str, bool] = {}
    for key, value in urllib.parse.parse_qsl(option_part, keep_blank_values=True):
        if key not in SUPPORTED_OPTIONS:
            raise SectionMappingError(ErrorCode.UNSUPPORTED_OPTION, detail=key)
        parsed[key] = _parse_bool(value, key)
    return parsed


def _parse_bool(value: str, key: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    detail = key + "=" + value
    raise SectionMappingError(ErrorCode.INVALID_BOOL, detail=detail)


def _parse_path(path: str) -> tuple[PathSegment, ...]:
    if not path:
        raise SectionMappingError(ErrorCode.EMPTY_PATH)

    tokens = _split_segments(path)
    segments: list[PathSegment] = []
    for token in tokens:
        segments.extend(_parse_segment(token))
    if not segments:
        raise SectionMappingError(ErrorCode.MISSING_SEGMENT)
    return tuple(segments)


def _split_segments(path: str) -> list[str]:
    lexer = shlex.shlex(path, posix=True, punctuation_chars=".")
    lexer.commenters = ""
    lexer.escape = ESCAPE_CHARACTER
    lexer.escapedquotes = "\"'"

    segments: list[str] = []
    buffer: list[str] = []

    try:
        for piece in lexer:
            if piece and set(piece) == {"."}:
                for _ in piece:
                    if not buffer:
                        raise SectionMappingError(ErrorCode.EMPTY_SEGMENT)
                    segments.append("".join(buffer))
                    buffer.clear()
                continue
            buffer.append(piece)
    except ValueError as error:  # shlex errors such as unterminated quotes
        message = str(error)
        error_code = (
            ErrorCode.UNTERMINATED_QUOTE
            if "No closing quotation" in message
            else ErrorCode.DANGLING_ESCAPE
        )
        raise SectionMappingError(error_code) from error

    if not buffer and _ends_with_unescaped_delimiter(path):
        raise SectionMappingError(ErrorCode.EMPTY_SEGMENT)

    if buffer:
        segments.append("".join(buffer))

    return segments


def _ends_with_unescaped_delimiter(path: str) -> bool:
    if not path or path[-1] != ".":
        return False

    escape = False
    for char in reversed(path[:-1]):
        if char == ESCAPE_CHARACTER:
            escape = not escape
            continue
        break
    return not escape


def _parse_segment(token: str) -> list[PathSegment]:
    if not token:
        raise SectionMappingError(ErrorCode.EMPTY_SEGMENT)

    key_raw, index_tokens = _extract_key_and_indices(token)
    key = _clean_key(key_raw)
    index_values = tuple(_parse_index(raw) for raw in index_tokens)

    return _build_segments(key, index_values)


def _build_segments(key: str | None, index_values: tuple[IndexToken, ...]) -> list[PathSegment]:
    if key is not None:
        return _segments_with_key(key, index_values)
    return _segments_without_key(index_values)


def _segments_with_key(key: str, index_values: tuple[IndexToken, ...]) -> list[PathSegment]:
    if not index_values:
        return [PathSegment(key=key)]

    head, *tail = index_values
    segments = [PathSegment(key=key, indices=(head,))]
    segments.extend(PathSegment(key=None, indices=(value,)) for value in tail)
    return segments


def _segments_without_key(index_values: tuple[IndexToken, ...]) -> list[PathSegment]:
    if not index_values:
        raise SectionMappingError(ErrorCode.EMPTY_INDEX_SEGMENT)
    return [PathSegment(key=None, indices=(value,)) for value in index_values]


def _extract_key_and_indices(token: str) -> tuple[str | None, list[str]]:
    matches = list(_INDEX_PATTERN.finditer(token))
    if not matches:
        return token, []

    first = matches[0]
    key_part = token[: first.start()]
    indices_raw = [match.group("index") for match in matches]

    if key_part == "":
        return None, indices_raw
    return key_part, indices_raw


def _clean_key(key: str | None) -> str | None:
    if key is None:
        return None

    unescaped = _unescape_key(key)
    has_min_length = len(unescaped) >= _MIN_QUOTED_LENGTH
    if has_min_length and unescaped[0] == unescaped[-1] and unescaped[0] in {'"', "'"}:
        return unescaped[1:-1]
    return unescaped


def _parse_index(raw: str) -> IndexToken:
    if raw == "*":
        return raw
    try:
        return int(raw)
    except ValueError as error:  # pragma: no cover - regex guards this
        raise SectionMappingError(ErrorCode.INVALID_INDEX, detail=raw) from error


def _unescape_key(key: str) -> str:
    result: list[str] = []
    escape = False
    for char in key:
        if escape:
            result.append(char)
            escape = False
            continue
        if char == ESCAPE_CHARACTER:
            escape = True
            continue
        result.append(char)
    if escape:
        raise SectionMappingError(ErrorCode.DANGLING_KEY_ESCAPE)

    return "".join(result)
