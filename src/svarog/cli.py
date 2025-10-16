import typer

from svarog import __version__

cli_app = typer.Typer(
    name="svarog",
    help="A collection of utilities.",
    no_args_is_help=True,
)


@cli_app.callback()
def main() -> None:
    """A collection of utilities."""


@cli_app.command()
def version() -> None:
    """Print the version of Svarog."""
    typer.echo(__version__)


if __name__ == "__main__":
    cli_app()
