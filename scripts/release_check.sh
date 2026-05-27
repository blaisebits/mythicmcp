#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-}"
SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="$(cd -- "${SCRIPT_PATH%/*}" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_ROOT}"

export UV_CACHE_DIR="${UV_CACHE_DIR:-${REPO_ROOT}/.local/uv-cache}"

step() {
    printf '==> %s\n' "$1"
}

step "Reading project version"
VERSION="$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")"
EXPECTED_TAG="v${VERSION}"

if [[ -z "${TAG}" ]]; then
    TAG="${EXPECTED_TAG}"
fi

if [[ "${TAG}" != "${EXPECTED_TAG}" ]]; then
    printf "Tag '%s' does not match pyproject.toml version '%s' (expected '%s').\n" "${TAG}" "${VERSION}" "${EXPECTED_TAG}" >&2
    exit 1
fi

step "Checking working tree"
if [[ -n "$(git status --porcelain)" ]]; then
    git status --porcelain
    printf 'Working tree is not clean. Commit or stash changes before tagging a release.\n' >&2
    exit 1
fi

step "Checking current commit is on master"
git fetch origin master:refs/remotes/origin/master --depth=1
git merge-base --is-ancestor HEAD origin/master

step "Checking tag does not already exist"
if [[ -n "$(git tag --list "${TAG}")" ]]; then
    printf "Local tag '%s' already exists.\n" "${TAG}" >&2
    exit 1
fi

REMOTE_TAG="$(git ls-remote --tags origin "refs/tags/${TAG}")"
if [[ -n "${REMOTE_TAG}" ]]; then
    printf "Remote tag '%s' already exists on origin.\n" "${TAG}" >&2
    exit 1
fi

step "Syncing dependencies from lockfile"
uv sync --locked --python 3.11

step "Clearing test-only environment overrides"
unset MYTHIC_HOTLOAD
unset MYTHIC_AGENTS
unset MYTHIC_DEV

step "Running unit tests"
uv run python -m pytest tests/unit -q

step "Building package"
uv build --python 3.11

step "Release preflight passed for ${TAG}"
printf 'Next:\n'
printf '  git tag -a %s -m "%s"\n' "${TAG}" "${TAG}"
printf '  git push origin %s\n' "${TAG}"
