---
description: 'General instructions for writing any code'
applyTo: '**'
---

# General instructions

## External dependencies

Avoid using external libraries, unless really necessary.

Implement straightforward features inside the project when feasible.

## Testing

After fixing a bug, add a regression test that reproduces it.

Test only public interfaces, not internal implementation details.

## Organization

Organize code into small, focused files that group related utilities.

Keep solutions simple when additional complexity offers no clear benefit.

## Refactoring

Avoid adding comments to explain complex code—refactor it instead.

Do not refactor without a solid reason.

Add tests before refactoring untested code.

## Readability and clarity

Always prioritize readability and clarity.

Write concise functions with a single responsibility.

Use meaningful variable names that describe their data.

Try to not use abbreviations unless they are really widely recognized.
List of the abbreviations you can use:

- `id` = identifier,
- `temp` = temporary,
- `info` = information,
- `config` = configuration,
- `params` = parameters,
- `args` = arguments,
- `kwargs` = keyword arguments.
