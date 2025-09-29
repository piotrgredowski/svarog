import typer

from svarog import __version__

from ._claude_hooks import claude_hooks_app

cli_app = typer.Typer(
    name="svarog",
    help="A collection of utilities.",
)


def version() -> None:
    """Print the version of Svarog."""
    typer.echo(__version__)


cli_app.add_typer(claude_hooks_app)
