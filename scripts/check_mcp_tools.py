#!/usr/bin/env python3
"""MCP client script for integration testing.

This script connects to the MythicMCP server and verifies all expected tools are available.

Usage:
    # With real Mythic server (full integration test):
    export MYTHIC_SERVER_URL="https://mythic.local:7443"
    export MYTHIC_API_TOKEN="your-token"
    python scripts/check_mcp_tools.py

    # Without Mythic server (tool registration check only):
    python scripts/check_mcp_tools.py --inspect-only
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


# Expected tools that MythicMCP should expose
EXPECTED_TOOLS = {
    "core_list_callbacks": "List all active callbacks in the operation",
    "core_get_callback": "Get details for a specific callback by ID",
    "core_get_operation": "Get current operation information",
    "core_check_connection": "Verify Mythic server connectivity",
}


def inspect_tool_registration() -> dict[str, str]:
    """Inspect the server module to verify tool registration without starting the server.

    Returns:
        Dictionary mapping tool names to their descriptions.
    """
    from mythicmcp.server import mcp

    tools = {}
    for name, tool in mcp._tool_manager._tools.items():
        description = tool.description or ""
        # Get first line of description
        first_line = description.split("\n")[0].strip()
        tools[name] = first_line

    return tools


async def check_tools_via_mcp() -> dict[str, str]:
    """Connect to MythicMCP server via MCP protocol and list tools.

    Returns:
        Dictionary mapping tool names to their descriptions.
    """
    import os

    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    # Get the path to the mythicmcp command
    # When installed via uv tool, it's in ~/.local/bin/mythicmcp
    # When running from source, use uv run
    mythicmcp_cmd = "mythicmcp"

    # Check if running from source (pyproject.toml exists in cwd or parent)
    from pathlib import Path

    project_root = Path(__file__).parent.parent
    if (project_root / "pyproject.toml").exists():
        # Running from source - use uv run
        server_params = StdioServerParameters(
            command="uv",
            args=["run", "mythicmcp"],
            cwd=str(project_root),
            env={
                **os.environ,
                # Ensure proper Python path
                "PYTHONPATH": str(project_root / "src"),
            },
        )
    else:
        # Running from installed package
        server_params = StdioServerParameters(
            command=mythicmcp_cmd,
            env=dict(os.environ),
        )

    tools = {}

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session
            await session.initialize()

            # List available tools
            result = await session.list_tools()

            for tool in result.tools:
                # Get first line of description
                description = tool.description or ""
                first_line = description.split("\n")[0].strip()
                tools[tool.name] = first_line

    return tools


def verify_tools(actual_tools: dict[str, str], expected_tools: dict[str, str]) -> bool:
    """Verify that all expected tools are present.

    Args:
        actual_tools: Dictionary of actual tool names to descriptions.
        expected_tools: Dictionary of expected tool names to descriptions.

    Returns:
        True if all expected tools are present, False otherwise.
    """
    all_passed = True

    print("\n" + "=" * 60)
    print("MythicMCP Tool Verification")
    print("=" * 60)

    # Check for missing tools
    missing_tools = set(expected_tools.keys()) - set(actual_tools.keys())
    if missing_tools:
        print(f"\n[FAIL] Missing tools: {', '.join(sorted(missing_tools))}")
        all_passed = False

    # Check for unexpected tools (informational only)
    extra_tools = set(actual_tools.keys()) - set(expected_tools.keys())
    if extra_tools:
        print(f"\n[INFO] Additional tools found: {', '.join(sorted(extra_tools))}")

    # List all tools found
    print("\nTools discovered:")
    print("-" * 60)

    for name in sorted(actual_tools.keys()):
        description = actual_tools[name]
        status = "[OK]" if name in expected_tools else "[NEW]"
        print(f"  {status} {name}")
        print(f"       {description[:70]}...")

    print("-" * 60)
    print(f"\nTotal tools: {len(actual_tools)}")
    print(f"Expected: {len(expected_tools)}")
    print(f"Missing: {len(missing_tools)}")
    print(f"Extra: {len(extra_tools)}")

    if all_passed:
        print("\n[PASS] All expected tools are available!")
    else:
        print("\n[FAIL] Some expected tools are missing!")

    return all_passed


async def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Check MythicMCP tool availability",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--inspect-only",
        action="store_true",
        help="Only inspect tool registration without starting the server",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON",
    )

    args = parser.parse_args()

    try:
        if args.inspect_only:
            print("Inspecting tool registration (no server startup)...")
            actual_tools = inspect_tool_registration()
        else:
            print("Connecting to MythicMCP server via MCP protocol...")
            actual_tools = await check_tools_via_mcp()

        if args.json:
            import json

            output = {
                "tools": actual_tools,
                "expected": EXPECTED_TOOLS,
                "missing": list(set(EXPECTED_TOOLS.keys()) - set(actual_tools.keys())),
                "extra": list(set(actual_tools.keys()) - set(EXPECTED_TOOLS.keys())),
            }
            print(json.dumps(output, indent=2))
            return 0 if not output["missing"] else 1
        else:
            success = verify_tools(actual_tools, EXPECTED_TOOLS)
            return 0 if success else 1

    except Exception as e:
        print(f"\n[ERROR] Failed to check tools: {e}", file=sys.stderr)
        if not args.inspect_only:
            print("\nHint: Use --inspect-only to check tool registration without a Mythic server")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
