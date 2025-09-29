---
description: 'Instructions for working with this project'
applyTo: '**'
---

# Instructions for working with this project

Keep repository-specific conventions in this document so contributors and agents can stay aligned.

## Documentation

- `README.md` holds the primary project documentation.
- `.github/instructions/` stores coding guidelines and conventions that every contribution must follow.
- Update these files whenever conventions change and record when contributors must adopt the revisions.

## Scratchpad workspace

- Use the root-level `.scratchpad/` directory for temporary experiments, helper scripts, or throwaway test data that should never ship.
- `.scratchpad/` and its contents must be ignored by git, so files placed here stay local by default.
- Feel free to create subdirectories inside `.scratchpad/` to group related work.
- Remove anything valuable from `.scratchpad/` once it should be shared with the team and move it into the proper tracked location before committing.
- Do not store secrets or long-term assets here; upgrade them into the tracked codebase or secure storage as soon as they matter.
