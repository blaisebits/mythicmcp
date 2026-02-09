#!/usr/bin/env bash
# Run MythicMCP integration tests
#
# Usage:
#   ./scripts/run_integration_tests.sh           # Run all integration tests
#   ./scripts/run_integration_tests.sh --quick   # Tool registration only (no Mythic needed)
#   ./scripts/run_integration_tests.sh --mcp     # Run MCP client check script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=============================================="
echo "MythicMCP Integration Tests"
echo "=============================================="

run_pytest_integration() {
    echo ""
    echo "Running pytest integration tests..."
    echo "----------------------------------------------"
    uv run pytest tests/integration/ -v
}

run_mcp_check() {
    echo ""
    echo "Running MCP tool verification..."
    echo "----------------------------------------------"
    uv run python scripts/check_mcp_tools.py --inspect-only
}

run_quick() {
    echo ""
    echo "Running quick tool registration tests..."
    echo "----------------------------------------------"
    uv run pytest tests/unit/test_mcp_tools.py tests/unit/test_file_tools.py -v
}

run_pipeline() {
    echo ""
    echo "Running full integration test pipeline..."
    echo "----------------------------------------------"
    uv run pytest tests/integration/ -v -m integration
}

case "${1:-}" in
    --quick)
        run_quick
        ;;
    --mcp)
        run_mcp_check
        ;;
    --pipeline)
        run_pipeline
        ;;
    --all)
        run_mcp_check
        echo ""
        run_pytest_integration
        ;;
    *)
        run_pytest_integration
        ;;
esac

echo ""
echo "=============================================="
echo "Integration tests complete"
echo "=============================================="
