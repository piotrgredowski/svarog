# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python utilities library called "svarog" created by @piotrgredowski. It's intended to be a collection of custom Python utilities for reuse across multiple projects. The project uses modern Python packaging with pyproject.toml and is currently in its initial setup phase.

## Development Commands

### Running the Application

```bash
python hello.py
```

### Python Environment

- Requires Python >= 3.10.0
- Uses pyproject.toml for project configuration
- Dependencies: structlog>=24.1.0 for structured logging

## Project Structure

- `hello.py` - Main entry point with a simple greeting function
- `pyproject.toml` - Project configuration and metadata
- `README.md` - Project documentation
- `src/svarog/` - Main package source code
- `src/demo/` - Example usage scripts
- `src/tests/` - Test files

## Architecture Notes

This is a utilities library that will contain reusable Python functions and classes. As the library grows, utilities should be organized into logical modules. The current hello.py serves as a placeholder and will likely be replaced with actual utility modules.

## General Guidelines

## Python specific guidelines

### Development Guidelines

When adding new utilities:

- Organize related functions into modules (e.g., file_utils(.py), string_utils(.py), data_utils(.py))

- Prefer smaller, focused functions that do one thing well

- Prefer smaller, focused files that contain related utilities

- Write Python 3.10+ compatible code

- Include type hints for all functions

- Write docstrings following standard Python conventions

- Consider adding the library as a dependency in other projects via pip install

- Wherever it makes sense - use keyword arguments and require them in functions

- Keep things simple. Don't overcomplicate if it doesn't make sense.

- Whenever it makes sense, remember about adding logging/observability to the features

- Have in mind SOLID principles:

  - Single Responsibility: Each class/function should have one reason to change
  - Open/Closed: Open for extension, closed for modification
  - Liskov Substitution: Subtypes must be substitutable for their base types
  - Interface Segregation: Don't force clients to depend on unused interfaces
  - Dependency Inversion: Depend on abstractions, not concretions

- Don't import directly from `typing` module, always import it `import typing as t` and use for example `t.Literal`

- When writing decorators, use @functools.wraps

### Development Utilities

- pre-commit hooks are run with `uv run pre-commit run --all-files`

### Important Warnings

- Never modify .ruff.toml

## Version Control Guidelines

- Use git as checkpoint mechanism - always commit changes, using conventional commit message

## Testing Commands

- Tests are run with `uv run pytest`

## Available Utilities

### Testing Guidelines

- In tests, try to not mock or patch if it's not necessary
- Use dependency injection in code to make it easier to test the code
- Try to write tests next to the source code in `tests` directory
