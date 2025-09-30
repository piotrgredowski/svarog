import typer

from svarog import __version__
from svarog.core.constants import APP_NAME

from ._claude_hooks import claude_hooks_app
from ._sync._cli import sync_app

cli_app = typer.Typer(
    name=APP_NAME,
    help="A collection of utilities.",
)


def version() -> None:
    """Print the version of Svarog."""
    typer.echo(__version__)


cli_app.add_typer(claude_hooks_app)
cli_app.add_typer(sync_app)
