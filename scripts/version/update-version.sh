#!/usr/bin/env bash
# update-version.sh — Bump the project version in .version
#
# Format: vMajor.Minor.Patch.build
#   build = epoch timestamp (seconds since 1970)
#
# Usage:
#   ./scripts/version/update-version.sh            # Refresh build timestamp only
#   ./scripts/version/update-version.sh patch       # Increment patch + refresh build
#   ./scripts/version/update-version.sh minor       # Increment minor, reset patch + refresh build
#   ./scripts/version/update-version.sh major       # Increment major, reset minor/patch + refresh build

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
VERSION_FILE="$ROOT_DIR/.version"

if [[ ! -f "$VERSION_FILE" ]]; then
    echo "Error: $VERSION_FILE not found" >&2
    exit 1
fi

CURRENT="$(head -1 "$VERSION_FILE" | tr -d '[:space:]')"

# Parse current version — strip leading 'v', split on '.'
VERSION_BODY="${CURRENT#v}"
IFS='.' read -r MAJOR MINOR PATCH _BUILD <<< "$VERSION_BODY"

# Default any missing component to 0
MAJOR="${MAJOR:-0}"
MINOR="${MINOR:-0}"
PATCH="${PATCH:-0}"

BUMP_TYPE="${1:-build}"
BUILD="$(date +%s)"

case "$BUMP_TYPE" in
    major)
        MAJOR=$((MAJOR + 1))
        MINOR=0
        PATCH=0
        ;;
    minor)
        MINOR=$((MINOR + 1))
        PATCH=0
        ;;
    patch)
        PATCH=$((PATCH + 1))
        ;;
    build|"")
        # Only refresh the build timestamp
        ;;
    *)
        echo "Usage: $0 [major|minor|patch|build]" >&2
        exit 1
        ;;
esac

NEW_VERSION="v${MAJOR}.${MINOR}.${PATCH}.${BUILD}"

echo "$NEW_VERSION" > "$VERSION_FILE"
echo "$NEW_VERSION"
