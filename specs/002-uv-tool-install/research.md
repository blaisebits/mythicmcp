# Research: UV Tool Installation Support

**Feature**: 002-uv-tool-install
**Date**: 2026-01-25

## Research Summary

This feature requires minimal technical research as the project already has most infrastructure in place. The main work is verification, documentation, and user experience improvements.

## Current State Analysis

### Existing Infrastructure

The project already has:

1. **pyproject.toml with scripts entry point**:
   ```toml
   [project.scripts]
   mythicmcp = "mythicmcp.server:main"
   ```

2. **Hatchling build backend** - compatible with uv

3. **Main entry point function** in `src/mythicmcp/server.py`:
   ```python
   def main() -> None:
       """Run the MythicMCP server."""
       logger.info("Starting MythicMCP server...")
       mcp.run()
   ```

4. **Configuration via environment variables** - already implemented in `config.py`

### What's Missing

1. **Improved startup UX** - When config is missing, the error is technical rather than user-friendly
2. **Installation documentation** - README doesn't include uv tool installation instructions
3. **MCP client configuration examples** - Users need to know how to configure Claude Desktop, etc.
4. **Verification testing** - No test confirms the tool installs and runs correctly

## UV Tool Installation Requirements

### Decision: Standard pyproject.toml Configuration

**Rationale**: The existing pyproject.toml already meets uv tool requirements:
- `[project.scripts]` defines the CLI entry point
- `hatchling` build backend is fully supported by uv
- Dependencies are properly declared

**Alternatives Considered**:
- Adding `[tool.uv]` section: Not needed for basic tool installation
- Switching to `setuptools`: No benefit, hatchling is modern and well-supported

### Decision: Installation Command

**Rationale**: Users will install via:
```bash
uv tool install mythicmcp
```

Or from git for development:
```bash
uv tool install git+https://github.com/user/mythicmcp
```

**Alternatives Considered**:
- `uvx mythicmcp`: Good for one-off runs, but not persistent installation
- `pip install`: Works but doesn't provide uv's isolation benefits

## Configuration Guidance Strategy

### Decision: Helpful Startup Messages

**Rationale**: When configuration is missing, the server should:
1. Print clear instructions for setting environment variables
2. Exit with a non-zero status code
3. Not start an unconfigured server

**Implementation**: Enhance the `ConfigurationError` handling in `server.py` to provide user-friendly guidance.

### Environment Variables Required

| Variable | Required | Description |
|----------|----------|-------------|
| `MYTHIC_SERVER_URL` | Yes | Mythic server URL (e.g., `https://mythic.local:7443`) |
| `MYTHIC_API_TOKEN` | Conditional | API token (alternative to username/password) |
| `MYTHIC_USERNAME` | Conditional | Username (requires MYTHIC_PASSWORD) |
| `MYTHIC_PASSWORD` | Conditional | Password (requires MYTHIC_USERNAME) |
| `MYTHIC_TIMEOUT` | No | Query timeout in seconds (default: 30) |

## MCP Client Configuration

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "mythic": {
      "command": "mythicmcp",
      "env": {
        "MYTHIC_SERVER_URL": "https://mythic.local:7443",
        "MYTHIC_API_TOKEN": "your-api-token"
      }
    }
  }
}
```

### Cursor Configuration

Similar JSON structure in Cursor's MCP settings.

## Sources

- [UV Working on Projects](https://docs.astral.sh/uv/guides/projects/)
- [UV Tools Documentation](https://docs.astral.sh/uv/guides/tools/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
