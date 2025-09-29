import json
import sys

import typer

from .notification import process_notification
from .post_tool_use import process_post_tool_use
from .pre_tool_use import process_pre_tool_use
from .stop import process_stop
from .subagent_stop import process_subagent_stop

claude_hooks_app = typer.Typer(
    name="claude-hooks",
    help="A collection of Claude hooks utilities.",
)


@claude_hooks_app.command()
def notification(
    *, notify: bool = typer.Option(default=False, help="Announce notification via TTS")
) -> None:
    """Process notification data and optionally announce via TTS."""
    try:
        input_data = json.load(sys.stdin)
        process_notification(input_data, notify=notify)
    except json.JSONDecodeError as e:
        typer.echo("Error: Invalid JSON input", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@claude_hooks_app.command()
def post_tool_use() -> None:
    """Process post tool use data and log it."""
    try:
        input_data = json.load(sys.stdin)
        process_post_tool_use(input_data)
    except json.JSONDecodeError as e:
        typer.echo("Error: Invalid JSON input", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@claude_hooks_app.command()
def pre_tool_use() -> None:
    """Process and validate pre tool use data, blocking dangerous operations."""
    try:
        input_data = json.load(sys.stdin)
        process_pre_tool_use(input_data)
    except json.JSONDecodeError as e:
        typer.echo("Error: Invalid JSON input", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@claude_hooks_app.command()
def stop(
    *,
    chat: bool = typer.Option(default=False, help="Copy transcript to chat.json"),
) -> None:
    """Process stop hook data and optionally save chat transcript."""
    try:
        input_data = json.load(sys.stdin)
        process_stop(input_data, chat=chat)
    except json.JSONDecodeError as e:
        typer.echo("Error: Invalid JSON input", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e


@claude_hooks_app.command()
def subagent_stop(
    *,
    chat: bool = typer.Option(default=False, help="Copy transcript to chat.json"),
) -> None:
    """Process subagent stop hook data and optionally save chat transcript."""
    try:
        input_data = json.load(sys.stdin)
        process_subagent_stop(input_data, chat=chat)
    except json.JSONDecodeError as e:
        typer.echo("Error: Invalid JSON input", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from e
