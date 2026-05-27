$ErrorActionPreference = "Stop"

$Rebuild = $false
$CodexVersion = "0.116.0"
$EnvFile = $null
$OperationId = $null

for ($index = 0; $index -lt $args.Count; $index++) {
  $arg = $args[$index]

  switch ($arg) {
    "--rebuild" {
      $Rebuild = $true
      continue
    }
    "--codex-version" {
      if ($index + 1 -ge $args.Count) {
        throw "Missing value for --codex-version"
      }

      $index++
      $CodexVersion = $args[$index]
      continue
    }
    "--env-file" {
      if ($index + 1 -ge $args.Count) {
        throw "Missing value for --env-file"
      }

      $index++
      $EnvFile = $args[$index]
      continue
    }
    "--operation-id" {
      if ($index + 1 -ge $args.Count) {
        throw "Missing value for --operation-id"
      }

      $index++
      $OperationId = $args[$index]
      continue
    }
    "--help" {
      Write-Host "Usage: ./scripts/docker/run-mcp-smoke.ps1 [--rebuild] [--codex-version VERSION] [--env-file PATH] [--operation-id ID]"
      exit 0
    }
    default {
      throw "Unknown argument: $arg"
    }
  }
}

$Runner = Join-Path $PSScriptRoot "run-codex-manual.ps1"
$OperationStep = ""
if ($OperationId) {
  $OperationStep = @"
3. Call `core_set_operation(operation_id=$OperationId)`.
4. Call `core_list_callbacks`.
"@
}

$PromptText = @"
You are validating the MythicMCP MCP server mounted from `/workspace`.

Use the `mythicmcp-dev` MCP server tools.

1. Call `core_check_connection`.
2. Call `list_available_agents`.
$OperationStep
Reply with a short report showing the results of each tool call.
"@

$RunnerArgs = @()
if ($Rebuild) {
  $RunnerArgs += "--rebuild"
}
if ($EnvFile) {
  $RunnerArgs += "--env-file"
  $RunnerArgs += $EnvFile
}
if ($CodexVersion) {
  $RunnerArgs += "--codex-version"
  $RunnerArgs += $CodexVersion
}
$RunnerArgs += "--prompt"
$RunnerArgs += $PromptText

& $Runner @RunnerArgs
exit $LASTEXITCODE
