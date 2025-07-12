## Testing

Ensure tests are written for all new features and bug fixes and are passing.

```bash
uv run pytest
```

## Pre-commit hooks

Ensure pre-commit hooks are run before committing code. This includes formatting, linting, and other checks.

```bash
uv run pre-commit run --all-files
```

## Python Version:

Write Python 3.10 code.
Prefer using the latest features of Python.
Use built-in generic types (e.g., list, dict) instead of importing equivalent types from the typing module.

## Code Style

Adhere to PEP 8 style guide for Python code.

## Error Handling and Input Validation

Error Handling and Input Validation:

Implement proper error handling and input validation where context-appropriate.

## Function and Class Signatures

Do not ever catch all exceptions. If you need to catch all because you don't know something, leave a # TODO: Change this to more specific exception comment.
Function and Class Signatures:

## Dependencies

Make arguments and return types explicit in the class/function signature.
Use type hints to improve code readability and maintainability.

## Documentation

## Testing

Ensure code doesn't contain any unused imports or variables.
Documentation:

## Performance

Include short, summary docstrings for all public functions, classes, and modules. Summary docstring should be one line and start right after """ (without empty line) and should end with a period.

## Tests

Use pytest's parametrization for tests where applicable.
Write tests alongside the code to ensure functionality and catch bugs early.
Performance:

Consider performance optimizations where relevant.

## Comments

Avoid adding comments other than the ones hinting that I should change something.
