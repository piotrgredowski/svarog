"""Tests for JSON tool functionality."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from svarog._tools.json_tool import json_app
from svarog._tools.json_tool import json_to_xml

runner = CliRunner()


class TestJSONTool:
    """Test cases for JSON tool commands."""

    def test_format_command_with_valid_json(self) -> None:
        """Test format command with valid JSON input."""
        test_json = '{"name":"test","value":123}'
        expected = '{\n  "name": "test",\n  "value": 123\n}'

        result = runner.invoke(json_app, ["format"], input=test_json)

        assert result.exit_code == 0
        assert result.stdout.strip() == expected

    def test_format_command_with_file(self) -> None:
        """Test format command with file input."""
        test_json = '{"name":"test","value":123}'
        expected = '{\n  "name": "test",\n  "value": 123\n}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(test_json)
            f.flush()

            result = runner.invoke(json_app, ["format", f.name])

            assert result.exit_code == 0
            assert result.stdout.strip() == expected

            Path(f.name).unlink()

    def test_format_command_with_custom_indent(self) -> None:
        """Test format command with custom indentation."""
        test_json = '{"name":"test","value":123}'
        expected = '{\n    "name": "test",\n    "value": 123\n}'

        result = runner.invoke(json_app, ["format", "--indent", "4"], input=test_json)

        assert result.exit_code == 0
        assert result.stdout.strip() == expected

    def test_format_command_with_output_file(self) -> None:
        """Test format command with output file."""
        test_json = '{"name":"test","value":123}'
        expected = '{\n  "name": "test",\n  "value": 123\n}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as output_file:
            output_path = output_file.name

        result = runner.invoke(json_app, ["format", "--output", output_path], input=test_json)

        assert result.exit_code == 0
        assert "Output written to" in result.stdout

        output_content = Path(output_path).read_text(encoding="utf-8")
        assert output_content.strip() == expected

        Path(output_path).unlink()

    def test_format_command_with_invalid_json(self) -> None:
        """Test format command with invalid JSON."""
        invalid_json = '{"name": "test", "value":}'

        result = runner.invoke(json_app, ["format"], input=invalid_json)

        assert result.exit_code == 1
        assert "Invalid JSON" in result.stdout or "Invalid JSON" in result.stderr

    def test_validate_command_with_valid_json(self) -> None:
        """Test validate command with valid JSON."""
        test_json = '{"name":"test","value":123}'

        result = runner.invoke(json_app, ["validate"], input=test_json)

        assert result.exit_code == 0
        assert "Valid JSON" in result.stdout

    def test_validate_command_with_invalid_json(self) -> None:
        """Test validate command with invalid JSON."""
        invalid_json = '{"name": "test", "value":}'

        result = runner.invoke(json_app, ["validate"], input=invalid_json)

        assert result.exit_code == 1
        assert "Invalid JSON" in result.stdout or "Invalid JSON" in result.stderr

    def test_minify_command(self) -> None:
        """Test minify command."""
        test_json = '{\n  "name": "test",\n  "value": 123\n}'
        expected = '{"name":"test","value":123}'

        result = runner.invoke(json_app, ["minify"], input=test_json)

        assert result.exit_code == 0
        assert result.stdout.strip() == expected

    def test_minify_command_with_output_file(self) -> None:
        """Test minify command with output file."""
        test_json = '{\n  "name": "test",\n  "value": 123\n}'
        expected = '{"name":"test","value":123}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as output_file:
            output_path = output_file.name

        result = runner.invoke(json_app, ["minify", "--output", output_path], input=test_json)

        assert result.exit_code == 0
        assert "Output written to" in result.stdout

        output_content = Path(output_path).read_text(encoding="utf-8")
        assert output_content.strip() == expected

        Path(output_path).unlink()

    def test_to_yaml_command(self) -> None:
        """Test to-yaml command."""
        test_json = '{"name":"test","value":123}'

        result = runner.invoke(json_app, ["to-yaml"], input=test_json)

        assert result.exit_code == 0

        # Parse the output to verify it's valid YAML
        yaml_data = yaml.safe_load(result.stdout)
        assert yaml_data == {"name": "test", "value": 123}

    def test_to_yaml_command_with_output_file(self) -> None:
        """Test to-yaml command with output file."""
        test_json = '{"name":"test","value":123}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as output_file:
            output_path = output_file.name

        result = runner.invoke(json_app, ["to-yaml", "--output", output_path], input=test_json)

        assert result.exit_code == 0
        assert "Output written to" in result.stdout

        output_content = Path(output_path).read_text(encoding="utf-8")
        yaml_data = yaml.safe_load(output_content)
        assert yaml_data == {"name": "test", "value": 123}

        Path(output_path).unlink()

    def test_to_xml_command_with_object(self) -> None:
        """Test to-xml command with JSON object."""
        test_json = '{"name":"test","value":123}'
        expected_root = "root"

        result = runner.invoke(json_app, ["to-xml", "--root-name", expected_root], input=test_json)

        assert result.exit_code == 0

        # Parse the output to verify it's valid XML
        xml_data = result.stdout.strip()
        assert xml_data.startswith(f"<{expected_root}>")
        assert xml_data.endswith(f"</{expected_root}>")
        assert "<name>test</name>" in xml_data
        assert "<value>123</value>" in xml_data

    def test_to_xml_command_with_array(self) -> None:
        """Test to-xml command with JSON array."""
        test_json = "[1, 2, 3]"
        expected_root = "data"

        result = runner.invoke(json_app, ["to-xml", "--root-name", expected_root], input=test_json)

        assert result.exit_code == 0

        # Parse the output to verify it's valid XML
        xml_data = result.stdout.strip()
        assert xml_data.startswith(f"<{expected_root}>")
        assert xml_data.endswith(f"</{expected_root}>")
        assert "<item>1</item>" in xml_data
        assert "<item>2</item>" in xml_data
        assert "<item>3</item>" in xml_data

    def test_to_xml_command_with_output_file(self) -> None:
        """Test to-xml command with output file."""
        test_json = '{"name":"test","value":123}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as output_file:
            output_path = output_file.name

        result = runner.invoke(json_app, ["to-xml", "--output", output_path], input=test_json)

        assert result.exit_code == 0
        assert "Output written to" in result.stdout

        output_content = Path(output_path).read_text(encoding="utf-8")
        assert "<root>" in output_content
        assert "</root>" in output_content

        Path(output_path).unlink()

    def test_no_input_error(self) -> None:
        """Test error when no input is provided."""
        result = runner.invoke(json_app, ["format"])

        assert result.exit_code == 1
        # When no input is provided, it tries to parse empty string as JSON
        assert (
            "No input provided" in result.stdout
            or "No input provided" in result.stderr
            or "Invalid JSON" in result.stderr
        )

    def test_file_not_found_error(self) -> None:
        """Test error when file doesn't exist."""
        result = runner.invoke(json_app, ["format", "/nonexistent/file.json"])

        assert result.exit_code == 1
        assert "Error reading file" in result.stdout or "Error reading file" in result.stderr


