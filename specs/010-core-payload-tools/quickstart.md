# Quickstart: Core Payload Tools

**Feature**: 010-core-payload-tools

## What to Build

Add 6 new MCP tools to `src/mythicmcp/tools/payloads.py` for managing Mythic payloads:

1. `core_list_payloads` — list all payloads in current operation
2. `core_get_payload` — get detail by UUID
3. `core_create_payload` — build a new standard payload
4. `core_download_payload` — download built binary
5. `core_check_payload_config` — validate C2 configuration
6. `core_payload_redirect_rules` — get redirect rules

## Files to Create/Modify

| File | Action | Purpose |
| ---- | ------ | ------- |
| `src/mythicmcp/tools/payloads.py` | Create | All 6 tool implementations + exception classes + parsers |
| `src/mythicmcp/models.py` | Modify | Add payload Pydantic response models |
| `src/mythicmcp/server.py` | Modify | Register 6 new tools with `@mcp.tool()` |
| `src/mythicmcp/tools/__init__.py` | Modify | Export new tool functions |
| `tests/unit/test_payload_tools.py` | Create | Unit tests for registration, models, parsing |

## Key Patterns to Follow

- **Module structure**: Mirror `files.py` — exception classes at top, parser helpers, business logic functions, then `core_*` entry points at bottom
- **Error handling**: Use response union types (`Response | ErrorResponse`) for create/download; use `McpError` for list/get
- **Models**: All responses include `retrieved_at: datetime` field with `default_factory=utc_now`
- **Mythic imports**: Lazy import `from mythic import mythic` inside async functions (not top-level)
- **Context access**: `mythic_ctx: MythicContext = ctx.request_context.lifespan_context`
- **Operation check**: Verify `mythic_instance.current_operation_id` before API calls

## Build Order

1. Models in `models.py` (no dependencies)
2. `payloads.py` — exception classes + parsers + business logic + entry points
3. `server.py` — register tools
4. `__init__.py` — exports
5. Unit tests
