"""Unit tests for section mapping argument parsing."""

import pytest

from svarog._sync.section_mapping import PathSegment
from svarog._sync.section_mapping import SectionMappingError
from svarog._sync.section_mapping import parse_section_argument


def test_parse_section_argument_basic() -> None:
    mapping = parse_section_argument("yaml:root.section->yaml:destination")

    assert mapping.src_adapter == "yaml"
    assert mapping.dst_adapter == "yaml"
    assert [segment.key for segment in mapping.src_path] == ["root", "section"]
    assert [segment.key for segment in mapping.dst_path] == ["destination"]
    assert mapping.create is False
    assert mapping.force is False


def test_parse_section_argument_with_options_and_indices() -> None:
    mapping = parse_section_argument("yaml:items[0][*]->json:collection?create=true&force=false")

    assert mapping.create is True
    assert mapping.force is False
    assert mapping.src_adapter == "yaml"
    assert mapping.dst_adapter == "json"
    assert mapping.src_path[0] == PathSegment(key="items", indices=(0,))
    assert mapping.src_path[1] == PathSegment(key=None, indices=("*",))
    assert mapping.dst_path[0] == PathSegment(key="collection")


def test_parse_section_argument_with_quoted_segments() -> None:
    mapping = parse_section_argument('yaml:"a.b"."c.d"->fm:front-matter')

    assert [segment.key for segment in mapping.src_path] == ["a.b", "c.d"]
    assert mapping.dst_adapter == "fm"
    assert mapping.dst_path == (PathSegment(key="front-matter"),)


def test_parse_section_argument_with_index_only_path() -> None:
    mapping = parse_section_argument("yaml:[0][-1]->yaml:target")

    assert mapping.src_path == (
        PathSegment(key=None, indices=(0,)),
        PathSegment(key=None, indices=(-1,)),
    )
    assert mapping.dst_path == (PathSegment(key="target"),)


def test_parse_section_argument_with_escaped_dot() -> None:
    mapping = parse_section_argument(r"yaml:a\.b->yaml:target")

    assert [segment.key for segment in mapping.src_path] == ["a.b"]
    assert mapping.dst_path == (PathSegment(key="target"),)


def test_parse_section_argument_with_escaped_quote() -> None:
    mapping = parse_section_argument(r"yaml:'a\'b'->yaml:dest")

    assert [segment.key for segment in mapping.src_path] == ["a'b"]
    assert mapping.dst_path == (PathSegment(key="dest"),)


@pytest.mark.parametrize(
    "argument",
    [
        "",
        "yaml:only_source",
        "yaml:->yaml:dest",
        "yaml:src->yaml:dest?unknown=1",
        "yaml:root.->yaml:dest",
        "yaml:root..child->yaml:dest",
        "yaml:src->yaml:dest?create=yes",
    ],
)
def test_parse_section_argument_errors(argument: str) -> None:
    with pytest.raises(SectionMappingError):
        parse_section_argument(argument)


def test_section_mapping_error_contains_code() -> None:
    with pytest.raises(SectionMappingError) as exc_info:
        parse_section_argument("")

    assert isinstance(exc_info.value, SectionMappingError)
    assert exc_info.value.code == "empty_mapping"
    assert str(exc_info.value)
