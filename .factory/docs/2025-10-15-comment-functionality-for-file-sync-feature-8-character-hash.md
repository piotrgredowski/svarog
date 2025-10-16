# Comment Functionality for File Sync Feature - Implementation Plan (Corrected)

## Overview

Add automatic comment generation to the file sync feature with CLI control, content-based IDs, and adapter-specific rendering. Comments will be inserted using the section mapping system with `previous_value` and `next_value` parameters.

## Implementation Components

### 1. CLI Integration

- **Add `--no-comment` flag** to `files` command in `_cli.py`
- **Update `files()` function** to accept new parameter
- **Update `SyncOptions`** dataclass with `add_comments: bool = True`

### 2. Comment Generation Logic

- **Create `generate_comment_id()` function** using SHA256 hash of content (first 8 characters)
- **Create `generate_section_comment()` function** with format: "This is auto-generated section with ID: {hash}"
- **Create `generate_comments_for_section()` function** to return start/end comment pair

### 3. Comment Insertion Logic (Using Section Mapping)

- **Leverage existing `previous_value` and `next_value` parameters** in `dst_adapter.set_section()`
- **Generate start and end comments** using adapter's `render_comment()` method
- **Insert comments as structured comment objects** for Markdown adapter
- **Insert comments as formatted strings** for YAML adapter
- **Handle both regular sync and section mapping scenarios**

### 4. Test Suite Creation

- **Unit tests** for comment generation and hash consistency
- **Integration tests** for CLI flag behavior
- **Adapter tests** for different comment formats (YAML `#`, Markdown `<!-- -->`)
- **End-to-end tests** for complete sync workflow with comments
- **Edge cases**: empty files, binary files, section mapping, dry-run mode

## Key Implementation Details

### Comment Insertion Mechanism

```python
# For each section being synced:
if options.add_comments:
    start_comment = adapter.render_comment(f"This is auto-generated section with ID: {hash}")
    end_comment = adapter.render_comment(f"This is auto-generated section with ID: {hash}")

    # Use existing set_section parameters
    dst_adapter.set_section(
        data=dst_data,
        path=mapping.dst_path,
        value=value,
        previous_value=start_comment,
        next_value=end_comment,
        create=mapping.create
    )
```

### Hash Generation

- Use SHA256 of the content being synced
- Return first 8 characters for readable IDs
- Ensure consistency across runs

### Adapter Integration

- **YAML**: `render_comment()` returns `"# {text}"`
- **Markdown**: `render_comment()` returns `"<!-- {text} -->"`
- Comments are rendered by adapters but inserted via section mapping system

## Files to Modify

1. `src/svarog/_sync/_cli.py` - Add CLI flag
1. `src/svarog/_sync/file_sync.py` - Update SyncOptions & sync logic
1. `tests/svarog/_sync/test_comment_functionality.py` - Create comprehensive tests

## Success Criteria

- Comments appear in correct format for YAML (`#`) and Markdown (`<!-- -->`) files
- Same content always generates same 8-character hash ID
- `--no-comment` flag successfully disables comment insertion
- Comments are visible in diff output during dry-run
- Feature integrates seamlessly with existing section mapping functionality
