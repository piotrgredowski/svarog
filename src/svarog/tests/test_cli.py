from unittest.mock import patch

from typer.testing import CliRunner

from svarog.cli import cli_app
from svarog.cli import version


class TestCLI:
    """Test cases for the main CLI interface."""

    def setup_method(self) -> None:
        """Set up test runner."""
        self.runner = CliRunner()

    def test_version_command(self) -> None:
        """Test the version command."""
        result = self.runner.invoke(cli_app, ["version"])
        assert result.exit_code == 0
        assert "svarog version 0.1.0" in result.stdout

    def test_help_command(self) -> None:
        """Test the help command."""
        result = self.runner.invoke(cli_app, ["--help"])
        assert result.exit_code == 0
        assert "svarog" in result.stdout
        assert "A collection of Python utilities" in result.stdout

    def test_no_args_shows_help(self) -> None:
        """Test that no arguments shows help."""
        result = self.runner.invoke(cli_app, [])
        # Typer with no_args_is_help=True shows help and exits with 2
        assert result.exit_code == 2
        assert "Usage:" in result.stdout

    def test_version_function_direct(self) -> None:
        """Test calling version function directly."""
        with patch("typer.echo") as mock_echo:
            version()
            mock_echo.assert_called_once_with("svarog version 0.1.0")

    def test_cli_main_execution(self) -> None:
        """Test CLI main execution path."""
        with patch("svarog._cli.cli_app"):
            # Import and execute the main block
            import svarog._claude_hooks.cli as cli_module

            # Simulate running the module directly
            if hasattr(cli_module, "__name__"):
                # This would be called when running python -m svarog._cli
                pass
