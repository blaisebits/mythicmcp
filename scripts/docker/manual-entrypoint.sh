#!/usr/bin/env bash
set -euo pipefail

CODEX_HOME="${CODEX_HOME:-/codex-home}"
WORK_ROOT="${WORK_ROOT:-/workspace}"

mkdir -p "$CODEX_HOME" "$WORK_ROOT"

echo "MythicMCP Codex Docker harness ready."
echo "- Workspace: $WORK_ROOT"
echo "- CODEX_HOME: $CODEX_HOME"

if [[ ! -f "$CODEX_HOME/auth.json" ]]; then
  echo "Codex auth was not found in CODEX_HOME. Run: codex login"
fi

cd "$WORK_ROOT"
exec "$@"
