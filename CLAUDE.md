# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python utilities library called "svarog" created by Piotr Grędowski. It's intended to be a collection of custom Python utilities for reuse across multiple projects. The project uses modern Python packaging with pyproject.toml and is currently in its initial setup phase.

## Development Commands

### Running the Application
```bash
python hello.py
```

### Python Environment
- Requires Python >= 3.10.0
- Uses pyproject.toml for project configuration
- No external dependencies currently defined

## Project Structure

- `hello.py` - Main entry point with a simple greeting function
- `pyproject.toml` - Project configuration and metadata
- `README.md` - Currently empty, intended for project documentation

## Architecture Notes

This is a utilities library that will contain reusable Python functions and classes. As the library grows, utilities should be organized into logical modules. The current hello.py serves as a placeholder and will likely be replaced with actual utility modules.

## Development Guidelines

When adding new utilities:
- Organize related functions into modules (e.g., file_utils.py, string_utils.py, data_utils.py)
- Include type hints for all functions
- Write docstrings following standard Python conventions
- Consider adding the library as a dependency in other projects via pip install
