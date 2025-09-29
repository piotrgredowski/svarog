---
description: 'Additional instructions for working with this project'
applyTo: '**'
---

# Additional instructions for working with this project

Keep repository-specific conventions in this document so contributors and agents can stay aligned.

## Useful commands

- `uv sync` - Install project dependencies
- `uv sync --dev` - Install project and development dependencies
- `uv run pytest` - Run tests
- `uv run pytest -k <test_name>` - Run specific test by name
- `uv run pytest --cov` - Run tests with coverage report
- `uv run pre-commit run --all-files` - Run pre-commit hooks on all files
- `uv run ruff check .` - Run ruff linter on the project
- `uv run ruff check . --fix` - Run ruff linter and

## Scratchpad workspace

- Use the root-level `.scratchpad/` directory for temporary experiments, helper scripts, or throwaway test data.
- Feel free to create subdirectories inside `.scratchpad/` to group related work; everything within is excluded from git.
- Remove anything valuable from `.scratchpad/` once it should be shared with the team and move it into the proper tracked location before committing.

## Project Structure

- `pyproject.toml` - Project configuration and metadata
- `README.md` - Project documentation
- `src/svarog/` - Main package source code
- `src/demo/` - Example usage scripts
- `tests/` - Test files

## Git

- This project uses pre-commit hooks for code quality checks (formatting, linting, etc.)
- If commits fail due to pre-commit issues, run pre-commit manually to see and fix issues
- Pre-commit configuration is defined in `.pre-commit-config.yaml`
- Always ensure pre-commit hooks pass before pushing changes

## Python Environment

- Dependencies are listed in `pyproject.toml` and managed via `uv`
- `.ruff.base.toml` must be kept unchanged to ensure consistent linting rules
- `.ruff.toml` can be modified only by human for project-specific linting rules if necessary
