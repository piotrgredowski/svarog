"""JSON tool implementation."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from xml.etree import ElementTree

import typer
import yaml


def get_input_data(file_path: str | None, *, quiet: bool = False) -> str:
    """Get input data from file or stdin.

    Args:
        file_path: Path to file to read from, or None to read from stdin.
        quiet: Suppress error messages.

    Returns:
        The input data as a string.

    Raises:
        typer.Exit: If input cannot be read.
    """
    if file_path:
        try:
            return Path(file_path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            if not quiet:
                typer.echo(f"Error reading file {file_path}: {error}", err=True)
            raise typer.Exit(code=1) from error
    else:
        if sys.stdin.isatty():
            if not quiet:
                typer.echo(
                    "Error: No input provided. Use file argument or pipe data to stdin.",
                    err=True,
                )
            raise typer.Exit(code=1)
        try:
            return sys.stdin.read()
        except (OSError, UnicodeDecodeError) as error:
            if not quiet:
                typer.echo(f"Error reading from stdin: {error}", err=True)
            raise typer.Exit(code=1) from error


FILE_ARGUMENT = typer.Argument(
    None,
    help="JSON file to process. If not provided, reads from stdin.",
    show_default=False,
)
INDENT_OPTION = typer.Option(
    default=2,
    help="Number of spaces for indentation in formatted output.",
)
OUTPUT_OPTION = typer.Option(
    default=None,
    help="Output file path. If not provided, writes to stdout.",
)
QUIET_OPTION = typer.Option(
    default=False,
    help="Suppress all output, only return exit code.",
    is_flag=True,
)

json_app = typer.Typer(
    name="json",
    help="JSON data processing tools.",
    no_args_is_help=True,
)


@json_app.command(name="format")
def format_(
    file_path: str = FILE_ARGUMENT,
    *,
    indent: int = INDENT_OPTION,
    output: str = OUTPUT_OPTION,
    quiet: bool = QUIET_OPTION,
) -> None:
    """Format JSON data with proper indentation.

    Args:
        file_path: Path to JSON file or stdin if not provided.
        indent: Number of spaces for indentation.
        output: Output file path or stdout if not provided.
        quiet: Suppress all output.

    Raises:
        typer.Exit: If JSON processing fails.
    """
    input_data = get_input_data(file_path, quiet=quiet)

    try:
        parsed_data = json.loads(input_data)
        formatted_json = json.dumps(parsed_data, indent=indent, ensure_ascii=False)
    except json.JSONDecodeError as error:
        if not quiet:
            typer.echo(f"Invalid JSON: {error}", err=True)
        raise typer.Exit(code=1) from error

    write_output(formatted_json, output, quiet=quiet)


@json_app.command()
def validate(
    file_path: str = FILE_ARGUMENT,
    *,
    quiet: bool = QUIET_OPTION,
) -> None:
    """Validate JSON data.

    Args:
        file_path: Path to JSON file or stdin if not provided.
        quiet: Suppress all output.

    Raises:
        typer.Exit: If JSON is invalid.
    """
    input_data = get_input_data(file_path, quiet=quiet)

    try:
        json.loads(input_data)
        if not quiet:
            typer.echo("Valid JSON")
    except json.JSONDecodeError as error:
        if not quiet:
            typer.echo(f"Invalid JSON: {error}", err=True)
        raise typer.Exit(code=1) from error


@json_app.command()
def minify(
    file_path: str = FILE_ARGUMENT,
    *,
    output: str = OUTPUT_OPTION,
    quiet: bool = QUIET_OPTION,
) -> None:
    """Minify JSON data by removing whitespace.

    Args:
        file_path: Path to JSON file or stdin if not provided.
        output: Output file path or stdout if not provided.
        quiet: Suppress all output.

    Raises:
        typer.Exit: If JSON processing fails.
    """
    input_data = get_input_data(file_path, quiet=quiet)

    try:
        parsed_data = json.loads(input_data)
        minified_json = json.dumps(parsed_data, separators=(",", ":"), ensure_ascii=False)
    except json.JSONDecodeError as error:
        if not quiet:
            typer.echo(f"Invalid JSON: {error}", err=True)
        raise typer.Exit(code=1) from error

    write_output(minified_json, output, quiet=quiet)


@json_app.command()
def to_yaml(
    file_path: str = FILE_ARGUMENT,
    *,
    output: str = OUTPUT_OPTION,
    quiet: bool = QUIET_OPTION,
) -> None:
    """Convert JSON data to YAML format.

    Args:
        file_path: Path to JSON file or stdin if not provided.
        output: Output file path or stdout if not provided.
        quiet: Suppress all output.

    Raises:
        typer.Exit: If conversion fails.
    """
    input_data = get_input_data(file_path, quiet=quiet)

    try:
        parsed_data = json.loads(input_data)
        yaml_data = yaml.dump(parsed_data, default_flow_style=False, allow_unicode=True)
    except json.JSONDecodeError as error:
        if not quiet:
            typer.echo(f"Invalid JSON: {error}", err=True)
        raise typer.Exit(code=1) from error
    except yaml.YAMLError as error:
        if not quiet:
            typer.echo(f"YAML conversion error: {error}", err=True)
        raise typer.Exit(code=1) from error

    write_output(yaml_data, output, quiet=quiet)


@json_app.command()
def to_xml(
    file_path: str = FILE_ARGUMENT,
    *,
    output: str = OUTPUT_OPTION,
    root_name: str = typer.Option("root", help="Root element name for XML output."),
    quiet: bool = QUIET_OPTION,
) -> None:
    """Convert JSON data to XML format.

    Args:
        file_path: Path to JSON file or stdin if not provided.
        output: Output file path or stdout if not provided.
        root_name: Name for the root XML element.
        quiet: Suppress all output.

    Raises:
        typer.Exit: If conversion fails.
    """
    input_data = get_input_data(file_path, quiet=quiet)

    try:
        parsed_data = json.loads(input_data)
        xml_data = json_to_xml(parsed_data, root_name)
    except json.JSONDecodeError as error:
        if not quiet:
            typer.echo(f"Invalid JSON: {error}", err=True)
        raise typer.Exit(code=1) from error
    except (ValueError, ElementTree.ParseError) as error:
        if not quiet:
            typer.echo(f"XML conversion error: {error}", err=True)
        raise typer.Exit(code=1) from error

    write_output(xml_data, output, quiet=quiet)


def _build_xml_element(parent: ElementTree.Element, key: str, value: object) -> None:
    """Recursively build XML elements from JSON data."""
    if isinstance(value, dict):
        element = ElementTree.SubElement(parent, key)
        for k, v in value.items():
            _build_xml_element(element, k, v)
    elif isinstance(value, list):
        element = ElementTree.SubElement(parent, key)
        for item in value:
            _build_xml_element(element, "item", item)
    elif isinstance(value, bool):
        element = ElementTree.SubElement(parent, key)
        element.text = str(value).lower()
    elif value is None:
        element = ElementTree.SubElement(parent, key)
        element.text = ""
    else:
        element = ElementTree.SubElement(parent, key)
        element.text = str(value)


def _create_root_element(data: dict | list, root_name: str) -> ElementTree.Element:
    """Create root XML element from JSON data.

    Args:
        data: JSON data to convert.
        root_name: Name for the root element.

    Returns:
        Root XML element.

    Raises:
        TypeError: If data type is not supported.
    """
    root = ElementTree.Element(root_name)

    if isinstance(data, dict):
        for key, value in data.items():
            _build_xml_element(root, key, value)
    elif isinstance(data, list):
        for item in data:
            _build_xml_element(root, "item", item)
    else:
        error_message = "Root JSON data must be an object or array"
        raise TypeError(error_message)

    return root


def json_to_xml(data: dict | list, root_name: str) -> str:
    """Convert JSON data to XML string.

    Args:
        data: JSON data to convert.
        root_name: Name for the root element.

    Returns:
        XML string representation.

    Raises:
        TypeError: If data type is not supported.
    """
    root = _create_root_element(data, root_name)
    return ElementTree.tostring(root, encoding="unicode")


def write_output(data: str, output_path: str | None, *, quiet: bool = False) -> None:
    """Write data to file or stdout.

    Args:
        data: Data to write.
        output_path: Output file path or None for stdout.
        quiet: Suppress all output messages.

    Raises:
        typer.Exit: If writing fails.
    """
    if output_path:
        try:
            Path(output_path).write_text(data, encoding="utf-8")
            if not quiet:
                typer.echo(f"Output written to {output_path}")
        except (OSError, UnicodeEncodeError) as error:
            if not quiet:
                typer.echo(f"Error writing to file {output_path}: {error}", err=True)
            raise typer.Exit(code=1) from error
    elif not quiet:
        typer.echo(data)
