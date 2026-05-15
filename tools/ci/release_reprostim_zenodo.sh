#!/usr/bin/env bash
# Update .zenodo.json version and publication_date before a release.
#
# Reads the VERSION environment variable (set by intuit/auto during release)
# and today's date, then replaces the corresponding fields in .zenodo.json.
#
# Usage (local test):
#   VERSION=0.7.32 bash tools/ci/release_reprostim_zenodo
#
# Usage (in .autorc exec beforeRelease):
#   tools/ci/release_reprostim_zenodo && git add .zenodo.json

set -eu

ZENODO_FILE=".zenodo.json"

if [ -z "${VERSION:-}" ]; then
    echo "ERROR: VERSION environment variable is not set." >&2
    exit 1
fi

DATE=$(date +%Y-%m-%d)

# sed -i behaves differently on macOS vs Linux
if [[ "$(uname)" == "Darwin" ]]; then
    sed -i '' "s/\"version\": \".*\"/\"version\": \"${VERSION}\"/" "$ZENODO_FILE"
    sed -i '' "s/\"publication_date\": \".*\"/\"publication_date\": \"${DATE}\"/" "$ZENODO_FILE"
else
    sed -i "s/\"version\": \".*\"/\"version\": \"${VERSION}\"/" "$ZENODO_FILE"
    sed -i "s/\"publication_date\": \".*\"/\"publication_date\": \"${DATE}\"/" "$ZENODO_FILE"
fi

echo "Updated ${ZENODO_FILE}: version=${VERSION}, publication_date=${DATE}"
