$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "docker-common.ps1")

$InteractiveMode = $false
$ShellMode = $false
$Rebuild = $false
$FreshHome = $false
$CodexVersion = "0.116.0"
$PromptText = $null
$PromptFile = $null
$EnvFile = $null
$CodexArgs = @()

for ($index = 0; $index -lt $args.Count; $index++) {
  $arg = $args[$index]

  switch ($arg) {
    "-i" {
      $InteractiveMode = $true
      continue
    }
    "--interactive" {
      $InteractiveMode = $true
      continue
    }
    "--shell" {
      $ShellMode = $true
      continue
    }
    "--rebuild" {
      $Rebuild = $true
      continue
    }
    "--fresh-home" {
      $FreshHome = $true
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
    "--prompt" {
      if ($index + 1 -ge $args.Count) {
        throw "Missing value for --prompt"
      }

      $index++
      $PromptText = $args[$index]
      continue
    }
    "--prompt-file" {
      if ($index + 1 -ge $args.Count) {
        throw "Missing value for --prompt-file"
      }

      $index++
      $PromptFile = $args[$index]
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
      Write-Host "Usage: ./scripts/docker/run-codex-manual.ps1 [-i|--interactive] [--shell] [--rebuild] [--fresh-home] [--codex-version VERSION] [--prompt TEXT | --prompt-file PATH] [--env-file PATH] [codex args...]"
      exit 0
    }
    default {
      $CodexArgs += $arg
    }
  }
}

if ($ShellMode -and ($PromptText -or $PromptFile)) {
  throw "--shell cannot be combined with --prompt or --prompt-file"
}

if ($PromptText -and $PromptFile) {
  throw "Use either --prompt or --prompt-file, not both"
}

if ($PromptFile) {
  $PromptFile = (Resolve-Path $PromptFile -ErrorAction Stop).Path
  $PromptText = Get-Content $PromptFile -Raw
}

$RepoRoot = Get-MythicMcpRepoRoot
$PersistedCodexHome = Join-Path $RepoRoot ".local\codex-docker-home"
$CaptureRoot = Join-Path $RepoRoot ".local\session-captures"
$ResolvedEnv = Resolve-MythicHarnessEnv -EnvFile $EnvFile
$ImageName = Ensure-MythicCodexImage -RepoRoot $RepoRoot -CodexVersion $CodexVersion -Rebuild:$Rebuild

Initialize-MythicCodexHome -PersistedCodexHome $PersistedCodexHome -ResolvedEnv $ResolvedEnv -FreshHome:$FreshHome

$PromptMode = -not [string]::IsNullOrWhiteSpace($PromptText)
$CaptureDir = Join-Path $CaptureRoot (Get-Date -Format "yyyyMMdd-HHmmss")

if ($PromptMode) {
  New-Item -ItemType Directory -Force $CaptureDir | Out-Null
  Set-Content -Path (Join-Path $CaptureDir "prompt.txt") -Value $PromptText
}

$DockerArgs = @(
  "run",
  "--rm"
)

if (-not $PromptMode) {
  $DockerArgs += "-it"
}

$DockerArgs += @(
  "-e",
  "CODEX_HOME=/codex-home"
)

$DockerArgs += Get-MythicDockerEnvArgs -ResolvedEnv $ResolvedEnv
$DockerArgs += @(
  "-v",
  "${RepoRoot}:/workspace",
  "-v",
  "${PersistedCodexHome}:/codex-home",
  "-w",
  "/workspace"
)

if ($PromptMode) {
  $DockerArgs += @(
    "-v",
    "${CaptureDir}:/capture"
  )
}

$DockerArgs += $ImageName

if ($ShellMode) {
  $DockerArgs += @("bash", "-i")
} elseif ($PromptMode) {
  $DockerArgs += @(
    "bash",
    "-lc",
    'cat /capture/prompt.txt | codex exec --dangerously-bypass-approvals-and-sandbox --skip-git-repo-check --color never --output-last-message /codex-home/manual-last-message.txt - "$@"',
    "--"
  ) + $CodexArgs
} else {
  if ($InteractiveMode) {
    Write-Host "Launching interactive Codex session in Docker"
  } else {
    Write-Host "Launching default Codex session in Docker"
  }

  $DockerArgs += @(
    "codex",
    "--dangerously-bypass-approvals-and-sandbox",
    "--no-alt-screen"
  ) + $CodexArgs
}

& docker @DockerArgs
exit $LASTEXITCODE
