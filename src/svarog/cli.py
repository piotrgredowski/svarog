import typer

from svarog import __version__

cli_app = typer.Typer(
    name="svarog",
    help="A collection of utilities.",
)


def version() -> None:
    """Print the version of Svarog."""
    typer.echo(__version__)
