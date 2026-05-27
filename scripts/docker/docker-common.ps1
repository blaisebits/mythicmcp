$ErrorActionPreference = "Stop"

$script:MythicHarnessEnvKeys = @(
  "MYTHIC_SERVER_URL",
  "MYTHIC_API_TOKEN",
  "MYTHIC_USERNAME",
  "MYTHIC_PASSWORD",
  "MYTHIC_TIMEOUT",
  "MYTHIC_AGENTS",
  "MYTHIC_HOTLOAD",
  "MYTHIC_DEV"
)

$script:MythicUvDockerEnv = [ordered]@{
  "UV_PROJECT_ENVIRONMENT" = "/tmp/mythicmcp-venv"
  "UV_CACHE_DIR" = "/tmp/uv-cache"
}

function Get-MythicMcpRepoRoot {
  Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

function Get-MythicCodexImageName {
  "mythicmcp-codex-manual"
}

function Get-MythicEnvVarValue {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Name
  )

  $item = Get-Item -Path "Env:$Name" -ErrorAction SilentlyContinue
  if ($null -eq $item) {
    return $null
  }

  return [string]$item.Value
}

function Read-MythicEnvFile {
  param(
    [string]$Path
  )

  $vars = @{}
  if ([string]::IsNullOrWhiteSpace($Path)) {
    return $vars
  }

  $resolvedPath = (Resolve-Path $Path -ErrorAction Stop).Path
  foreach ($line in Get-Content $resolvedPath) {
    $trimmed = $line.Trim()
    if (-not $trimmed -or $trimmed.StartsWith("#")) {
      continue
    }

    if ($trimmed.StartsWith("export ")) {
      $trimmed = $trimmed.Substring(7).Trim()
    }

    $parts = $trimmed -split "=", 2
    if ($parts.Count -ne 2) {
      continue
    }

    $key = $parts[0].Trim()
    $value = $parts[1].Trim()

    if (
      ($value.StartsWith('"') -and $value.EndsWith('"')) -or
      ($value.StartsWith("'") -and $value.EndsWith("'"))
    ) {
      $value = $value.Substring(1, $value.Length - 2)
    }

    $vars[$key] = $value
  }

  return $vars
}

function Resolve-MythicHarnessEnv {
  param(
    [string]$EnvFile
  )

  $fileValues = Read-MythicEnvFile -Path $EnvFile
  $resolved = [ordered]@{}

  foreach ($key in $script:MythicHarnessEnvKeys) {
    if ($fileValues.Contains($key)) {
      $value = $fileValues[$key]
    } else {
      $value = Get-MythicEnvVarValue -Name $key
    }

    if (-not [string]::IsNullOrWhiteSpace($value)) {
      $resolved[$key] = $value
    }
  }

  return $resolved
}

function ConvertTo-TomlString {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Value
  )

  '"' + $Value.Replace('\', '\\').Replace('"', '\"') + '"'
}

function New-MythicCodexConfig {
  param(
    [hashtable]$ResolvedEnv
  )

  $mcpEnv = [ordered]@{
    "UV_PROJECT_ENVIRONMENT" = "/codex-home/.venvs/mythicmcp"
    "UV_CACHE_DIR" = "/codex-home/.cache/uv"
  }

  foreach ($key in $ResolvedEnv.Keys) {
    $mcpEnv[$key] = [string]$ResolvedEnv[$key]
  }

  $lines = @(
    'model = "gpt-5.4-cyber"',
    '',
    '[projects."/workspace"]',
    'trust_level = "trusted"',
    '',
    '[mcp_servers.mythicmcp-dev]',
    'command = "bash"',
    'args = ["-lc", "export UV_PROJECT_ENVIRONMENT=/codex-home/.venvs/mythicmcp && export UV_CACHE_DIR=/codex-home/.cache/uv && exec uv run --directory /workspace mythicmcp"]',
    'startup_timeout_sec = 60',
    'enabled = true'
  )

  $lines += ''
  $lines += '[mcp_servers.mythicmcp-dev.env]'
  foreach ($key in $mcpEnv.Keys) {
    $lines += "$key = $(ConvertTo-TomlString -Value ([string]$mcpEnv[$key]))"
  }

  return ($lines -join [Environment]::NewLine) + [Environment]::NewLine
}

function Initialize-MythicCodexHome {
  param(
    [Parameter(Mandatory = $true)]
    [string]$PersistedCodexHome,
    [hashtable]$ResolvedEnv,
    [switch]$FreshHome
  )

  if ($FreshHome -and (Test-Path $PersistedCodexHome)) {
    Get-ChildItem -Force $PersistedCodexHome -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force
  }

  New-Item -ItemType Directory -Force $PersistedCodexHome | Out-Null

  $hostCodexHome = Join-Path $env:USERPROFILE ".codex"
  foreach ($seedFile in @("auth.json", "cap_sid")) {
    $source = Join-Path $hostCodexHome $seedFile
    $destination = Join-Path $PersistedCodexHome $seedFile

    if ((Test-Path $source) -and -not (Test-Path $destination)) {
      Copy-Item $source $destination -Force
    }
  }

  $configPath = Join-Path $PersistedCodexHome "config.toml"
  Set-Content -Path $configPath -Value (New-MythicCodexConfig -ResolvedEnv $ResolvedEnv)
}

function Ensure-MythicCodexImage {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RepoRoot,
    [string]$CodexVersion = "0.116.0",
    [switch]$Rebuild
  )

  $imageName = Get-MythicCodexImageName
  & cmd /c "docker image inspect $imageName >nul 2>nul"
  $exists = $LASTEXITCODE -eq 0

  if ($Rebuild -or -not $exists) {
    Write-Host "Building Docker image '$imageName' with Codex CLI $CodexVersion"
    docker build `
      -f (Join-Path $RepoRoot "Dockerfile.codex-manual") `
      --build-arg "CODEX_VERSION=$CodexVersion" `
      -t $imageName `
      $RepoRoot

    if ($LASTEXITCODE -ne 0) {
      throw "Docker build failed for '$imageName'"
    }
  } else {
    Write-Host "Using existing Docker image '$imageName'"
  }

  return $imageName
}

function Get-MythicDockerEnvArgs {
  param(
    [hashtable]$ResolvedEnv
  )

  $args = @()
  foreach ($key in $ResolvedEnv.Keys) {
    $args += "-e"
    $args += "$key=$($ResolvedEnv[$key])"
  }

  return $args
}

function Get-MythicUvDockerEnvArgs {
  $args = @()
  foreach ($key in $script:MythicUvDockerEnv.Keys) {
    $args += "-e"
    $args += "$key=$($script:MythicUvDockerEnv[$key])"
  }

  return $args
}
