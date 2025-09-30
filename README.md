# Svarog

A collection of custom Python utilities by @piotrgredowski for reuse across multiple projects.

## Overview

This library contains reusable Python functions and classes organized into logical modules.

## Available Utilities

### File synchronization

The `svarog sync files` command copies the contents of one file into another within the same repository.

```bash
uv run svarog sync files path/to/source.txt path/to/target.txt
```

Key options:

- `--dry-run`: Preview the changes without modifying the target file.
- `--diff`: Print a unified diff between the current and proposed contents.
- `--backup`: Create a timestamped `.bak` file of the target before overwriting.
- `--binary`: Allow synchronization of binary files.
- `--encoding`: Override the default UTF-8 encoding.

Repeated runs on already synchronized files exit successfully and report `Already in sync.`

## Installation

```bash
uv sync
```

## Development

Requires Python >= 3.10.0

### Running

```bash
python hello.py
```
