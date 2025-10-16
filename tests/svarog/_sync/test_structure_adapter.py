"""Tests for structure adapters."""

from io import StringIO
from pathlib import Path

import pytest

from svarog._sync._exceptions import FileSyncError
from svarog._sync.structure_adapter import YamlAdapter
from svarog._sync.structure_adapter import get_adapter_class


@pytest.fixture
def yaml_adapter() -> YamlAdapter:
    return YamlAdapter()


def test_yaml_adapter_load_valid(yaml_adapter: YamlAdapter):
    yaml_content = "key: value\nlist:\n  - item1\n  - item2"
    data = yaml_adapter.load(StringIO(yaml_content))
    assert data == {"key": "value", "list": ["item1", "item2"]}


def test_yaml_adapter_load_invalid(yaml_adapter: YamlAdapter):
    with pytest.raises(FileSyncError, match="Failed to parse YAML"):
        yaml_adapter.load(
            StringIO(
                """
key: value
- invalid_indent
""".strip()
            )
        )


def test_yaml_adapter_dump(yaml_adapter: YamlAdapter):
    data = {"key": "value", "list": ["item1", "item2"]}
    stream = StringIO()
    yaml_adapter.dump(data, stream)
    assert stream.getvalue() == "key: value\nlist:\n- item1\n- item2\n"


def test_get_adapter_by_name():
    adapter = get_adapter_class("yaml", Path("test.txt"))()
    assert isinstance(adapter, YamlAdapter)


def test_get_adapter_by_extension():
    adapter = get_adapter_class(None, Path("test.yaml"))()
    assert isinstance(adapter, YamlAdapter)
    adapter = get_adapter_class(None, Path("test.yml"))()
    assert isinstance(adapter, YamlAdapter)


def test_get_adapter_unsupported():
    with pytest.raises(FileSyncError, match="Unsupported adapter: foo"):
        get_adapter_class("foo", Path("test.txt"))()


def test_get_adapter_not_implemented():
    with pytest.raises(NotImplementedError, match="Adapter 'json' is not yet implemented"):
        get_adapter_class("json", Path("test.txt"))()


def test_get_adapter_no_inference():
    with pytest.raises(FileSyncError, match="Could not infer adapter"):
        get_adapter_class(None, Path("test.txt"))()
