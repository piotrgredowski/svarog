---
description: 'General instructions for Python code'
applyTo: '**/*.py'
---

<!-- NOTE: Do not modify this file manually unless you are sure about the changes. Instead, extend python-custom.instructions.md for project-specific dependencies and customizations. -->

## New language features

Prefer using the latest features of Python version used in the project. Look for `.python_version` or `pyproject.toml` file in the root of the repository to see which version is used.

Use `pathlib` for file path operations instead of `os.path`.

Prefer working with `pathlib.Path` objects instead of strings for file paths.

Prefer f-strings for string formatting.

For logging and exceptions, don't use f-strings. Use comma-separated arguments instead. Example: \`logging.info("%s - Something happened", user)

## Documentation

Use type hints for all function parameters and return values.

Use built-in generic types (e.g., `list`, `dict`) instead of importing equivalent types from the typing module.

Always add comprehensive docstrings using Google style format. But don't include types in docstrings. Example:

```python
def add(a: int, b: int) -> int:
    """Add two integers.

    Args:
        a: The first integer.
        b: The second integer.

    Returns:
        The sum of the two integers.
    """
    return a + b
```

Include short, summary docstrings for all public functions, classes, and modules. Summary docstring should be one line and start right after """ (without empty line) and should end with a period.

Include raised exceptions in docstrings.

Include doctests in docstring for the functions, if that makes sense and will not obfuscate the docstring.

When modifying existing code, update the docstrings if they are outdated or incomplete.

When adding new functionality, ensure that docstrings are added and are comprehensive.

## Error handling

Implement proper error handling and input validation where context-appropriate.

Do not use generic exceptions; always use custom exceptions. If a custom exception is available, use it; if not, create it.

Do not ever catch all exceptions with `except:` or `except Exception:`. If you need to catch all because you lack knowledge, leave a `# TODO: Change this to more specific exception` comment.

## External dependencies

Avoid using external libraries, unless really necessary.

Prefer implementing functionality using standard libraries, unless in already used dependencies there is a library which can be used.

If some functionality is needed and implementation of it is trivial - prefer implementing it inside of a project, instead of adding a dependency.

## Testing

Use pytest's parametrization for tests where applicable.

Write tests alongside the code to ensure functionality and catch bugs early.

When you are done with the implementation - run all unit tests to ensure everything works as expected.

## Refactoring

Avoid deeply nested code. If you find yourself nesting more than 2-3 levels, consider refactoring.

## Readability and clarity

Wherever it makes sense - use keyword arguments and require them in functions

Ensure code doesn't contain any unused imports or variables.

## Code organization

Organize related functions into modules (e.g., file_utils(.py), string_utils(.py), data_utils(.py)).

Prefer smaller, focused files that contain related utilities.

## Rest of the guidelines

When writing decorators, always use `@functools.wraps` to preserve the original function's metadata.
