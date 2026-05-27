$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "docker-common.ps1")

$CodexVersion = "0.116.0"

for ($index = 0; $index -lt $args.Count; $index++) {
  switch ($args[$index]) {
    "--codex-version" {
      if ($index + 1 -ge $args.Count) {
        throw "Missing value for --codex-version"
      }

      $index++
      $CodexVersion = $args[$index]
      continue
    }
    "--help" {
      Write-Host "Usage: ./scripts/docker/build-codex-image.ps1 [--codex-version VERSION]"
      exit 0
    }
    default {
      throw "Unknown argument: $($args[$index])"
    }
  }
}

$RepoRoot = Get-MythicMcpRepoRoot
[void](Ensure-MythicCodexImage -RepoRoot $RepoRoot -CodexVersion $CodexVersion -Rebuild)
