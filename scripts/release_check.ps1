param(
    [string]$Tag
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

if ([string]::IsNullOrWhiteSpace($env:UV_CACHE_DIR)) {
    $env:UV_CACHE_DIR = Join-Path $repoRoot ".local\uv-cache"
}

function Step($Message) {
    Write-Host "==> $Message"
}

function Invoke-Native($Command, [string[]]$Arguments) {
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
}

function Invoke-NativeOutput($Command, [string[]]$Arguments) {
    $output = & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $Command $($Arguments -join ' ')"
    }
    return $output
}

Step "Reading project version"
$version = Invoke-NativeOutput "python" @("-c", "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")
$expectedTag = "v$version"

if ([string]::IsNullOrWhiteSpace($Tag)) {
    $Tag = $expectedTag
}

if ($Tag -ne $expectedTag) {
    throw "Tag '$Tag' does not match pyproject.toml version '$version' (expected '$expectedTag')."
}

Step "Checking working tree"
$status = Invoke-NativeOutput "git" @("status", "--porcelain")
if (-not [string]::IsNullOrWhiteSpace($status)) {
    Write-Host $status
    throw "Working tree is not clean. Commit or stash changes before tagging a release."
}

Step "Checking current commit is on master"
Invoke-Native "git" @("fetch", "origin", "master:refs/remotes/origin/master", "--depth=1")
Invoke-Native "git" @("merge-base", "--is-ancestor", "HEAD", "origin/master")

Step "Checking tag does not already exist"
$existingLocalTag = Invoke-NativeOutput "git" @("tag", "--list", $Tag)
if (-not [string]::IsNullOrWhiteSpace($existingLocalTag)) {
    throw "Local tag '$Tag' already exists."
}

$existingRemoteTag = Invoke-NativeOutput "git" @("ls-remote", "--tags", "origin", "refs/tags/$Tag")
if (-not [string]::IsNullOrWhiteSpace($existingRemoteTag)) {
    throw "Remote tag '$Tag' already exists on origin."
}

Step "Syncing dependencies from lockfile"
Invoke-Native "uv" @("sync", "--locked", "--python", "3.11")

Step "Clearing test-only environment overrides"
Remove-Item Env:MYTHIC_HOTLOAD -ErrorAction SilentlyContinue
Remove-Item Env:MYTHIC_AGENTS -ErrorAction SilentlyContinue
Remove-Item Env:MYTHIC_DEV -ErrorAction SilentlyContinue

Step "Running unit tests"
Invoke-Native "uv" @("run", "python", "-m", "pytest", "tests/unit", "-q")

Step "Building package"
Invoke-Native "uv" @("build", "--python", "3.11")

Step "Release preflight passed for $Tag"
Write-Host "Next:"
Write-Host "  git tag -a $Tag -m `"$Tag`""
Write-Host "  git push origin $Tag"
