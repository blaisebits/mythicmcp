$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "docker-common.ps1")

$Rebuild = $false
$CodexVersion = "0.116.0"
$EnvFile = $null
$IntegrationArgs = @()

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
    "--help" {
      Write-Host "Usage: ./scripts/docker/run-integration-tests.ps1 [--rebuild] [--codex-version VERSION] [--env-file PATH] [integration args...]"
      exit 0
    }
    default {
      $IntegrationArgs += $arg
    }
  }
}

$RepoRoot = Get-MythicMcpRepoRoot
$ResolvedEnv = Resolve-MythicHarnessEnv -EnvFile $EnvFile
$ImageName = Ensure-MythicCodexImage -RepoRoot $RepoRoot -CodexVersion $CodexVersion -Rebuild:$Rebuild

$DockerArgs = @(
  "run",
  "--rm",
  "-v",
  "${RepoRoot}:/workspace",
  "-w",
  "/workspace"
)

$DockerArgs += Get-MythicUvDockerEnvArgs
$DockerArgs += Get-MythicDockerEnvArgs -ResolvedEnv $ResolvedEnv
$DockerArgs += @(
  $ImageName,
  "bash",
  "./scripts/run_integration_tests.sh"
) + $IntegrationArgs

& docker @DockerArgs
exit $LASTEXITCODE