class TestJSONToXML:
    """Test cases for json_to_xml utility function."""

    def test_json_to_xml_with_object(self) -> None:
        """Test json_to_xml with JSON object."""
        data = {"name": "test", "value": 123}
        result = json_to_xml(data, "root")

        assert "<root>" in result
        assert "</root>" in result
        assert "<name>test</name>" in result
        assert "<value>123</value>" in result

    def test_json_to_xml_with_array(self) -> None:
        """Test json_to_xml with JSON array."""
        data = [1, 2, 3]
        result = json_to_xml(data, "root")

        assert "<root>" in result
        assert "</root>" in result
        assert "<item>1</item>" in result
        assert "<item>2</item>" in result
        assert "<item>3</item>" in result

    def test_json_to_xml_with_nested_object(self) -> None:
        """Test json_to_xml with nested JSON object."""
        data = {"user": {"name": "test", "age": 25}}
        result = json_to_xml(data, "root")

        assert "<root>" in result
        assert "</root>" in result
        assert "<user>" in result
        assert "</user>" in result
        assert "<name>test</name>" in result
        assert "<age>25</age>" in result

    def test_json_to_xml_with_boolean(self) -> None:
        """Test json_to_xml with boolean values."""
        data = {"active": True, "inactive": False}
        result = json_to_xml(data, "root")

        assert "<active>true</active>" in result
        assert "<inactive>false</inactive>" in result

    def test_json_to_xml_with_null(self) -> None:
        """Test json_to_xml with null value."""
        data = {"empty": None}
        result = json_to_xml(data, "root")

        # XML null values can be represented as empty elements or self-closing tags
        assert "<empty></empty>" in result or "<empty />" in result

    def test_json_to_xml_with_invalid_root_type(self) -> None:
        """Test json_to_xml with invalid root data type."""
        data = "string"

        with pytest.raises(TypeError, match="Root JSON data must be an object or array"):
            json_to_xml(data, "root")
