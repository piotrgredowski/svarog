"""CLI interface for Svarog tools."""

from __future__ import annotations

import typer

from .json_tool import json_app

tools_app = typer.Typer(
    name="tool",
    help="A collection of useful command-line tools.",
    no_args_is_help=True,
)

tools_app.add_typer(json_app, name="json")
